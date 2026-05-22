document.addEventListener('DOMContentLoaded', () => {
    // === SELETORES DOM ===
    const apiUrlInput = document.getElementById('api-url-input');
    const modelStatusEl = document.getElementById('model-status');
    const apiStatusEl = document.getElementById('api-status');
    const form = document.getElementById('analysis-form');
    const logInput = document.getElementById('log-input');
    const contextInput = document.getElementById('context-input');
    const btnSubmit = document.getElementById('btn-submit');
    const submitText = btnSubmit.querySelector('.btn-text');
    const spinner = btnSubmit.querySelector('.spinner');
    
    // Elementos de Resposta
    const outputPlaceholder = document.getElementById('output-placeholder');
    const outputContent = document.getElementById('output-content');
    const btnCopyReport = document.getElementById('btn-copy-report');
    const executionTag = document.getElementById('execution-tag');
    
    // Elementos de Raciocínio (Thinking)
    const thinkingContainer = document.getElementById('thinking-container');
    const thinkingContent = document.getElementById('thinking-content');
    const thinkingStatusText = document.getElementById('thinking-status-text');
    const btnToggleThinking = document.getElementById('btn-toggle-thinking');
    
    // Botão e Containers de Comparação Lado a Lado
    const btnCompareToggle = document.getElementById('btn-compare-toggle');
    const singleModelOutput = document.getElementById('single-model-output');
    const compareModelOutput = document.getElementById('compare-model-output');
    
    // Elementos Qwen Nativo
    const thinkingContainerNativo = document.getElementById('thinking-container-nativo');
    const thinkingContentNativo = document.getElementById('thinking-content-nativo');
    const thinkingStatusTextNativo = document.getElementById('thinking-status-text-nativo');
    const btnToggleThinkingNativo = document.getElementById('btn-toggle-thinking-nativo');
    const outputContentNativo = document.getElementById('output-content-nativo');
    const executionTagNativo = document.getElementById('execution-tag-nativo');
    
    // Elementos CyberSentinel (Finetuned)
    const thinkingContainerFinetuned = document.getElementById('thinking-container-finetuned');
    const thinkingContentFinetuned = document.getElementById('thinking-content-finetuned');
    const thinkingStatusTextFinetuned = document.getElementById('thinking-status-text-finetuned');
    const btnToggleThinkingFinetuned = document.getElementById('btn-toggle-thinking-finetuned');
    const outputContentFinetuned = document.getElementById('output-content-finetuned');
    const executionTagFinetuned = document.getElementById('execution-tag-finetuned');
    
    // Métricas
    const metricCountEl = document.getElementById('metric-count');
    const metricTimeEl = document.getElementById('metric-time');
    
    // Modal
    const btnShowAbout = document.getElementById('btn-show-about');
    const aboutModal = document.getElementById('about-modal');
    const closeModal = aboutModal.querySelector('.close-modal');
    
    // Templates
    const templateButtons = document.querySelectorAll('.btn-template');

    // === ESTADO DE COMPARAÇÃO ===
    let isCompareMode = false;

    // === ESTADO GLOBAL DO APP ===
    let totalAnalyzed = 0;
    let totalTime = 0.0;
    let isConnected = false;
    let severityCounts = {
        'CRITICAL': 0,
        'HIGH': 0,
        'MEDIUM': 0,
        'LOW': 0,
        'INFO': 0
    };
    let severityChartObj = null;

    // === TEMPLATES DE LOGS CIBERNÉTICOS REAIS ===
    const logsTemplates = {
        ssh_brute: `May 20 10:24:45 prod-web-server sshd[18245]: Failed password for invalid user admin from 185.220.101.42 port 54820 ssh2
May 20 10:24:48 prod-web-server sshd[18247]: Failed password for invalid user admin from 185.220.101.42 port 54824 ssh2
May 20 10:24:51 prod-web-server sshd[18251]: Failed password for invalid user backup from 185.220.101.42 port 54832 ssh2
May 20 10:24:53 prod-web-server sshd[18255]: Failed password for invalid user guest from 185.220.101.42 port 54840 ssh2
May 20 10:24:56 prod-web-server sshd[18260]: Failed password for root from 185.220.101.42 port 54846 ssh2
May 20 10:24:59 prod-web-server sshd[18264]: Failed password for root from 185.220.101.42 port 54850 ssh2`,
        
        sql_inject: `192.168.4.82 - - [20/May/2026:10:31:02 -0300] "POST /api/v1/users/login HTTP/1.1" 500 1284 "http://company.com/login" "Mozilla/5.0"
Payload enviado no campo 'username':
' OR '1'='1' -- 
' UNION SELECT username, password FROM users --
ADMIN' AND 1=1 --`,
        
        ddos: `Detectado tráfego anormal em direção ao servidor de borda 'proxy-nginx-01'.
Taxa de conexões simultâneas saltou de 120 req/s para 45.800 req/s em um intervalo de 45 segundos.
Mais de 95% do tráfego consiste em requisições GET para '/' sem cabeçalho User-Agent definido.
Faixa de IPs de origem: Distribuição global (Botnet baseada em IoT).`,
        
        ransomware: `Security Alert from CarbonBlack EDR:
Dispositivo: ESTACAO-FINANCEIRO-04 (IP: 10.0.12.54)
Processo Suspeito: 'update_java.exe' executando a partir do diretório C:\\Users\\User\\AppData\\Local\\Temp\\
Ação Detectada: Modificação em lote de 1.450 arquivos em menos de 10 segundos com alteração de extensões para '.locked'.
Criação do arquivo: 'HOW_TO_DECRYPT.txt' contendo instrução de pagamento em carteira BTC.`
    };

    // === INICIALIZAÇÃO DO GRÁFICO (Chart.js) ===
    function initChart() {
        const ctx = document.getElementById('severity-chart').getContext('2d');
        severityChartObj = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Crítico', 'Alto', 'Médio', 'Baixo', 'Informativo'],
                datasets: [{
                    data: [0, 0, 0, 0, 0],
                    backgroundColor: [
                        '#ff2e5b', // CRITICAL (Crimson)
                        '#ff9000', // HIGH (Orange)
                        '#ffd900', // MEDIUM (Yellow)
                        '#00f3ff', // LOW (Cyan)
                        '#a1a1aa'  // INFO (Zinc)
                    ],
                    borderWidth: 1,
                    borderColor: '#09090c'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: '#a1a1aa',
                            font: {
                                family: 'Share Tech Mono',
                                size: 11
                            }
                        }
                    }
                },
                cutout: '65%'
            }
        });
    }

    // === VERIFICAÇÃO DE SAÚDE DA API ===
    async function checkApiHealth() {
        const baseUrl = apiUrlInput.value.trim();
        try {
            const response = await fetch(`${baseUrl}/health`, { method: 'GET' });
            if (response.ok) {
                const data = await response.json();
                isConnected = true;
                
                // Atualiza conexões da API
                apiStatusEl.textContent = 'Conectado';
                apiStatusEl.className = 'status-indicator online';
                
                // Status do modelo GGUF
                if (data.model_loaded) {
                    modelStatusEl.textContent = 'Carregado';
                    modelStatusEl.className = 'status-indicator online';
                } else if (data.model_file_exists) {
                    modelStatusEl.textContent = 'Carregando...';
                    modelStatusEl.className = 'status-indicator loading';
                } else {
                    modelStatusEl.textContent = 'Sem Modelo';
                    modelStatusEl.className = 'status-indicator offline';
                }
            } else {
                throw new Error('Retorno inválido');
            }
        } catch (e) {
            isConnected = false;
            apiStatusEl.textContent = 'Desconectado';
            apiStatusEl.className = 'status-indicator offline';
            modelStatusEl.textContent = 'Offline';
            modelStatusEl.className = 'status-indicator offline';
        }
    }

    // Polling de saúde a cada 5 segundos
    checkApiHealth();
    setInterval(checkApiHealth, 5000);
    apiUrlInput.addEventListener('change', checkApiHealth);

    // === CARREGAR TEMPLATES DE LOG ===
    templateButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const type = btn.getAttribute('data-type');
            if (logsTemplates[type]) {
                logInput.value = logsTemplates[type];
                
                // Adiciona um contexto automático adequado
                if (type === 'ssh_brute' || type === 'ddos') {
                    contextInput.value = 'Servidor Web de Produção Linux. Setor de E-commerce.';
                } else if (type === 'sql_inject') {
                    contextInput.value = 'Banco de dados crítico com informações cadastrais de clientes.';
                } else if (type === 'ransomware') {
                    contextInput.value = 'Desktop administrativo na rede corporativa. Acesso a compartilhamento Samba.';
                }
            }
        });
    });

    // Toggle para o acordeão do raciocínio
    btnToggleThinking.addEventListener('click', () => {
        thinkingContainer.classList.toggle('active');
    });

    // Toggle do acordeão nativo
    btnToggleThinkingNativo.addEventListener('click', () => {
        thinkingContainerNativo.classList.toggle('active');
    });

    // Toggle do acordeão finetuned
    btnToggleThinkingFinetuned.addEventListener('click', () => {
        thinkingContainerFinetuned.classList.toggle('active');
    });

    // Toggle Comparação Lado a Lado
    btnCompareToggle.addEventListener('click', () => {
        isCompareMode = !isCompareMode;
        if (isCompareMode) {
            btnCompareToggle.classList.add('active');
            singleModelOutput.classList.add('hidden');
            compareModelOutput.classList.remove('hidden');
            
            // Oculta botões do modo individual
            btnCopyReport.classList.add('hidden');
            executionTag.classList.add('hidden');
        } else {
            btnCompareToggle.classList.remove('active');
            singleModelOutput.classList.remove('hidden');
            compareModelOutput.classList.add('hidden');
        }
        
        // Reseta placeholder
        outputPlaceholder.classList.remove('hidden');
        
        // Oculta layouts internos
        thinkingContainer.classList.add('hidden');
        outputContent.classList.add('hidden');
        thinkingContainerNativo.classList.add('hidden');
        outputContentNativo.classList.add('hidden');
        thinkingContainerFinetuned.classList.add('hidden');
        outputContentFinetuned.classList.add('hidden');
    });

    // === FUNÇÃO AUXILIAR DE STREAMING POR MODELO ===
    async function streamModel(modelName, elements, logContent, orgContext, baseUrl) {
        const { container, content, status, output, execTag } = elements;
        const startTime = performance.now();

        // Reseta estados
        container.classList.add('hidden');
        container.classList.remove('active');
        content.textContent = '';
        status.textContent = 'Raciocínio da IA: Processando...';
        output.classList.add('hidden');
        output.innerHTML = '';
        execTag.classList.add('hidden');

        try {
            const response = await fetch(`${baseUrl}/analyze?model=${modelName}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    log: logContent,
                    context: orgContext
                })
            });

            if (!response.ok) {
                let errText = '';
                try {
                    const errData = await response.json();
                    errText = errData.detail || 'Erro desconhecido.';
                } catch {
                    errText = await response.text();
                }
                throw new Error(errText || 'Erro ao processar modelo.');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            
            let fullText = '';
            let reportStarted = false;

            container.classList.remove('hidden');
            container.classList.add('active');

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                fullText += chunk;

                let splitIndex = -1;
                const thinkEndIndex = fullText.indexOf('</think>');
                if (thinkEndIndex !== -1) {
                    splitIndex = thinkEndIndex + 8;
                } else {
                    const indicators = ['## 🔴', '## \uD83D\uDD34', '🔴', '## Classificação', '1. ##'];
                    for (const ind of indicators) {
                        const idx = fullText.indexOf(ind);
                        if (idx !== -1) {
                            if (splitIndex === -1 || idx < splitIndex) {
                                splitIndex = idx;
                            }
                        }
                    }
                }

                if (splitIndex !== -1) {
                    const thinkingPart = fullText.substring(0, splitIndex).trim();
                    const reportPart = fullText.substring(splitIndex).trim();

                    let cleanThinking = thinkingPart.replace(/<\/?think>/g, '').trim();
                    cleanThinking = cleanThinking.replace(/^Thinking Process:\s*/i, '');

                    if (cleanThinking) {
                        content.textContent = cleanThinking;
                        // Auto-scroll da caixa de pensamento para manter fade e scroll sincronizados
                        content.scrollTop = content.scrollHeight;
                    } else {
                        container.classList.add('hidden');
                    }

                    if (reportPart) {
                        if (!reportStarted) {
                            reportStarted = true;
                            output.classList.remove('hidden');
                            container.classList.remove('active');
                            status.textContent = 'Raciocínio da IA: Concluído (Clique para expandir)';
                        }
                        output.innerHTML = marked.parse(reportPart);
                    }
                } else {
                    let cleanThinking = fullText.replace(/<\/?think>/g, '').trim();
                    cleanThinking = cleanThinking.replace(/^Thinking Process:\s*/i, '');
                    content.textContent = cleanThinking;
                    // Auto-scroll
                    content.scrollTop = content.scrollHeight;
                }
            }

            const endTime = performance.now();
            const totalDurationSec = (endTime - startTime) / 1000;

            const hasReport = fullText.includes('## 🔴') || 
                              fullText.includes('## \uD83D\uDD34') || 
                              fullText.includes('🔴') || 
                              fullText.includes('## Classificação') || 
                              fullText.includes('</think>');

            if (hasReport) {
                status.textContent = 'Raciocínio da IA: Concluído (Clique para expandir)';
            } else {
                container.classList.add('hidden');
                output.classList.remove('hidden');
                output.innerHTML = marked.parse(fullText);
            }

            execTag.classList.remove('hidden');
            execTag.textContent = `${totalDurationSec.toFixed(2)}s`;

            return {
                success: true,
                duration: totalDurationSec,
                fullText: output.innerText || fullText
            };

        } catch (error) {
            console.error(`Erro ao rodar modelo ${modelName}:`, error);
            output.classList.remove('hidden');
            
            let displayError = error.message;
            let technicalDetails = '';
            let llamaLogsHtml = '';

            if (displayError.includes('Detalhes técnicos:')) {
                const parts = displayError.split('Detalhes técnicos:');
                displayError = parts[0].trim();
                let techMsg = parts[1].trim();

                if (techMsg.includes('(Detalhes do llama.cpp:')) {
                    const llamaParts = techMsg.split('(Detalhes do llama.cpp:');
                    techMsg = llamaParts[0].trim();
                    const rawLogs = llamaParts[1].replace(/\)$/, '').trim();
                    if (rawLogs) {
                        const logLines = rawLogs.split(' | ').map(line => `• ${line}`).join('\n');
                        llamaLogsHtml = `<div style="margin-top: 10px; background: rgba(0,0,0,0.3); border-left: 3px solid #ff3131; padding: 8px 12px; font-family: 'Courier New', Courier, monospace; font-size: 11px; max-height: 150px; overflow-y: auto; white-space: pre-wrap; line-height: 1.4; text-align: left; color: #ff8e8e; border-radius: 0 4px 4px 0;">
<div style="font-weight: bold; margin-bottom: 4px; color: #ff5555; font-family: sans-serif;">[llama.cpp diagnostic log]</div>${logLines}</div>`;
                    }
                }
                
                technicalDetails = `<div style="margin-top: 6px; font-size: 12px; opacity: 0.9; color: #ffa3a3;">
                    <strong>Erro Técnico:</strong> ${techMsg}
                </div>`;
            }

            output.innerHTML = `<div class="error-msg" style="color: #ff3131; padding: 15px; border: 1px dashed rgba(255,49,49,0.4); border-radius: 6px; font-size: 13px; background: rgba(255,49,49,0.05); text-align: left;">
                <div style="font-weight: bold; font-size: 14px; display: flex; align-items: center; gap: 8px;">
                    <i class="fa-solid fa-triangle-exclamation"></i> Falha na inferência
                </div>
                <div style="margin-top: 8px; color: #ffcccc;">
                    ${displayError}
                </div>
                ${technicalDetails}
                ${llamaLogsHtml}
            </div>`;

            return {
                success: false,
                duration: 0,
                fullText: ''
            };
        }
    }

    // === ENVIAR REQUISIÇÃO DE ANÁLISE ===
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (!isConnected) {
            alert('Erro: O servidor da API do CyberSentinel está desconectado. Certifique-se de que o backend local está rodando.');
            return;
        }

        const logContent = logInput.value.trim();
        const orgContext = contextInput.value.trim();

        if (!logContent) return;

        // Reseta estado do placeholder
        outputPlaceholder.classList.add('hidden');

        // Ativa estado de carregamento do botão
        btnSubmit.disabled = true;
        submitText.classList.add('hidden');
        spinner.classList.remove('hidden');

        const baseUrl = apiUrlInput.value.trim();

        if (!isCompareMode) {
            // === MODO INDIVIDUAL ===
            const result = await streamModel('finetuned', {
                container: thinkingContainer,
                content: thinkingContent,
                status: thinkingStatusText,
                output: outputContent,
                execTag: executionTag
            }, logContent, orgContext, baseUrl);

            if (result.success) {
                btnCopyReport.classList.remove('hidden');
                
                // Atualiza métricas
                detectAndAddSeverity(result.fullText);
                totalAnalyzed++;
                totalTime += result.duration;
                metricCountEl.textContent = totalAnalyzed;
                metricTimeEl.textContent = `${(totalTime / totalAnalyzed).toFixed(1)}s`;

                outputContent.scrollIntoView({ behavior: 'smooth' });
            }
        } else {
            // === MODO COMPARATIVO (Lado a Lado) ===
            const nativoElements = {
                container: thinkingContainerNativo,
                content: thinkingContentNativo,
                status: thinkingStatusTextNativo,
                output: outputContentNativo,
                execTag: executionTagNativo
            };

            const finetunedElements = {
                container: thinkingContainerFinetuned,
                content: thinkingContentFinetuned,
                status: thinkingStatusTextFinetuned,
                output: outputContentFinetuned,
                execTag: executionTagFinetuned
            };

            // Executa requisições de forma concorrente em background
            const [nativoRes, finetunedRes] = await Promise.all([
                streamModel('nativo', nativoElements, logContent, orgContext, baseUrl),
                streamModel('finetuned', finetunedElements, logContent, orgContext, baseUrl)
            ]);

            // Atualiza métricas gerais baseando-se no modelo CyberSentinel
            if (finetunedRes.success) {
                detectAndAddSeverity(finetunedRes.fullText);
                totalAnalyzed++;
                totalTime += finetunedRes.duration;
                metricCountEl.textContent = totalAnalyzed;
                metricTimeEl.textContent = `${(totalTime / totalAnalyzed).toFixed(1)}s`;
            }

            compareModelOutput.scrollIntoView({ behavior: 'smooth' });
        }

        // Restaura o botão de submissão
        btnSubmit.disabled = false;
        submitText.classList.remove('hidden');
        spinner.classList.add('hidden');
    });

    // === DETECÇÃO DE SEVERIDADE PARA MÉTRICAS ===
    function detectAndAddSeverity(text) {
        const upperText = text.toUpperCase();
        let detected = 'INFO';
        
        if (upperText.includes('CRITICAL') || upperText.includes('CRÍTICO')) {
            detected = 'CRITICAL';
        } else if (upperText.includes('HIGH') || upperText.includes('ALTO') || upperText.includes('ALTA')) {
            detected = 'HIGH';
        } else if (upperText.includes('MEDIUM') || upperText.includes('MÉDIO') || upperText.includes('MÉDIA')) {
            detected = 'MEDIUM';
        } else if (upperText.includes('LOW') || upperText.includes('BAIXO') || upperText.includes('BAIXA')) {
            detected = 'LOW';
        }
        
        severityCounts[detected]++;
        updateChart();
    }

    function updateChart() {
        if (!severityChartObj) return;
        
        severityChartObj.data.datasets[0].data = [
            severityCounts['CRITICAL'],
            severityCounts['HIGH'],
            severityCounts['MEDIUM'],
            severityCounts['LOW'],
            severityCounts['INFO']
        ];
        severityChartObj.update();
    }

    // === COPIAR RELATÓRIO ===
    btnCopyReport.addEventListener('click', () => {
        const textToCopy = outputContent.innerText;
        navigator.clipboard.writeText(textToCopy).then(() => {
            const originalText = btnCopyReport.innerHTML;
            btnCopyReport.innerHTML = '<i class="fa-solid fa-check"></i> Copiado!';
            setTimeout(() => {
                btnCopyReport.innerHTML = originalText;
            }, 2000);
        }).catch(err => {
            console.error('Falha ao copiar: ', err);
        });
    });

    // === INTERAÇÕES DE MODAL ===
    btnShowAbout.addEventListener('click', (e) => {
        e.preventDefault();
        aboutModal.classList.remove('hidden');
    });

    closeModal.addEventListener('click', () => {
        aboutModal.classList.add('hidden');
    });

    window.addEventListener('click', (e) => {
        if (e.target === aboutModal) {
            aboutModal.classList.add('hidden');
        }
    });

    // Inicializa o painel gráfico
    initChart();
});
