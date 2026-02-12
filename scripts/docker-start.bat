@echo off
REM ─────────────────────────────────────────────
REM MetinForge — Launcher (Docker + VcXsrv)
REM ─────────────────────────────────────────────
REM Inicia VcXsrv si no está corriendo y luego
REM levanta el contenedor Docker con la GUI.
REM ─────────────────────────────────────────────

echo [MetinForge] Verificando VcXsrv...

tasklist /FI "IMAGENAME eq vcxsrv.exe" 2>NUL | find /I "vcxsrv.exe" >NUL
if %ERRORLEVEL% NEQ 0 (
    echo [MetinForge] Iniciando VcXsrv...
    start "" "C:\Program Files\VcXsrv\vcxsrv.exe" :0 -multiwindow -clipboard -ac -nowgl
    timeout /t 2 /nobreak >NUL
    echo [MetinForge] VcXsrv iniciado.
) else (
    echo [MetinForge] VcXsrv ya esta corriendo.
)

echo [MetinForge] Levantando contenedor Docker...
docker compose up --build
