# 📊 Metodologia de Avaliação de Assertividade do CyberSentinel

Este documento descreve a metodologia e as diretrizes recomendadas para auditar, mensurar e comparar a assertividade das análises de incidentes geradas pelos modelos **Qwen Nativo** e **CyberSentinel (Fine-tuned)**.

---

## 1. Objetivos da Avaliação

O principal objetivo desta metodologia é garantir a confiabilidade técnica dos relatórios emitidos pela IA no Security Operations Center (SOC). Queremos validar se as previsões automatizadas estão corretas em relação a especialistas humanos e conjuntos de dados de referência (*Ground Truth*).

A avaliação analisa tanto a **precisão técnica** das informações de segurança fornecidas quanto a **qualidade de formatação e estrutura** das respostas geradas pelo modelo.

---

## 2. Pilares de Avaliação & Métricas de Desempenho

A assertividade é dividida em **4 pilares fundamentais**:

| Pilar | Métrica | O que Mede | Como Avaliar |
|---|---|---|---|
| **1. Classificação de Severidade** | F1-Score / Matriz de Confusão | Se a severidade atribuída (CRITICAL, HIGH, MEDIUM, LOW, INFO) condiz com a gravidade do incidente real. | Comparação direta do rótulo previsto contra o rótulo esperado do dataset de teste. |
| **2. Mapeamento MITRE ATT&CK** | Taxa de Acerto Exato (Exact Match) | A precisão na identificação de Táticas e Técnicas do framework MITRE ATT&CK (ex: T1190 para SQL Injection). | Extração das tags e códigos de técnicas na resposta e comparação com o gabarito. |
| **3. Ação de Resposta (Mitigação)** | Score de Utilidade (Rubrica 1-5) | A exequibilidade, relevância e segurança dos passos descritos para contenção e erradicação do ataque. | Avaliação via "LLM-as-a-judge" ou auditoria humana cega (Double-Blind Expert Review). |
| **4. Aderência ao Formato** | Taxa de Conformidade Estrutural | Se o modelo seguiu o formato markdown solicitado e encerrou/escondeu corretamente as tags de raciocínio `<think>`. | Validação sintática automática (Expressões Regulares / Parsers Markdown). |

---

## 3. Matriz de Avaliação Detalhada

### 3.1 Classificação de Severidade
Os alertas devem ser classificados seguindo a tabela padrão abaixo:

*   **CRITICAL**: Ataques ativos com vazamento de dados confirmado, execução de código remoto (RCE) em produção ou criptografia por Ransomware.
*   **HIGH**: Tentativas de intrusão bem-sucedidas sem privilégios administrativos, varreduras agressivas em portas de serviços críticos, ou explorações ativas sem vazamento confirmado.
*   **MEDIUM**: Ataques de força bruta (ex: SSH brute force) sem sucesso, tentativas malsucedidas de SQL Injection/XSS bloqueadas pelo WAF.
*   **LOW**: Varreduras de portas comuns (port scanning), anomalias de rede menores, acessos de IPs suspeitos em áreas não críticas.
*   **INFO**: Atividades normais do sistema, auditorias agendadas ou logs de depuração.

**Cálculo da Acurácia de Severidade:**
$$\text{Acurácia} = \frac{\text{Classificações Corretas}}{\text{Total de Casos Analisados}}$$

---

### 3.2 Rubrica de Qualidade para Planos de Resposta e Mitigação (Escala 1 a 5)

Para medir a qualidade e utilidade prática das recomendações do modelo, utilize a seguinte escala de avaliação:

*   **Nota 5 (Excelente)**: As recomendações contêm ações exatas e viáveis de contenção imediata (ex: bloquear IP no firewall x, isolar máquina y), erradicação da causa raiz e etapas de recuperação rápida. Sem alucinações.
*   **Nota 4 (Bom)**: Recomendações sólidas e aplicáveis, mas ligeiramente genéricas. Podem exigir adaptação manual mínima de comandos ou nomes de ferramentas.
*   **Nota 3 (Aceitável)**: Plano conceitualmente correto, porém genérico (ex: "atualize o sistema e use senhas fortes"). Não prejudica a segurança, mas requer bastante esforço do analista de infraestrutura para executar.
*   **Nota 2 (Incompleto/Fraco)**: Recomendações incompletas que deixam passar etapas vitais (ex: sugere redefinir a senha do usuário, mas ignora o isolamento do servidor que continua enviando tráfego malicioso).
*   **Nota 1 (Inseguro/Inútil)**: Recomendações prejudiciais ou completamente alucinadas que poderiam comprometer ainda mais o ambiente se seguidas (ex: reiniciar um banco de dados no meio de um ataque sem salvar logs para análise forense).

---

## 4. Roteiro Prático de Auditoria de Modelos (Passo a Passo)

### Passo 1: Construção do Dataset de Teste (*Golden Dataset*)
Prepare um arquivo CSV ou JSON chamado `golden_dataset.json` contendo no mínimo 20 a 50 exemplos representativos. Cada exemplo deve ter a seguinte estrutura:

```json
[
  {
    "id": "CASE-001",
    "log": "May 20 10:24:45 prod-web-server sshd[18245]: Failed password for invalid user admin from 185.220.101.42 port 54820 ssh2...",
    "context": "Servidor de Produção Linux. Setor de E-commerce.",
    "ground_truth": {
      "severity": "MEDIUM",
      "mitre_tactics": ["Credential Access"],
      "mitre_techniques": ["T1110", "T1110.001"]
    }
  }
]
```

### Passo 2: Execução em Lote (Batch Evaluation)
Crie um script em Python para ler o *Golden Dataset*, realizar as requisições de inferência para ambos os modelos (`qwen_nativo` e `qwen_finetuned`) e guardar as respostas brutas.

### Passo 3: Parsing e Extração Automática
Utilize expressões regulares para extrair os dados gerados pelo modelo nas seções de resposta:

```python
import re

def parse_model_response(text):
    # Extrai o nível de severidade
    severity_match = re.search(r"🔴\s*Classificação da Ameaça:\s*(CRITICAL|HIGH|MEDIUM|LOW|INFO)", text, re.IGNORECASE)
    severity = severity_match.group(1).upper() if severity_match else None
    
    # Extrai as técnicas MITRE ATT&CK (ex: T1110)
    techniques = re.findall(r"T\d{4}(?:\.\d{3})?", text)
    
    return {
        "severity": severity,
        "techniques": list(set(techniques))
    }
```

### Passo 4: Tabulação e Cálculo das Métricas
Compare as previsões extraídas com os valores do `ground_truth`. Documente a acurácia global, taxa de conformidade do formato markdown e a nota média dos planos de mitigação.

---

## 5. Script de Exemplo para Teste Automatizado de Aderência e Precisão

Salve o código a seguir na pasta `<appDataDir>\brain\<conversation-id>/scratch/avaliador_assertividade.py` para executar uma rotina automatizada de teste contra o endpoint local do CyberSentinel:

```python
import urllib.request
import json
import re

# Configurações do teste
API_URL = "http://localhost:8000/analyze"
TEST_LOG = """
May 20 10:24:45 prod-web-server sshd[18245]: Failed password for invalid user admin from 185.220.101.42 port 54820 ssh2
May 20 10:24:48 prod-web-server sshd[18247]: Failed password for invalid user admin from 185.220.101.42 port 54824 ssh2
"""
EXPECTED_SEVERITY = "MEDIUM"

def test_model(model_name):
    data = json.dumps({
        "log": TEST_LOG,
        "context": "Teste de Sandbox"
    }).encode('utf-8')
    
    req = urllib.request.Request(
        f"{API_URL}?model={model_name}", 
        data=data, 
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            
            # Verifica se há a seção correta e as tags
            has_think_leak = "<think>" in html or "</think>" in html
            has_classification = "Classificação da Ameaça" in html
            has_mitre = "Mapeamento MITRE ATT&CK" in html
            
            # Tenta extrair severidade
            sev_match = re.search(r"Classificação da Ameaça:.*?([A-Z]{4,8})", html, re.DOTALL)
            detected_sev = sev_match.group(1) if sev_match else "NÃO DETECTADA"
            
            print(f"=== RESULTADO MODELO: {model_name.upper()} ===")
            print(f"-> Severidade Detectada: {detected_sev} (Esperada: {EXPECTED_SEVERITY})")
            print(f"-> Converteu tags de pensamento? {'Não (Vazou tag)' if has_think_leak else 'Sim (Ok)'}")
            print(f"-> Contém cabeçalhos exigidos? {'Sim' if (has_classification and has_mitre) else 'Não'}")
            print(f"-> Resposta final possui tamanho: {len(html)} bytes")
            print("-" * 50)
            
    except Exception as e:
        print(f"Erro ao conectar ao modelo {model_name}: {e}")

if __name__ == "__main__":
    print("Iniciando auditoria rápida de conformidade...\n")
    test_model("nativo")
    test_model("finetuned")
```

---

## 6. Template de Relatório Comparativo Final

Use esta estrutura para consolidar as análises após o término de um ciclo de testes:

1.  **Acurácia de Severidade**: Qwen Nativo (X%) vs. CyberSentinel Fine-tuned (Y%)
2.  **Acurácia MITRE ATT&CK**: Qwen Nativo (X%) vs. CyberSentinel Fine-tuned (Y%)
3.  **Aderência ao Idioma Português (Thinking + Output)**:
    *   *Nativo*: Se tendeu a alucinar ou pensar em inglês.
    *   *CyberSentinel*: Raciocínio consistente e 100% em português.
4.  **Qualidade Média da Mitigação (1-5)**: Qwen Nativo (Média) vs. CyberSentinel (Média)
5.  **Principais Falhas Encontradas**: Descrever se houve alucinações repetidas ou perda de formatação markdown.
