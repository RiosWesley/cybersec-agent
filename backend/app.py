import os
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from llama_cpp import Llama

app = FastAPI(
    title="CyberSentinel API",
    description="Backend de inferência local para o Agente SOC Especialista em Cibersegurança",
    version="1.0.0"
)

# Configurando CORS para permitir conexões do Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Desativar cache para evitar que o navegador use código Javascript/CSS antigo
@app.middleware("http")
async def add_no_cache_header(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Caminhos dos modelos
NATIVO_MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "qwen_nativo.gguf")
FINETUNED_MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "qwen_finetuned.gguf")
LEGACY_MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "model.gguf")

# Dicionário de instâncias dos modelos carregados na RAM (Carregamento lazy/sob demanda)
llms = {
    "nativo": None,
    "finetuned": None
}

# Prompt de Sistema do CyberSentinel (Otimizado para manter o raciocínio em português)
SYSTEM_PROMPT = """Você é o CyberSentinel, um agente inteligente e analista SOC (Security Operations Center) sênior especialista em resposta a incidentes cibernéticos.
Você analisa logs, descrições de falhas, vulnerabilidades e alertas e fornece análises estruturadas detalhadas.

Importante:
1. O seu processo de raciocínio interno (Thinking Process) deve ser breve (máximo de 3 a 5 linhas) e escrito ESTRITAMENTE em português do Brasil.
2. Ao receber um log ou incidente, estruture sua resposta final RIGOROSAMENTE com as seguintes seções em Markdown:
## 🔴 Classificação da Ameaça: Identifique o tipo de ataque e defina a severidade (CRITICAL, HIGH, MEDIUM, LOW ou INFO).
## 🎯 Mapeamento MITRE ATT&CK: Indique a Tática e Técnica correspondente ao comportamento observado.
## 🛡️ Análise de Impacto (CIA): Descreva brevemente o impacto à Confidencialidade, Integridade e Disponibilidade dos dados.
## 📋 Plano de Resposta e Mitigação: Indique os passos práticos de contenção, erradicação e recuperação que o analista de infraestrutura deve executar.
3. Todo o relatório final deve ser escrito em português do Brasil."""

def init_llm(model_name: str):
    global llms
    if llms[model_name] is not None:
        return
        
    path = NATIVO_MODEL_PATH if model_name == "nativo" else FINETUNED_MODEL_PATH
    
    # Fallback para o modelo legado caso qwen_finetuned não exista
    if model_name == "finetuned" and not os.path.exists(path) and os.path.exists(LEGACY_MODEL_PATH):
        path = LEGACY_MODEL_PATH
        
    # Fallback caso o modelo selecionado não esteja no disco mas o outro esteja
    if not os.path.exists(path):
        alternative = FINETUNED_MODEL_PATH if model_name == "nativo" else NATIVO_MODEL_PATH
        if os.path.exists(alternative):
            path = alternative
        else:
            print(f"[ERROR] Modelo {model_name} não encontrado em {path} e sem fallback disponível.")
            return

    print(f"Carregando o modelo {model_name} a partir de: {path}...")
    start_time = time.time()
    try:
        # Configurado de forma otimizada para execução em CPU (n_ctx=2048, n_threads=4)
        llms[model_name] = Llama(
            model_path=path,
            n_ctx=2048,
            n_threads=4,
            n_batch=512,
            verbose=False
        )
        print(f"Modelo {model_name} carregado com sucesso em {time.time() - start_time:.2f}s!")
    except Exception as e:
        print(f"[ERROR] Erro crítico ao carregar o modelo {model_name}: {e}")

@app.on_event("startup")
def startup_event():
    # Inicializa por padrão o modelo fine-tuned no startup do servidor para velocidade inicial
    # O nativo será carregado quando o usuário alternar para o modo comparativo e rodar
    init_llm("finetuned")

class LogAnalysisRequest(BaseModel):
    log: str
    context: str = ""

class LogAnalysisResponse(BaseModel):
    raw_response: str
    processing_time_sec: float

@app.get("/health")
def health_check():
    nativo_exists = os.path.exists(NATIVO_MODEL_PATH)
    finetuned_exists = os.path.exists(FINETUNED_MODEL_PATH) or os.path.exists(LEGACY_MODEL_PATH)
    return {
        "status": "healthy" if (nativo_exists or finetuned_exists) else "degraded",
        "model_loaded_nativo": llms["nativo"] is not None,
        "model_loaded_finetuned": llms["finetuned"] is not None,
        "model_exists_nativo": nativo_exists,
        "model_exists_finetuned": finetuned_exists
    }

@app.post("/analyze")
def analyze_log(request: LogAnalysisRequest, model: str = "finetuned"):
    global llms
    if model not in ["nativo", "finetuned"]:
        raise HTTPException(status_code=400, detail="Modelo inválido. Escolha 'nativo' ou 'finetuned'.")
        
    if llms[model] is None:
        init_llm(model)
        if llms[model] is None:
            raise HTTPException(
                status_code=503, 
                detail=f"O modelo de linguagem '{model}' não pôde ser carregado. Certifique-se de que o arquivo GGUF correspondente está em backend/models/."
            )
            
    # Prepara a entrada seguindo a estrutura ChatML recomendada para o Qwen/Llama
    prompt = f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
    if request.context:
        prompt += f"<|im_start|>user\nContexto Organizacional: {request.context}\n\nLog/Alerta a ser analisado:\n{request.log}<|im_end|>\n"
    else:
        prompt += f"<|im_start|>user\nLog/Alerta a ser analisado:\n{request.log}<|im_end|>\n"
    
    # Pré-preenchimento do assistente para iniciar o raciocínio em português
    prefill = "<think>\nProcesso de Raciocínio:\n1. Análise do log: "
    prompt += f"<|im_start|>assistant\n{prefill}"
    
    def event_generator():
        # Rendemos o prefill primeiro para que o frontend receba as tags
        yield prefill
        try:
            chunks = llms[model](
                prompt,
                max_tokens=1024,
                temperature=0.2,
                top_p=0.9,
                stop=["<|im_end|>", "<|im_start|>"],
                echo=False,
                stream=True
            )
            for chunk in chunks:
                text = chunk['choices'][0]['text']
                yield text
        except Exception as e:
            yield f"\n[Erro no motor de inferência: {str(e)}]"
            
    return StreamingResponse(event_generator(), media_type="text/plain; charset=utf-8")

# Monta o Frontend para ser servido a partir da raiz da mesma porta do Backend
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
