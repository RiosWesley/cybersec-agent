@echo off
title CyberSentinel Setup & Startup Utility
color 0B

echo =====================================================================
echo              🛡️  CyberSentinel -- SOC Virtual Inteligente 🛡️
echo =====================================================================
echo.
echo Este utilitario ira configurar e inicializar o agente localmente.
echo.

:: Verifica se o Docker esta instalado e rodando
docker info >nul 2>&1
if %errorlevel% == 0 goto docker_ok
echo [AVISO] O Docker nao foi detectado ou nao esta em execucao.
echo Como alternativa, iremos iniciar no modo NATIVO em Python (sem Docker)...
echo.
timeout /t 3 >nul
call start_local.bat
exit /b 0
:docker_ok

echo [INFO] Docker detectado e rodando com sucesso.
echo [INFO] Criando diretorios locais necessarios...
if not exist "backend\models" mkdir "backend\models"

echo.
echo =====================================================================
echo [ATENCAO] Na primeira execucao, o Docker ira:
echo 1. Compilar o motor de inferencia llama-cpp-python para CPU.
echo 2. Baixar automaticamente o modelo base Qwen-3.5-2B GGUF (1.3GB).
echo.
echo Isso pode levar de 5 a 15 minutos dependendo da sua conexao e hardware.
echo Nas proximas execucoes o carregamento sera instantaneo.
echo =====================================================================
echo.
echo Pressione qualquer tecla para iniciar os containers via docker-compose...
pause >nul

echo.
echo [INFO] Subindo containers via Docker Compose...
docker-compose up --build -d

if %errorlevel% neq 0 (
    color 0C
    echo [ERRO] Ocorreu uma falha ao tentar subir os containers.
    echo Verifique os logs do Docker acima.
    echo.
    pause
    exit /b 1
)

echo.
echo =====================================================================
echo 🛡️  CyberSentinel inicializado com sucesso!
echo =====================================================================
echo.
echo Acesse a interface web no seu navegador:
echo 👉 http://localhost
echo.
echo O backend estara exposto e processando em:
echo 👉 http://localhost:8000
echo.
echo Para ver os logs ou parar a execucao:
echo - Ver Logs:   docker-compose logs -f
echo - Parar:      docker-compose down
echo =====================================================================
echo.
pause
