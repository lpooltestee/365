import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
# Remova ou comente a linha abaixo:
# from signature_service import get_signature
from dotenv import load_dotenv
# Mantenha esta linha:
from backend.signature_service import get_signature

load_dotenv()  # Carrega o .env na raiz do projeto

app = FastAPI()
# Garanta que o diretório 'static' existe na raiz do projeto
app.mount("/static", StaticFiles(directory="static"), name="static")
# Garanta que o diretório 'backend/templates' existe
templates = Jinja2Templates(directory="backend/templates")

@app.get("/addin", response_class=HTMLResponse)
async def load_addin(request: Request):
    # Garanta que 'addin.html' existe em 'backend/templates'
    return templates.TemplateResponse("addin.html", {"request": request})

@app.get("/api/signature")
async def fetch_signature(email: str):
    signature = get_signature(email)
    return {"signature_html": signature}

# Variáveis de certificado TLS (para uvicorn externo)
SSL_CERTFILE = os.getenv("SSL_CERTFILE")
SSL_KEYFILE = os.getenv("SSL_KEYFILE")

if __name__ == "__main__":
    import uvicorn
    # Esta parte é para execução direta (python backend/main.py)
    # O start.bat provavelmente usa 'uvicorn backend.main:app ...'
    uvicorn.run(
        "backend.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"), # Use 0.0.0.0 para ser acessível na rede
        port=int(os.getenv("API_PORT", 8010)), # Porta diferente da usada no deploy.sh?
        ssl_certfile=os.getenv("SSL_CERTFILE"),
        ssl_keyfile=os.getenv("SSL_KEYFILE"),
        reload=True # Adicionar reload para desenvolvimento é útil
    )

