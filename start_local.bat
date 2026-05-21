@echo off
title CyberSentinel -- Inicializacao Local (Sem Docker)
color 0B

echo =====================================================================
echo              🛡️  CyberSentinel -- SOC Virtual Inteligente 🛡️
echo                   (Execucao Nativa em Python)
echo =====================================================================
echo.
echo Este utilitario ira configurar o ambiente Python local (venv),
echo instalar as dependencias necessarias, baixar o modelo (se preciso)
echo e inicializar o agente e o painel web.
echo.

:: 1. Verifica se o Python esta instalado
python --version >nul 2>&1
if %errorlevel% == 0 goto python_ok
color 0C
echo [ERRO] O Python nao foi encontrado no seu sistema.
echo Por favor, instale o Python (versao recomendada: 3.10 a 3.12) e
echo marque a opcao "Add Python to PATH" durante a instalacao.
echo.
pause
exit /b 1
:python_ok

:: 1.1 Verifica se a versao do Python e >= 3.13
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 13) else 1)" >nul 2>&1
if %errorlevel% == 1 goto python_version_ok
color 0E
echo =====================================================================
echo [ATENCAO] Versao do Python nao recomendada!
echo Voce esta usando o Python 3.13 ou superior (detectado 3.14+). Nao existem
echo pacotes pre-compilados (wheels) para esta versao no Windows.
echo.
echo Isso exige que seu computador compile bibliotecas de IA e core do zero:
echo - llama-cpp-python (requer Build Tools C++ do Visual Studio)
echo - pydantic-core (requer compilador Rust)
echo.
echo Como voce nao possui esses compiladores instalados, a instalacao falha.
echo.
echo [SOLUCAO RECOMENDADA]
echo Por favor, desinstale a versao atual e instale o Python 3.12 (ou 3.11/3.10).
echo Link para download: https://www.python.org/downloads/
echo.
echo Com o Python 3.12, o setup instalara tudo em segundos sem compilar nada!
echo =====================================================================
echo.
pause
exit /b 1
:python_version_ok

:: 2. Cria o ambiente virtual se nao existir
if exist "venv" goto venv_ok
echo [INFO] Criando ambiente virtual Python (venv)...
python -m venv venv
if %errorlevel% == 0 goto venv_created
color 0C
echo [ERRO] Falha ao criar o ambiente virtual (venv).
pause
exit /b 1
:venv_created
echo [INFO] Ambiente virtual criado com sucesso.
:venv_ok

:: 3. Ativa o ambiente virtual e instala dependencias
echo [INFO] Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo [INFO] Atualizando pip...
python -m pip install --upgrade pip >nul 2>&1

echo [INFO] Instalando dependencias do projeto...
echo (Isso pode levar de 2 a 5 minutos na primeira vez. Por favor, aguarde...)
pip install -r backend\requirements.txt --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
if %errorlevel% == 0 goto requirements_ok
color 0C
echo [ERRO] Ocorreu um erro ao instalar as dependencias.
echo Verifique sua conexao com a internet e tente novamente.
echo.
pause
exit /b 1
:requirements_ok

:: 4. Garante que a pasta de modelos existe
if not exist "backend\models" mkdir "backend\models"

:: 5. Verifica/Baixa o modelo GGUF
if exist "backend\models\model.gguf" goto model_ok
echo.
echo =====================================================================
echo [AVISO] O modelo base Qwen-3.5-2B GGUF (~1.3GB) nao foi encontrado.
echo Iniciando o download automatico direto do HuggingFace...
echo =====================================================================
echo.
python backend\download_model.py
if %errorlevel% == 0 goto model_ok
color 0C
echo [ERRO] Falha ao baixar o modelo. Verifique sua conexao.
pause
exit /b 1
:model_ok

:: 6. Abre o navegador e inicia o uvicorn
echo.
echo =====================================================================
echo [SUCESSO] Ambiente configurado!
echo [INFO] Iniciando o servidor e abrindo o painel no navegador...
echo =====================================================================
echo.

:: Inicia uma rotina em background para abrir o navegador apos 3 segundos
start /b cmd /c "timeout /t 3 >nul && start http://localhost:8000"

:: Executa o FastAPI
python backend\app.py

pause
