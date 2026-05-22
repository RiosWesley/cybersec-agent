# 📊 Fluxograma de Funcionamento — CyberSentinel

Este documento contém a representação em diagramas (sintaxe Mermaid.js) do ciclo de vida, fluxo de processamento concorrente e arquitetura de dados do agente inteligente **CyberSentinel**.

---

## 🔄 1. Fluxograma de Execução do Agente (Inferência Local com Lock)

O diagrama a seguir descreve a jornada de um log bruto de segurança desde a submissão no Frontend até o processamento síncrono no backend FastAPI (através do mecanismo de bloqueio de concorrência) e a renderização do stream final.

```mermaid
graph TD
    %% Nós
    Start([Início: Novo Incidente]) --> Input[Interface: Usuário insere Log + Contexto]
    Input --> Valid{API Ativa?}
    
    Valid -- Não --> Error[Exibe Erro de Conexão no Dashboard]
    Valid -- Sim --> Payload[FastAPI recebe POST em /analyze]
    
    Payload --> ModelCheck{Modelo GGUF inicializado?}
    ModelCheck -- Não --> ModelLoad[Carrega qwen_nativo.gguf em RAM via Llama class]
    ModelLoad --> LockAcquire
    ModelCheck -- Sim --> LockAcquire[Aquisição da trava global: llm_lock]
    
    LockAcquire -->|Aguardando na Fila| Wait[Bloqueia até liberação]
    LockAcquire -->|Livre| Exec[Invocação do Llama-cpp-python com Prompt e Parâmetros]
    
    Exec --> StreamLoop{Loop de Geração de Tokens}
    StreamLoop -->|Gera Token| StreamSend[Yield chunk de texto]
    StreamSend --> StreamLoop
    
    StreamLoop -->|Concluído / Fim| LockRelease[Liberação automática da trava llm_lock]
    LockRelease --> End([Fim da Requisição])
    
    %% Estilos de Cor
    style Start fill:#060913,stroke:#00f0ff,stroke-width:2px,color:#fff
    style End fill:#060913,stroke:#00f0ff,stroke-width:2px,color:#fff
    style Valid fill:#0c1020,stroke:#ff9000,stroke-width:1px,color:#fff
    style ModelCheck fill:#0c1020,stroke:#ff9000,stroke-width:1px,color:#fff
    style LockAcquire fill:#ff2e5b,stroke:#ff2e5b,stroke-width:2px,color:#fff
    style Exec fill:#00f0ff,stroke:#00a8ff,stroke-width:2px,color:#000
```

---

## 🧠 2. Diagrama do Fluxo de Comparação (Engenharia de Prompt Concorrente)

Este diagrama detalha como a requisição de análise é direcionada e processada no modo comparativo para evidenciar o impacto da Engenharia de Prompt no modelo base. Como as duas requisições são disparadas em paralelo pelo frontend (`Promise.all`), a sincronização com `llm_lock` é crítica.

```mermaid
flowchart TD
    %% Nós
    LogInput[Log de Segurança Bruto + Contexto] --> ModeCheck{Modo Comparação?}
    
    ModeCheck -- Não --> Single[Executa Rota: com_prompt]
    ModeCheck -- Sim --> Parallel[Dispara Duas Requisições Paralelas via Promise.all]
    
    Parallel --> RouteSem[POST /analyze?model=sem_prompt]
    Parallel --> RouteCom[POST /analyze?model=com_prompt]
    Single --> RouteCom
    
    subgraph Servidor FastAPI [Sincronização por Trava]
        RouteSem --> LockSem{Obtém llm_lock?}
        RouteCom --> LockCom{Obtém llm_lock?}
        
        LockSem -- Sim (adquire) --> InferenceSem[Inferência local SEM Prompt de Sistema]
        LockSem -- Não (ocupado) --> WaitSem[Aguardando liberação do Lock]
        
        LockCom -- Sim (adquire) --> ContextBuild[Monta ChatML com SYSTEM_PROMPT + Prefill]
        ContextBuild --> InferenceCom[Inferência local COM Prompt de Sistema]
        LockCom -- Não (ocupado) --> WaitCom[Aguardando liberação do Lock]
        
        InferenceSem --> ReleaseSem[Libera llm_lock]
        InferenceCom --> ReleaseCom[Libera llm_lock]
    end
    
    ReleaseSem --> OutputSem[Stream: Português Genérico/Inglês, Sem Estrutura]
    ReleaseCom --> OutputCom[Stream: Raciocínio & Relatório SOC Estruturado em Markdown]
    
    OutputSem --> UICompare[Exibição Comparativa Lado a Lado no Dashboard]
    OutputCom --> UICompare
    
    %% Relações de espera
    WaitSem -.->|Quando liberado| LockSem
    WaitCom -.->|Quando liberado| LockCom
    
    %% Estilos de Cor
    style LogInput fill:#0c1020,stroke:#fff,color:#fff
    style ModeCheck fill:#ff9000,stroke:#ff9000,color:#fff
    style LockSem fill:#ff2e5b,stroke:#ff2e5b,color:#fff
    style LockCom fill:#ff2e5b,stroke:#ff2e5b,color:#fff
    style InferenceSem fill:#0c1020,stroke:#ff8888,color:#fff
    style InferenceCom fill:#0c1020,stroke:#39ff14,color:#fff
    style UICompare fill:#00f3ff,stroke:#00f3ff,color:#000
```

---

## 📥 3. Entradas, Processamento e Saídas (PEAS)

O ciclo de vida de dados do agente segue o paradigma tradicional de processamento:

```
📥 ENTRADAS                        🧠 PROCESSAMENTO                      📤 SAÍDAS
- Log Bruto (Syslog, SSH, etc.)   - Formatação ChatML                   - Raciocínio (<think>)
- Contexto da TI                  - Sincronização por Thread-Lock       - Classificação de Risco
- Parâmetro Model (com/sem)       - Inferência GGUF CPU Otimizada       - MITRE ATT&CK, CIA & Mitigação
```
