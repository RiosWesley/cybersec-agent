import os
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

# Caminho do modelo local
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "model.gguf")
llm = None

# Prompt de Sistema do CyberSentinel (Igual ao do Fine-tuning)
SYSTEM_PROMPT = """Você é o CyberSentinel, um agente inteligente e analista SOC (Security Operations Center) sênior especialista em resposta a incidentes cibernéticos.
Você analisa logs, descrições de falhas, vulnerabilidades e alertas e fornece análises estruturadas detalhadas.
Ao receber um log ou incidente, estruture sua resposta RIGOROSAMENTE com as seguintes seções em Markdown:
1. ## 🔴 Classificação da Ameaça: Identifique o tipo de ataque e defina a severidade (CRITICAL, HIGH, MEDIUM, LOW ou INFO).
2. ## 🎯 Mapeamento MITRE ATT&CK: Indique a Tática e Técnica correspondente ao comportamento observado.
3. ## 🛡️ Análise de Impacto (CIA): Descreva brevemente o impacto à Confidencialidade, Integridade e Disponibilidade dos dados.
4. ## 📋 Plano de Resposta e Mitigação: Indique os passos práticos de contenção, erradicação e recuperação que o analista de infraestrutura deve executar."""

def init_llm():
    global llm
    if llm is not None:
        return
        
    if not os.path.exists(MODEL_PATH):
        print(f"[ERROR] Modelo GGUF não encontrado em: {MODEL_PATH}")
        print("[INFO] Por favor, certifique-se de executar o download_model.py ou colocar seu próprio GGUF nesta pasta.")
        return

    print(f"Carregando o modelo GGUF a partir de: {MODEL_PATH}...")
    start_time = time.time()
    try:
        # Configurado de forma otimizada para execução em CPU (n_ctx=2048, n_threads=4)
        llm = Llama(
            model_path=MODEL_PATH,
            n_ctx=2048,
            n_threads=4,
            n_batch=512,
            verbose=False
        )
        print(f"Modelo carregado com sucesso em {time.time() - start_time:.2f}s!")
    except Exception as e:
        print(f"[ERROR] Erro crítico ao carregar o modelo GGUF: {e}")

@app.on_event("startup")
def startup_event():
    # Inicializa o modelo no startup do servidor
    init_llm()

class LogAnalysisRequest(BaseModel):
    log: str
    context: str = ""

class LogAnalysisResponse(BaseModel):
    raw_response: str
    processing_time_sec: float

@app.get("/health")
def health_check():
    model_loaded = llm is not None
    model_exists = os.path.exists(MODEL_PATH)
    return {
        "status": "healthy" if model_loaded else "degraded",
        "model_loaded": model_loaded,
        "model_file_exists": model_exists,
        "model_path": MODEL_PATH
    }

@app.post("/analyze", response_model=LogAnalysisResponse)
def analyze_log(request: LogAnalysisRequest):
    global llm
    if llm is None:
        # Tenta carregar o modelo novamente caso tenha falhado antes
        init_llm()
        if llm is None:
            raise HTTPException(
                status_code=503, 
                detail="O modelo de linguagem (GGUF) não pôde ser carregado. Certifique-se de baixar o modelo antes de enviar requisições."
            )
            
    start_time = time.time()
    
    # Prepara a entrada seguindo a estrutura ChatML recomendada para o Qwen/Llama
    prompt = f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
    if request.context:
        prompt += f"<|im_start|>user\nContexto Organizacional: {request.context}\n\nLog/Alerta a ser analisado:\n{request.log}<|im_end|>\n"
    else:
        prompt += f"<|im_start|>user\nLog/Alerta a ser analisado:\n{request.log}<|im_end|>\n"
    prompt += "<|im_start|>assistant\n"
    
    try:
        # Gera a resposta com temperatura baixa (0.2) para garantir respostas analíticas e precisas
        response = llm(
            prompt,
            max_tokens=1024,
            temperature=0.2,
            top_p=0.9,
            stop=["<|im_end|>", "<|im_start|>"],
            echo=False
        )
        
        raw_text = response['choices'][0]['text'].strip()
        processing_time = time.time() - start_time
        
        return LogAnalysisResponse(
            raw_response=raw_text,
            processing_time_sec=round(processing_time, 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno no motor de inferência: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
