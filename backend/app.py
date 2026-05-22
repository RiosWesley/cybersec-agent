import os
import time
import ctypes
import threading
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from llama_cpp import Llama, llama_cpp

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

# Instância única do modelo carregado na RAM (evita duplicação e OOM)
llm_instance = None
llm_error = None
llm_lock = threading.Lock()

# Buffer para capturar logs do llama.cpp e ajudar a detalhar falhas de inicialização
llama_log_buffer = []

def llama_log_callback(level, text, user_data):
    if text:
        try:
            msg = text.decode('utf-8', errors='replace')
            if len(llama_log_buffer) > 200:
                llama_log_buffer.pop(0)
            llama_log_buffer.append(msg)
        except Exception:
            pass

# Mantemos a referência do callback viva em escopo global para evitar Garbage Collection crash
_llama_log_callback_fn = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p, ctypes.c_void_p)(llama_log_callback)

try:
    llama_cpp.llama_log_set(_llama_log_callback_fn, None)
except Exception as e:
    print(f"[WARN] Não foi possível registrar o callback de logs do llama.cpp: {e}")

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

def init_llm():
    global llm_instance, llm_error, llama_log_buffer
    if llm_instance is not None:
        return
    with llm_lock:
        if llm_instance is not None:
            return
            
        path = NATIVO_MODEL_PATH
        if not os.path.exists(path):
            if os.path.exists(FINETUNED_MODEL_PATH):
                path = FINETUNED_MODEL_PATH
            elif os.path.exists(LEGACY_MODEL_PATH):
                path = LEGACY_MODEL_PATH
            else:
                err = f"Nenhum arquivo GGUF encontrado em {NATIVO_MODEL_PATH}."
                print(f"[ERROR] {err}")
                llm_error = err
                return

        print(f"Carregando o modelo a partir de: {path}...")
        start_time = time.time()
        
        # Limpa logs anteriores antes de iniciar carregamento
        llama_log_buffer.clear()
        
        try:
            # Configurado de forma otimizada para execução em CPU (n_ctx=2048, n_threads=4)
            llm_instance = Llama(
                model_path=path,
                n_ctx=2048,
                n_threads=4,
                n_batch=512,
                verbose=True  # Habilita logs para que nosso callback capture detalhes de erros internos
            )
            llm_error = None
            print(f"Modelo carregado com sucesso em {time.time() - start_time:.2f}s!")
            # Limpa o buffer de log após sucesso para liberar memória
            llama_log_buffer.clear()
        except Exception as e:
            # Extrai os últimos logs relevantes do llama.cpp
            recent_logs = [line.strip() for line in llama_log_buffer if line.strip()]
            last_logs_str = " | ".join(recent_logs[-8:])
            
            err_msg = f"Falha interna no motor de inferência llama-cpp-python ao carregar GGUF. Erro: {type(e).__name__}: {str(e)}"
            if last_logs_str:
                err_msg += f" (Detalhes do llama.cpp: {last_logs_str})"
                
            print(f"[ERROR] {err_msg}")
            llm_error = err_msg

@app.on_event("startup")
def startup_event():
    # Inicializa o modelo no startup
    init_llm()

class LogAnalysisRequest(BaseModel):
    log: str
    context: str = ""

class LogAnalysisResponse(BaseModel):
    raw_response: str
    processing_time_sec: float

@app.get("/health")
def health_check():
    model_exists = os.path.exists(NATIVO_MODEL_PATH) or os.path.exists(FINETUNED_MODEL_PATH) or os.path.exists(LEGACY_MODEL_PATH)
    return {
        "status": "healthy" if model_exists else "degraded",
        "model_loaded": llm_instance is not None,
        "model_file_exists": model_exists
    }

@app.get("/prompt")
def get_system_prompt():
    return {"system_prompt": SYSTEM_PROMPT}

@app.post("/analyze")
def analyze_log(request: LogAnalysisRequest, model: str = "com_prompt"):
    global llm_instance
    # Mapeamento para suportar nomes antigos e novos
    use_system = model in ["finetuned", "com_prompt"]
    
    if llm_instance is None:
        init_llm()
        if llm_instance is None:
            err_detail = llm_error or "Erro indeterminado de inicialização."
            raise HTTPException(
                status_code=503, 
                detail=f"O modelo de linguagem não pôde ser carregado. Detalhes técnicos: {err_detail}"
            )
            
    if use_system:
        # Prepara a entrada seguindo a estrutura ChatML recomendada para o Qwen/Llama com System Prompt
        prompt = f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
        if request.context:
            prompt += f"<|im_start|>user\nContexto Organizacional: {request.context}\n\nLog/Alerta a ser analisado:\n{request.log}<|im_end|>\n"
        else:
            prompt += f"<|im_start|>user\nLog/Alerta a ser analisado:\n{request.log}<|im_end|>\n"
        
        # Pré-preenchimento do assistente para iniciar o raciocínio em português
        prefill = "<think>\nProcesso de Raciocínio:\n1. Análise do log: "
        prompt += f"<|im_start|>assistant\n{prefill}"
    else:
        # Sem System Prompt: Envia diretamente a entrada do usuário ao modelo, sem diretrizes estruturadas
        if request.context:
            prompt = f"<|im_start|>user\nContexto Organizacional: {request.context}\n\nLog/Alerta a ser analisado:\n{request.log}<|im_end|>\n"
        else:
            prompt = f"<|im_start|>user\nLog/Alerta a ser analisado:\n{request.log}<|im_end|>\n"
        prompt += "<|im_start|>assistant\n"
        prefill = ""
    
    def event_generator():
        if prefill:
            yield prefill
        with llm_lock:
            try:
                chunks = llm_instance(
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
