import os
import sys
from huggingface_hub import hf_hub_download

def download_cybersec_model():
    model_dir = os.path.join(os.path.dirname(__file__), "models")
    os.makedirs(model_dir, exist_ok=True)
    
    # Arquivo de saída esperado
    model_path = os.path.join(model_dir, "model.gguf")
    
    if os.path.exists(model_path):
        print(f"[CyberSentinel Setup] O modelo já existe em: {model_path}")
        return
        
    print("[CyberSentinel Setup] Baixando o modelo padrão Qwen-2.5-3B-Instruct GGUF quantizado em 4 bits do HuggingFace...")
    print("[CyberSentinel Setup] Este download de aproximadamente 2GB é feito apenas uma vez.")
    
    try:
        # Baixa o modelo Qwen-2.5-3B-Instruct de 4 bits
        # Este modelo é super leve e roda de forma extremamente rápida em CPU.
        downloaded_file = hf_hub_download(
            repo_id="Qwen/Qwen2.5-3B-Instruct-GGUF",
            filename="qwen2.5-3b-instruct-q4_k_m.gguf",
            local_dir=model_dir,
            local_dir_use_symlinks=False
        )
        
        # Renomeia para 'model.gguf' para facilidade de carregamento
        downloaded_path = os.path.join(model_dir, "qwen2.5-3b-instruct-q4_k_m.gguf")
        if os.path.exists(downloaded_path):
            os.rename(downloaded_path, model_path)
            
        print(f"[CyberSentinel Setup] Modelo baixado e configurado com sucesso em: {model_path}")
    except Exception as e:
        print(f"\n[ERRO] Falha ao baixar o modelo: {e}", file=sys.stderr)
        print("[AVISO] Por favor, certifique-se de ter conexão com a internet e tente rodar novamente.", file=sys.stderr)
        print("[AVISO] Como alternativa, você pode colocar seu próprio arquivo GGUF gerado no Colab renomeado para 'model.gguf' diretamente na pasta: backend/models/", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    download_cybersec_model()
