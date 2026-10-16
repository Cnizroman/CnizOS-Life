@echo off
echo === CnizOS Bridge — One-Click Install (Windows) ===
echo.

REM 1. Python check
python --version >nul 2>&1
if errorlevel 1 (
  echo [x] Python не найден. Поставь Python 3.13 с https://python.org (галочка Add to PATH)
  pause
  exit /b
)

echo [1/4] Ставлю зависимости...
pip install -r requirements.txt

echo [2/4] Вставь bridge_token из браузера (PC Control - Register) и нажми Enter:
set /p TOKEN=
echo [3/4] Настраиваю...
python -m bridge.main --setup --server wss://cnizos.example.com/ws/bridge --token %TOKEN%
REM Для локального теста замени на ws://localhost:8000/ws/bridge

echo [4/4] Ставлю в автозагрузку...
python -m bridge.main --install-autostart

echo.
echo === ГОТОВО! ===
echo Запуск: python -m bridge.main  (или CnizOS-Bridge.exe если собрал)
echo Логи: %%APPDATA%%\CnizOS\bridge.log
echo Чтобы проверить: открой PC Control в браузере — статус должен стать online
pause
