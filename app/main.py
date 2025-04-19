"""
Arquivo principal da aplicação FastAPI
"""
import logging
from fastapi import FastAPI, Request, Response, Cookie
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi import FastAPI, Form
from pathlib import Path
from .api import signature, admin
from . import db  # Certifique-se de importar seu módulo de acesso ao banco
import hashlib
from datetime import datetime

from .api import signature, admin
from .config import BASE_URL
from .services import auth_service

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

def is_authenticated(request: Request) -> bool:
    session_token = request.cookies.get("session_token")
    
    # Log detalhado da verificação
    if session_token:
        logger.debug(f"Verificando autenticação para {request.url.path}, token encontrado: {session_token[:10]}...")
    else:
        logger.warning(f"Verificando autenticação para {request.url.path}, token não encontrado")
        return False
    
    try:    
        session = auth_service.validate_session(session_token)
        if session:
            logger.info(f"Sessão válida para usuário: {session.get('username')}, rota: {request.url.path}")
            return True
        
        logger.warning(f"Sessão inválida ou expirada para rota: {request.url.path}")
        return False
    except Exception as e:
        logger.error(f"Erro ao validar autenticação: {str(e)}")
        return False

# Adicionar middleware de autenticação para rotas da API admin
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Middleware para verificar autenticação nas rotas admin"""
    if request.url.path.startswith("/api/admin/"):
        # Excluir a rota de login da verificação
        if request.url.path != "/api/admin/login":
            session_token = request.cookies.get("session_token")
            logger.debug(f"Token recebido: {session_token[:10] if session_token else None}")
            
            if not session_token:
                logger.warning("Token não encontrado no request")
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Não autenticado"}
                )
                
            session = auth_service.validate_session(session_token)
            if not session:
                logger.warning(f"Sessão inválida para token: {session_token[:10] if session_token else None}")
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Sessão inválida ou expirada"}
                )
            
            # Adicionar informações da sessão ao request
            request.state.user = session

    response = await call_next(request)
    return response

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
    session_token = request.cookies.get("session_token")
    logger.debug(f"Verificando auth para /admin, token: {session_token[:10] if session_token else None}")
    
    if not is_authenticated(request):
        logger.warning("Não autenticado, redirecionando para /admin/login")
        return RedirectResponse(url="/admin/login", status_code=303)
    
    logger.info("Usuário autenticado, carregando página admin")
    return templates.TemplateResponse("admin/index.html", {"request": request, "base_url": BASE_URL})

@app.get("/admin/login")
async def admin_login_get(request: Request):
    """
    Exibe o formulário de login da área administrativa.
    """
    return templates.TemplateResponse("admin/login.html", {"request": request, "base_url": BASE_URL})

# Remova ou comente o endpoint abaixo:
# @app.post("/admin/login")
# async def admin_login_post(request: Request, username: str = Form(...), password: str = Form(...)):
#     """
#     Processa o login da área administrativa.
#     """
#     # Não é mais necessário, pois o login é feito via AJAX em /api/admin/login
#     return RedirectResponse(url="/admin/login", status_code=303)

@app.get("/admin/users")
async def admin_users(request: Request):
    """Página de gerenciamento de usuários"""
    if not is_authenticated(request):
        logger.warning("Acesso não autorizado a /admin/users")
        return RedirectResponse(url="/admin/login", status_code=303)
        
    return templates.TemplateResponse(
        "admin/users.html", 
        {"request": request, "base_url": BASE_URL}
    )

@app.get("/admin/signatures")
async def admin_signatures(request: Request):
    """
    Página de gerenciamento de templates de assinatura.
    """
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=303)
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

# Rota de debug para cookies
@app.get("/debug/cookies")
async def debug_cookies(request: Request):
    """
    Rota para depuração de cookies.
    """
    cookies = request.cookies
    session_valid = False
    
    if "session_token" in cookies:
        session = auth_service.validate_session(cookies["session_token"])
        session_valid = session is not None
    
    return {
        "cookies": {k: v[:10] + "..." if k == "session_token" and v else v for k, v in cookies.items()},
        "session_valid": session_valid,
        "request_headers": dict(request.headers)
    }

# Rota de diagnóstico para autenticação
@app.get("/debug/auth")
async def debug_auth(request: Request):
    """
    Rota para diagnóstico do sistema de autenticação.
    """
    # Verificar cookies
    cookies = request.cookies
    session_token = cookies.get("session_token")
    session_check = cookies.get("session_check")
    
    # Informações sobre a sessão
    session_info = None
    session_error = None
    if session_token:
        try:
            session = auth_service.validate_session(session_token)
            if session:
                session_info = {
                    "user_id": session.get("user_id"),
                    "username": session.get("username"),
                    "role": session.get("role")
                }
        except Exception as e:
            session_error = str(e)
    
    # Verificar sessões ativas no serviço de autenticação
    active_sessions_count = len(auth_service.active_sessions) if hasattr(auth_service, 'active_sessions') else 0
    
    return {
        "timestamp": datetime.now().isoformat(),
        "cookies": {
            "session_token_exists": session_token is not None,
            "session_token_truncated": session_token[:10] + "..." if session_token else None,
            "session_check_exists": session_check is not None
        },
        "session": {
            "valid": session_info is not None,
            "info": session_info,
            "error": session_error
        },
        "auth_service": {
            "active_sessions_count": active_sessions_count
        },
        "request": {
            "path": request.url.path,
            "method": request.method,
            "host": request.client.host
        }
    }