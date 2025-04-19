@echo off
echo Ativando ambiente virtual...
call .venv\Scripts\activate.bat

echo Iniciando servidor FastAPI...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8010 

pause
