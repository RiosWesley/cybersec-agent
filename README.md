# 🛡️ CyberSentinel — Analista SOC Virtual Especialista em Cibersegurança

Este projeto apresenta a proposta conceitual e a implementação funcional de um **Agente Inteligente Especialista** treinado para atuar no domínio de cibersegurança como um Analista SOC (Security Operations Center) Virtual.

O agente é capaz de receber logs de segurança de servidores, alertas de firewalls/IDS e relatórios de vulnerabilidades, processar esses dados sob a ótica de mitigação de incidentes, mapeá-los para técnicas reais da matriz **MITRE ATT&CK** e sugerir ações de contenção acionáveis para administradores de infraestrutura.

---

## 📋 Sumário
1. [Definição do Problema Real](#-definição-do-problema-real)
2. [Arquitetura PEAS do Agente Inteligente](#-arquitetura-peas-do-agente-inteligente)
3. [Entradas, Processamento e Saídas](#-entradas-processamento-e-saídas)
4. [Pipeline de Fine-Tuning (Treinamento do Especialista)](#-pipeline-de-fine-tuning-treinamento-do-especialista)
5. [Interface Customizada (Dashboard SOC)](#-interface-customizada-dashboard-soc)
6. [Instruções para Execução Local (Docker)](#-instruções-para-execução-local-docker)

---

## 🔍 Definição do Problema Real

O cenário moderno de ameaças digitais é crítico. Somente em 2024, o Brasil sofreu mais de **100 bilhões de tentativas de ataques cibernéticos**. Ao mesmo tempo, há um déficit global estimado de **3.5 milhões de profissionais de cibersegurança**. 

Pequenas e médias empresas (PMEs) enfrentam um grande dilema:
- Não possuem recursos financeiros para contratar analistas de segurança humanos (SOC) dedicados.
- Ferramentas tradicionais geram alertas de segurança complexos em arquivos de log brutos que gerentes de TI genéricos não sabem interpretar nem mitigar a tempo.

**O CyberSentinel resolve este problema:** Ele atua como um triador de incidentes de primeiro nível em cibersegurança de baixo custo, traduzindo logs incompreensíveis em relatórios estruturados de ameaças com planos de ação claros.

---

## 🏛️ Arquitetura PEAS do Agente Inteligente

De acordo com a teoria de agentes inteligentes (Russell & Norvig), o CyberSentinel é caracterizado pela seguinte estrutura PEAS:

- **P**erformance (Medidas de Desempenho): 
  - Acurácia na identificação correta do vetor de ataque.
  - Alinhamento preciso com a classificação de técnicas **MITRE ATT&CK**.
  - Qualidade prática do plano de resposta (contenção, erradicação, recuperação).
  - Baixo tempo de resposta (latência de inferência local).
- **E**nvironment (Ambiente):
  - Logs brutos do sistema operacional (Syslog, SSH logins).
  - Logs de servidores Web (Apache, Nginx, IIS).
  - Alertas gerados por IPS/IDS e Firewalls.
  - Relatórios textuais de vulnerabilidades (CVEs).
- **A**ctuators (Atuadores):
  - Dashboard SOC interativo com análise em tela.
  - Relatórios técnicos formatados em Markdown.
  - Exportação de planos de mitigação e bloqueios de IPs/Portas.
- **S**ensors (Sensores):
  - Caixa de entrada de texto e upload de arquivos de log do Dashboard.
  - Informações de contexto organizacional (importância do ativo, setor da empresa).

---

## 🔄 Entradas, Processamento e Saídas

```
 📥 ENTRADA (Logs/CVE/Contexto) ──▶ 🧠 PROCESSAMENTO (LLM Fine-tuned + Regras) ──▶ 📤 SAÍDA (Dashboard/Mapeamento/Ações)
```

### 1. Entradas (Sensors)
O agente recebe duas fontes de informação:
- **Log Bruto ou Descrição do Incidente:** O log cru do evento de segurança.
- **Contexto da Organização:** A criticidade do servidor afetado e o nicho de mercado (ajuda a ajustar o impacto de Confidencialidade, Integridade e Disponibilidade - CIA).

### 2. Processamento (CPU / Local GGUF)
O processamento é realizado por um modelo de linguagem otimizado (**Qwen3.5-2B-Instruct**) ajustado de forma supervisionada com adaptadores LoRA (QLoRA) para cibersegurança. 
O processamento envolve:
1. **Parsing da Entrada:** Extração de metadados como IPs de origem, portas, usuários e payloads.
2. **Contextualização e Prompting:** O agente combina a entrada com instruções sistêmicas rígidas de SOC Analyst.
3. **Inferencia Local:** O motor `llama-cpp-python` executa os pesos quantizados em CPU local, realizando a análise técnica com foco em cibersegurança defensiva.

### 3. Saídas (Actuators)
A resposta gerada pelo modelo é formatada rigidamente no seguinte padrão:
- **Classificação da Ameaça:** Tipo exato de ataque (ex: *Brute Force*, *SQL Injection*, *Privilege Escalation*) e sua Severidade (Critica, Alta, Média, Baixa ou Informativa).
- **Mapeamento MITRE ATT&CK:** Mapeia o log para uma Tática e Técnica real (ex: *Tática: Credential Access (TA0006)*, *Técnica: Brute Force (T1110)*).
- **Análise de Impacto (CIA Triad):** Avaliação de quão afetados foram a Confidencialidade, Integridade e Disponibilidade dos sistemas.
- **Plano de Resposta a Incidentes:** Passos claros de **Contenção** (ex: bloquear IP no firewall), **Erradicação** (ex: remover usuário comprometido) e **Recuperação** (ex: restaurar backup).

---

## 🧠 Pipeline de Fine-Tuning (Treinamento do Especialista)

Modelos generativos comuns de linguagem (como ChatGPT ou Gemini base) costumam falhar ao analisar logs brutos de segurança porque não possuem treinamento focado e contextualizado na sintaxe e nos jargões de segurança da informação.

Para solucionar isso, o CyberSentinel passou por um ajuste fino (fine-tuning):
- **Modelo Base:** `unsloth/Qwen3.5-2B-Instruct` devido a sua alta velocidade, eficiência e forte capacidade de reasoning.
- **Dataset Real Utilizado:** **AttackQA** (SambaNova Systems), disponível publicamente no HuggingFace. Contém mais de **25.000 anotações reais** de perguntas e respostas detalhadas sobre táticas, técnicas, mitigações e ameaças da base oficial do MITRE ATT&CK.
- **Método de Otimização:** **QLoRA (Quantized Low-Rank Adaptation)** com precisão de 4 bits. O treinamento otimizou os pesos das matrizes de atenção e perceptrons multicamadas (`target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]`) com rank `r=16` e fator de escala `alpha=16`.
- **Exportação GGUF:** O script funde os adaptadores LoRA aprendidos de cibersegurança com o modelo base e exporta um arquivo `.gguf` quantizado em 4 bits (`q4_k_m`), que permite executar a inferência de forma leve em qualquer processador (CPU) comum sem necessitar de placas de vídeo (GPU).

> 💡 O script de fine-tuning adaptado e comentado para execução no Google Colab está localizado no diretório: `training/cybersentinel_finetune.py`.

---

## 🖥️ Interface Customizada (Dashboard SOC)

A interface web foi desenvolvida sob medida com uma identidade visual moderna de Centro de Operações de Segurança (SOC):
- **Tema Dark Cyber:** Paleta de cores tecnológica e neon para indicação de estados e severidades.
- **Métricas em Tempo Real:** Contador de ameaças analisadas e cálculo de latência de inferência do modelo local.
- **Gráfico Dinâmico de Severidade:** Gráfico no formato Doughnut (Chart.js) que se atualiza automaticamente conforme novas ameaças de diferentes criticidades são diagnosticadas.
- **Templates Reais Integrados:** O usuário (ou professor) pode testar com um único clique quatro simulações de ataques populares: *SSH Brute Force*, *SQL Injection*, *DDoS HTTP Flood* e *Ransomware Alert*.

---

## 🚀 Instruções para Execução Local (Docker)

### Pré-requisitos
Certifique-se de ter instalado em sua máquina:
1. [Docker Desktop](https://www.docker.com/products/docker-desktop/) rodando e com o serviço ativado.

### Inicialização Rápida no Windows
1. Extraia o projeto.
2. Dê um duplo clique no arquivo `setup.bat` localizado na raiz do projeto.
3. O script irá verificar as configurações do Docker e executar os containers.
4. *Nota: Na primeira inicialização, o Docker baixará automaticamente o modelo padrão GGUF de ~2GB do HuggingFace e compilará o interpretador llama-cpp-python. Isso pode levar alguns minutos dependendo do seu hardware e internet.*
5. Abra o navegador em: **`http://localhost`** para testar!

### Inicialização Manual (Qualquer OS - Linux / macOS)
Caso esteja em outro sistema operacional, abra o terminal na pasta raiz do projeto e execute:

```bash
# Subir os containers do backend e frontend em segundo plano
docker-compose up --build -d
```

Após a inicialização concluir, acesse `http://localhost` em seu navegador. O painel da API FastAPI estará disponível para consultas em `http://localhost:8000/docs`.

### Utilizando seu modelo fine-tune do Colab
Se você executou o notebook de fine-tuning e gerou seu próprio arquivo GGUF:
1. Pare os containers com `docker-compose down`.
2. Pegue o arquivo `.gguf` gerado no Colab e renomeie-o para `model.gguf`.
3. Substitua o arquivo existente na pasta local `backend/models/model.gguf`.
4. Inicie o Docker novamente com `docker-compose up -d`. O Docker usará instantaneamente o seu modelo customizado!
