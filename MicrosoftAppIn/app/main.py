"""
Arquivo principal da aplicação FastAPI
"""
import logging
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi import Form
from pathlib import Path
from fastapi.responses import RedirectResponse
from .api import signature, admin

from .api import signature, admin
from .config import BASE_URL

# Configuração de logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='addin.log'
)
logger = logging.getLogger(__name__)

# Cria a aplicação FastAPI
app = FastAPI(title="Outlook Signature Add-in")

# Configura o CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Para produção, especificar origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configura arquivos estáticos
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

# Configura os templates
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# Registra as rotas da API
app.include_router(signature.router, prefix="/api", tags=["signature"])
app.include_router(signature.router, prefix="/api/signatures", tags=["signatures"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

@app.get("/")
async def root(request: Request):
    """
    Página inicial da aplicação.
    """
    return templates.TemplateResponse("index.html", {"request": request, "base_url": BASE_URL})

@app.get("/addin")
async def addin(request: Request):
    """
    Página principal do Add-in do Outlook.
    """
    return templates.TemplateResponse("addin/index.html", {"request": request, "base_url": BASE_URL})

@app.get("/admin")
async def admin_panel(request: Request):
    """
    Página principal da área administrativa.
    """
    return templates.TemplateResponse("admin/index.html", {"request": request, "base_url": BASE_URL})

@app.get("/admin/login")
async def admin_login_get(request: Request):
    """
    Exibe o formulário de login da área administrativa.
    """
    return templates.TemplateResponse("admin/login.html", {"request": request, "base_url": BASE_URL})

@app.post("/admin/login")
async def admin_login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    """
    Processa o login da área administrativa.
    """
    # Exemplo de lógica de autenticação (substitua pela lógica real)
    if username == "admin" and password == "1234":  # Credenciais de exemplo
        # Redireciona para o painel administrativo após login bem-sucedido
        return RedirectResponse(url="/admin", status_code=302)
    return templates.TemplateResponse(
        "admin/login.html",
        {"request": request, "base_url": BASE_URL, "error": "Credenciais inválidas"}
    )

@app.get("/admin/users")
async def admin_users(request: Request):
    """
    Página de gerenciamento de usuários.
    """
    return templates.TemplateResponse("admin/users.html", {"request": request, "base_url": BASE_URL})

@app.get("/admin/signatures")
async def admin_signatures(request: Request):
    """
    Página de gerenciamento de templates de assinatura.
    """
    return templates.TemplateResponse("admin/signatures.html", {"request": request, "base_url": BASE_URL})

@app.get("/admin/editor")
async def admin_editor(request: Request):
    """
    Editor de assinaturas HTML.
    """
    return templates.TemplateResponse("admin/editor.html", {"request": request, "base_url": BASE_URL})

@app.get("/support")
async def support(request: Request):
    """
    Página de suporte.
    """
    return templates.TemplateResponse("support.html", {"request": request, "base_url": BASE_URL})

@app.get("/addin/index")
async def addin_index(request: Request):
    """
    Página principal do add-in.
    """
    return templates.TemplateResponse("addin/index.html", {"request": request, "base_url": BASE_URL})

@app.get("/addin/functions")
async def addin_functions(request: Request):
    """
    Página de funções do add-in.
    """
    return templates.TemplateResponse("addin/functions.html", {"request": request, "base_url": BASE_URL})

# Rota de verificação de saúde
@app.get("/health")
async def health_check():
    """
    Verificação de saúde da API.
    """
    return {"status": "ok"}