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
    
    // Métricas
    const metricCountEl = document.getElementById('metric-count');
    const metricTimeEl = document.getElementById('metric-time');
    
    // Modal
    const btnShowAbout = document.getElementById('btn-show-about');
    const aboutModal = document.getElementById('about-modal');
    const closeModal = aboutModal.querySelector('.close-modal');
    
    // Templates
    const templateButtons = document.querySelectorAll('.btn-template');

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
                        '#ff3131', // CRITICAL
                        '#ff9000', // HIGH
                        '#ffea00', // MEDIUM
                        '#00f0ff', // LOW
                        '#8ea1b4'  // INFO
                    ],
                    borderWidth: 1,
                    borderColor: '#0c1020'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: '#8ea1b4',
                            font: {
                                family: 'Inter',
                                size: 10
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

    // === ENVIAR REQUISIÇÃO DE ANÁLISE ===
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (!isConnected) {
            alert('Erro: O servidor da API do CyberSentinel está desconectado. Certifique-se de que o Docker Backend está rodando.');
            return;
        }

        const logContent = logInput.value.trim();
        const orgContext = contextInput.value.trim();

        if (!logContent) return;

        // Ativa estado de carregamento do botão
        btnSubmit.disabled = true;
        submitText.classList.add('hidden');
        spinner.classList.remove('hidden');

        const baseUrl = apiUrlInput.value.trim();

        try {
            const response = await fetch(`${baseUrl}/analyze`, {
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
                const errData = await response.json();
                throw new Error(errData.detail || 'Erro ao processar modelo.');
            }

            const data = await response.json();
            
            // Sucesso - Renderizar relatório
            outputPlaceholder.classList.add('hidden');
            outputContent.classList.remove('hidden');
            btnCopyReport.classList.remove('hidden');
            executionTag.classList.remove('hidden');
            
            // Executa conversão de Markdown para HTML usando marked.js
            outputContent.innerHTML = marked.parse(data.raw_response);
            executionTag.textContent = `${data.processing_time_sec.toFixed(2)}s`;

            // Extrai a severidade da resposta para atualizar o gráfico (Regex simples)
            detectAndAddSeverity(data.raw_response);

            // Atualiza métricas globais
            totalAnalyzed++;
            totalTime += data.processing_time_sec;
            
            metricCountEl.textContent = totalAnalyzed;
            metricTimeEl.textContent = `${(totalTime / totalAnalyzed).toFixed(1)}s`;

            // Scroll suave até o relatório gerado
            outputContent.scrollIntoView({ behavior: 'smooth' });

        } catch (error) {
            alert(`Erro na análise: ${error.message}`);
        } finally {
            // Restaura o botão
            btnSubmit.disabled = false;
            submitText.classList.remove('hidden');
            spinner.classList.add('hidden');
        }
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
