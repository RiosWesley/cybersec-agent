# -*- coding: utf-8 -*-
"""ai_studio_code (1).py

Original file is located at
    https://colab.research.google.com/drive/1OVA7QaQI3ry20M3pP9ZWhKLfMuUk0b-W

# 🛡️ Projeto CyberSentinel: Fine-Tuning do Analista SOC Virtual

**Objetivo da Atividade:** Realizar o ajuste fino (fine-tuning) de um LLM especialista em cibersegurança utilizando dados reais do HuggingFace. O modelo final será capaz de classificar ameaças, mapear logs para técnicas **MITRE ATT&CK**, avaliar impactos na tríade CIA (Confidencialidade, Integridade, Disponibilidade) e sugerir ações imediatas de resposta a incidentes.

**Abordagem Metodológica:**
- **Modelo Base:** `unsloth/Qwen3.5-2B-Instruct`
- **Otimização:** QLoRA (Rank = 16, Alpha = 16) para redução drástica de uso de memória de GPU.
- **Dataset:** `sambanovasystems/attackqa` (dados de Q&A reais sobre MITRE ATT&CK).
- **Split de Dados:** 70% Treino e 30% Validação.
- **Portabilidade:** Fusão de adaptadores e exportação direta para **GGUF em 4 bits (q4_k_m)** para execução local em CPU.
"""

# ==========================================
# 1. Instalação de Dependências
# ==========================================
# Para rodar no Google Colab, descomente as linhas abaixo:
# !pip install --upgrade -qqq uv
# !uv pip install -qqq "torch==2.8.0" "triton>=3.3.0" torchvision bitsandbytes xformers==0.0.32.post2
# !uv pip install -qqq "unsloth_zoo[base] @ git+https://github.com/unslothai/unsloth-zoo" "unsloth[base] @ git+https://github.com/unslothai/unsloth"
# !uv pip install -qqq --no-deps "torchcodec==0.7.0"
# !uv pip install --upgrade --no-deps "tokenizers>=0.22.0,<=0.23.0" trl==0.22.2
# !uv pip install transformers==5.2.0 flash-linear-attention causal_conv1d==1.6.0
# !uv pip install --no-deps --upgrade "torchao>=0.16.0"

# ==========================================
# 2. Inicialização do Modelo e Tokenizador
# ==========================================
from unsloth import FastLanguageModel
import torch

max_seq_length = 4096  # Suporte a janelas de contexto longas para logs e relatórios
dtype = None           # Detecção automática de tipo com base na GPU
load_in_4bit = True    # Ativa carregamento em 4 bits para viabilizar o treino em hardware modesto

model_id = "unsloth/Qwen3.5-2B-Instruct"

print(f"Carregando o modelo base {model_id}...")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_id = model_id,
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,
)

# ==========================================
# 3. Parametrização PEFT (QLoRA)
# ==========================================
print("Configurando adaptadores LoRA (PEFT)...")
model = FastLanguageModel.get_peft_model(
    model,
    r = 16,                # Rank do LoRA (ajuste fino de rank médio)
    target_modules = [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ],
    lora_alpha = 16,       # Fator de escala
    lora_dropout = 0,      # Desativado para fins de eficiência com Unsloth
    bias = "none",
    random_state = 42,
    use_rslora = False,
    loftq_config = None,
)

# ==========================================
# 4. Carregamento e Divisão do Dataset (70/30)
# ==========================================
from datasets import load_dataset

print("Carregando o dataset de segurança real do HuggingFace...")
dataset = load_dataset("sambanovasystems/attackqa", split="train")

# Definição do prompt sistemático que molda o comportamento do CyberSentinel
prompt_sistema = """Você é o CyberSentinel, um agente inteligente e analista SOC (Security Operations Center) sênior especialista em resposta a incidentes cibernéticos.
Você analisa logs, descrições de falhas, vulnerabilidades e alertas e fornece análises estruturadas detalhadas.
Ao receber um log ou incidente, estruture sua resposta RIGOROSAMENTE com as seguintes seções em Markdown:
1. ## 🔴 Classificação da Ameaça: Identifique o tipo de ataque e defina a severidade (CRITICAL, HIGH, MEDIUM, LOW ou INFO).
2. ## 🎯 Mapeamento MITRE ATT&CK: Indique a Tática e Técnica correspondente ao comportamento observado.
3. ## 🛡️ Análise de Impacto (CIA): Descreva brevemente o impacto à Confidencialidade, Integridade e Disponibilidade dos dados.
4. ## 📋 Plano de Resposta e Mitigação: Indique os passos práticos de contenção, erradicação e recuperação que o analista de infraestrutura deve executar."""

def preparar_dataset_conversacional(amostra):
    # Formata a entrada para o template de chat com ChatML/ShareGPT
    pergunta = amostra["question"]
    resposta = amostra["response"]
    
    dialogo = [
        {"role": "system", "content": prompt_sistema},
        {"role": "user", "content": f"Analise a seguinte questão de segurança ou alerta:\n\n{pergunta}"},
        {"role": "assistant", "content": resposta}
    ]
    return {"messages": dialogo}

# Realizando a divisão 70/30 no dataset real
print("Dividindo o dataset em 70% Treino e 30% Validação...")
dataset_split = dataset.train_test_split(test_size=0.3, seed=42)

# Limitando o tamanho máximo para otimizar o tempo de treino no Colab gratuito (T4)
limite_treino = min(2100, len(dataset_split["train"]))
limite_val = min(900, len(dataset_split["test"]))

train_raw = dataset_split["train"].select(range(limite_treino))
val_raw = dataset_split["test"].select(range(limite_val))

print(f"Estruturando dados de Treinamento ({len(train_raw)} registros)...")
dataset_treino = [preparar_dataset_conversacional(a) for a in train_raw]

print(f"Estruturando dados de Validação ({len(val_raw)} registros)...")
dataset_validacao = [preparar_dataset_conversacional(a) for a in val_raw]

# ==========================================
# 5. Loop de Treinamento e Otimização
# ==========================================
from trl import SFTTrainer, SFTConfig

# Prepara modelo de linguagem para modo de treino
FastLanguageModel.for_training(model)

config_treino = SFTConfig(
    per_device_train_batch_size = 2,
    gradient_accumulation_steps = 4,
    warmup_steps = 10,
    max_steps = 120,           # Suficiente para alinhar no Colab em ~10 minutos
    learning_rate = 2e-4,
    logging_steps = 10,
    eval_strategy = "steps",   # Habilita avaliação contínua no processo
    eval_steps = 20,           # Calcula eval_loss a cada 20 passos
    optim = "adamw_8bit",      # Otimizador de 8 bits para VRAM reduzida
    weight_decay = 0.01,
    lr_scheduler_type = "linear",
    seed = 42,
    output_dir = "cybersentinel_checkpoints",
    report_to = "none",
    remove_unused_columns = False,
    dataset_text_field = "",
    dataset_kwargs = {"skip_prepare_dataset": True},
    max_seq_length = max_seq_length,
)

print("Iniciando o treinamento do CyberSentinel com QLoRA...")
trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset_treino,
    eval_dataset = dataset_validacao, # Passagem do conjunto de avaliação
    args = config_treino,
)

metricas_treino = trainer.train()
print("Treinamento finalizado com sucesso!")

# ==========================================
# 6. Validação do Agente (Inferência)
# ==========================================
# Muda o modelo para modo de inferência (otimiza caches internos)
FastLanguageModel.for_inference(model)

teste_log = "Detectadas 450 tentativas falhas de login SSH para o usuário 'root' em menos de 3 minutos vindo do IP 192.168.1.150."

mensagens = [
    {"role": "system", "content": prompt_sistema},
    {"role": "user", "content": f"Analise a seguinte questão de segurança ou alerta:\n\n{teste_log}"}
]

inputs = tokenizer.apply_chat_template(
    mensagens,
    add_generation_prompt = True,
    return_tensors = "pt"
).to("cuda")

print("Gerando resposta do CyberSentinel...")
saidas = model.generate(
    input_ids = inputs,
    max_new_tokens = 512,
    use_cache = True,
    temperature = 0.3,
    top_p = 0.9
)

resultado = tokenizer.decode(saidas[0][len(inputs[0]):], skip_special_tokens=True)
print("\nResposta:\n")
print(resultado)

# ==========================================
# 7. Exportação direta para GGUF (4 bits)
# ==========================================
print("Fundindo adaptadores e exportando modelo para GGUF...")
model.save_pretrained_gguf(
    "cybersentinel_gguf", 
    tokenizer, 
    quantization_method = "q4_k_m"
)
print("Exportação concluída! Baixe o arquivo '.gguf' gerado na pasta 'cybersentinel_gguf' e coloque-o na pasta 'backend/models' do local renomando para 'model.gguf'.")