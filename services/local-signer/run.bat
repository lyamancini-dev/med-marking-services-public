@echo off
chcp 65001 > nul
cls
echo =======================================================================
echo =======================================================================
echo.

:: Путь к утилите КриптоПро
set CSPTEST_PATH=C:\Program Files\Crypto Pro\CSP\csptest.exe

set CERT_THUMBPRINT=0000000000000000000000000000000000000000

:: Порт сервиса шлюза
set SIGNER_PORT=8003
set SIGNER_HOST=0.0.0.0

:: Запуск веб-сервера Python
python main.py

echo.
echo [Внимание] Сервер прекратил свою работу.
pause