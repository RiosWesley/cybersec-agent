import os
import sys
import shutil
from huggingface_hub import hf_hub_download

def download_cybersec_model():
    model_dir = os.path.join(os.path.dirname(__file__), "models")
    os.makedirs(model_dir, exist_ok=True)
    
    nativo_path = os.path.join(model_dir, "qwen_nativo.gguf")
    finetuned_path = os.path.join(model_dir, "qwen_finetuned.gguf")
    legacy_path = os.path.join(model_dir, "model.gguf")
    
    # 1. Trata migração do arquivo legado
    if os.path.exists(legacy_path):
        print(f"[CyberSentinel Setup] Detectado modelo legado em: {legacy_path}")
        if not os.path.exists(finetuned_path):
            print(f"[CyberSentinel Setup] Copiando modelo legado para o caminho do fine-tuned: {finetuned_path}")
            try:
                shutil.copy(legacy_path, finetuned_path)
            except Exception as e:
                print(f"[Aviso] Não foi possível copiar: {e}")
            
    # 2. Baixa o modelo nativo se não existir
    if not os.path.exists(nativo_path):
        print("[CyberSentinel Setup] Baixando o modelo padrão Qwen3.5-2B GGUF (Nativo) do HuggingFace...")
        print("[CyberSentinel Setup] Este download de aproximadamente 1.3GB é feito apenas uma vez.")
        try:
            downloaded_file = hf_hub_download(
                repo_id="unsloth/Qwen3.5-2B-GGUF",
                filename="Qwen3.5-2B-Q4_K_M.gguf",
                local_dir=model_dir,
                local_dir_use_symlinks=False
            )
            # HF Hub download salva em subpastas se local_dir_use_symlinks for False dependendo da versão
            # Vamos garantir que ele vai parar no lugar certo
            if os.path.exists(downloaded_file) and downloaded_file != nativo_path:
                if os.path.exists(nativo_path):
                    os.remove(nativo_path)
                shutil.move(downloaded_file, nativo_path)
            print(f"[CyberSentinel Setup] Modelo nativo configurado com sucesso em: {nativo_path}")
        except Exception as e:
            print(f"\n[ERRO] Falha ao baixar o modelo nativo: {e}", file=sys.stderr)
            print("[AVISO] Certifique-se de ter conexão com a internet.", file=sys.stderr)
            
    # 3. Se ainda não houver o modelo fine-tuned, usa o nativo como cópia temporária de demonstração
    if not os.path.exists(finetuned_path):
        if os.path.exists(nativo_path):
            print("[CyberSentinel Setup] Nenhuma versão fine-tuned encontrada em qwen_finetuned.gguf.")
            print("[CyberSentinel Setup] Criando cópia temporária do modelo nativo para demonstração lado a lado...")
            try:
                shutil.copy(nativo_path, finetuned_path)
                print(f"[CyberSentinel Setup] Cópia criada com sucesso em: {finetuned_path}")
            except Exception as e:
                print(f"[ERRO] Falha ao criar cópia: {e}")

if __name__ == "__main__":
    download_cybersec_model()
