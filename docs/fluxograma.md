# 📊 Fluxograma de Funcionamento — CyberSentinel

Este documento contém a representação em diagramas do ciclo de vida e processamento do agente inteligente CyberSentinel.

---

## 🔄 1. Fluxograma de Execução do Agente (Inferência Local)

O diagrama a seguir descreve a jornada de um log bruto de segurança desde sua entrada na interface até o processamento local pela LLM fine-tuned e a exibição das respostas estruturadas de mitigação no painel.

```mermaid
graph TD
    %% Nós
    Start([Inicio: Novo Incidente]) --> Input[Interface: Usuario insere Log + Contexto]
    Input --> Valid{API Ativa?}
    
    Valid -- Nao --> Error[Exibe Erro de Conexao]
    Valid -- Sim --> Payload[FastAPI recebe POST em /analyze]
    
    Payload --> ModelCheck{Modelo GGUF carregado?}
    ModelCheck -- Nao --> ModelLoad[Carrega model.gguf em CPU via llama-cpp-python]
    ModelLoad --> PromptBuild
    ModelCheck -- Sim --> PromptBuild[Montagem do Prompt com SYSTEM_PROMPT do SOC Analyst]
    
    PromptBuild --> Inference[Inferencia local em 4-bits no modelo Qwen3.5-2B-Instruct]
    Inference --> TextGen[Geracao do Parecer Tecnico Estruturado]
    
    TextGen --> Response[FastAPI responde com JSON contendo relatorio + latencia]
    Response --> UI[Frontend recebe resposta]
    
    UI --> Parse[marked.js converte Markdown do parecer para HTML]
    UI --> Severity[JavaScript extrai Severidade do texto]
    
    Parse --> Display[Renderiza parecer detalhado na tela]
    Severity --> Chart[Atualiza grafico doughnut de estatisticas do SOC]
    
    Display --> End([Fim: Parecer entregue ao Analista])
    Chart --> End
    
    %% Estilos de Cor
    style Start fill:#060913,stroke:#00f0ff,stroke-width:2px,color:#fff
    style End fill:#060913,stroke:#00f0ff,stroke-width:2px,color:#fff
    style Valid fill:#0c1020,stroke:#ff9000,stroke-width:1px,color:#fff
    style ModelCheck fill:#0c1020,stroke:#ff9000,stroke-width:1px,color:#fff
    style Inference fill:#00f0ff,stroke:#00a8ff,stroke-width:2px,color:#000
    style UI fill:#39ff14,stroke:#39ff14,stroke-width:1px,color:#000
```

---

## 🧠 2. Diagrama do Fluxo de Fine-Tuning (Treinamento)

Este diagrama detalha como o modelo especialista é gerado a partir do dataset real antes de ser exportado para o ambiente local Docker.

```mermaid
flowchart TD
    %% Nos
    BaseModel[Modelo Base de Texto<br/>Qwen3.5-2B-Instruct] --> LoadModel[Carregamento com Unsloth em 4-bits]
    
    Dataset[Dataset Real HuggingFace<br/>sambanovasystems/attackqa] --> Preprocess[Preprocessamento: Conversao para formato conversacional ChatML]
    Preprocess --> FormatData[Filtro de subset: 3000 exemplos de logs e mitigacao]
    
    LoadModel --> PEFT[Insercao de adaptadores LoRA<br/>r=16, alpha=16 nas camadas de projecao]
    
    PEFT --> Train[Loop de Treinamento supervisionado SFTTrainer]
    FormatData --> Train
    
    Train --> Checkpoints[Pesos LoRA aprendidos com ciberseguranca]
    
    Checkpoints --> Merge[Fusao automatica dos adaptadores LoRA ao Modelo Base]
    Merge --> GGUF[Quantizacao final 4-bits e exportacao para GGUF]
    
    GGUF --> DockerFolder[Modelo copiado para pasta backend/models/model.gguf]
    
    %% Estilos de Cor
    style BaseModel fill:#0c1020,stroke:#fff,color:#fff
    style Dataset fill:#0c1020,stroke:#fff,color:#fff
    style Train fill:#ff9000,stroke:#ff9000,color:#fff
    style GGUF fill:#39ff14,stroke:#39ff14,color:#000
```
