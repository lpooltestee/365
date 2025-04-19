@echo off
cd /d %~dp0
call .venv\Scripts\activate

:: Executa uvicorn com as configurações internas do main.py (.env já carregado lá)
uvicorn backend.main:app --host 0.0.0.0 --port 8010 
