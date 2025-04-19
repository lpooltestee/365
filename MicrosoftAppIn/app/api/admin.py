"""
Rotas da API para administração
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, Header, Cookie, Request, Response
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any

from ..services import auth_service, ms_graph_service
from ..models.user import User, AdminUser, LoginRequest, LoginResponse, UserUpdateRequest
from .. import db

logger = logging.getLogger(__name__)

router = APIRouter()
graph_service = ms_graph_service.MSGraphService()

def get_current_user(session_token: Optional[str] = Cookie(None)):
    """
    Obtém o usuário atual a partir do token de sessão.
    
    Args:
        session_token: Token de sessão (cookie)
        
    Returns:
        Informações do usuário
    """
    if not session_token:
        raise HTTPException(
            status_code=401,
            detail="Não autenticado"
        )
    
    session = auth_service.validate_session(session_token)
    if not session:
        raise HTTPException(
            status_code=401,
            detail="Sessão inválida ou expirada"
        )
    
    return session

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, response: Response):
    """
    Realiza o login administrativo.
    
    Args:
        request: Dados de login
        
    Returns:
        Token de sessão e informações do usuário
    """
    try:
        token = auth_service.authenticate_user(request.username, request.password)
        
        if token:
            # Define o cookie de sessão
            response.set_cookie(
                key="session_token",
                value=token,
                httponly=True,
                max_age=86400,  # 24 horas
                samesite="lax"
            )
            
            # Obtém a sessão do usuário
            session = auth_service.validate_session(token)
            
            return LoginResponse(
                token=token,
                username=session["username"],
                role=session["role"]
            )
        else:
            raise HTTPException(
                status_code=401,
                detail="Usuário ou senha inválidos"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro durante login: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro durante login: {str(e)}"
        )

@router.post("/logout")
async def logout(response: Response, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Realiza o logout.
    
    Args:
        response: Objeto de resposta
        current_user: Usuário atual
        
    Returns:
        Mensagem de sucesso
    """
    try:
        # Remove o cookie de sessão
        response.delete_cookie(key="session_token")
        
        # Invalida a sessão
        auth_service.invalidate_session(current_user.get("session_token", ""))
        
        return {"message": "Logout realizado com sucesso"}
    except Exception as e:
        logger.error(f"Erro durante logout: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro durante logout: {str(e)}"
        )

@router.get("/users", response_model=List[User])
async def get_users(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Obtém a lista de usuários.
    
    Args:
        current_user: Usuário atual
        
    Returns:
        Lista de usuários
    """
    try:
        # Consulta os usuários no banco
        query = """
        SELECT * FROM [dbo].[users]
        ORDER BY nome_completo
        """
        
        users = db.execute_query(query)
        return users
    except Exception as e:
        logger.error(f"Erro ao obter usuários: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter usuários: {str(e)}"
        )

@router.get("/users/{email}", response_model=User)
async def get_user(email: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Obtém informações de um usuário pelo e-mail.
    
    Args:
        email: E-mail do usuário
        current_user: Usuário atual
        
    Returns:
        Informações do usuário
    """
    try:
        # Consulta o usuário no banco
        query = """
        SELECT * FROM [dbo].[users]
        WHERE email = ?
        """
        
        results = db.execute_query(query, (email,))
        
        if results and len(results) > 0:
            return results[0]
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Usuário não encontrado para o e-mail: {email}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter usuário {email}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter usuário: {str(e)}"
        )

@router.put("/users/{email}", response_model=bool)
async def update_user(
    email: str, 
    user: UserUpdateRequest, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Atualiza as informações de um usuário.
    
    Args:
        email: E-mail do usuário
        user: Dados atualizados
        current_user: Usuário atual
        
    Returns:
        True se bem sucedido
    """
    try:
        # Verifica se o usuário existe
        query = """
        SELECT id FROM [dbo].[users]
        WHERE email = ?
        """
        
        results = db.execute_query(query, (email,))
        
        if not results or len(results) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Usuário não encontrado para o e-mail: {email}"
            )
        
        # Prepara os dados para atualização
        update_fields = []
        params = []
        
        if user.nome_completo is not None:
            update_fields.append("nome_completo = ?")
            params.append(user.nome_completo)
        
        if user.cargo is not None:
            update_fields.append("cargo = ?")
            params.append(user.cargo)
        
        if user.setor is not None:
            update_fields.append("setor = ?")
            params.append(user.setor)
        
        if user.empresa is not None:
            update_fields.append("empresa = ?")
            params.append(user.empresa)
        
        if user.telefone is not None:
            update_fields.append("telefone = ?")
            params.append(user.telefone)
        
        if user.ramal is not None:
            update_fields.append("ramal = ?")
            params.append(user.ramal)
        
        # Adiciona o e-mail aos parâmetros
        params.append(email)
        
        # Atualiza o usuário
        query = f"""
        UPDATE [dbo].[users]
        SET {", ".join(update_fields)}, updated_at = GETDATE()
        WHERE email = ?
        """
        
        db.execute_non_query(query, tuple(params))
        
        return True
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar usuário {email}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao atualizar usuário: {str(e)}"
        )

@router.post("/sync-users", response_model=Dict[str, Any])
async def sync_users(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Sincroniza os usuários com o Microsoft 365.
    
    Args:
        current_user: Usuário atual
        
    Returns:
        Mensagem de sucesso e informações de sincronização
    """
    try:
        # Executa a sincronização
        result = graph_service.sync_users()
        
        if result:
            return {"success": True, "message": "Usuários sincronizados com sucesso"}
        else:
            return {"success": False, "message": "Falha na sincronização de usuários"}
    except Exception as e:
        logger.error(f"Erro ao sincronizar usuários: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao sincronizar usuários: {str(e)}"
        )

@router.post("/sync-user/{email}", response_model=Dict[str, Any])
async def sync_single_user(
    email: str, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Sincroniza um único usuário com o Microsoft 365.
    
    Args:
        email: E-mail do usuário
        current_user: Usuário atual
        
    Returns:
        Mensagem de sucesso e informações de sincronização
    """
    try:
        # Obtém os dados do usuário no Microsoft 365
        ms_user = graph_service.get_user_by_email(email)
        
        if not ms_user:
            raise HTTPException(
                status_code=404,
                detail=f"Usuário não encontrado no Microsoft 365: {email}"
            )
        
        # Verifica se o usuário já existe no banco
        existing = db.execute_query("""
        SELECT id FROM [dbo].[users]
        WHERE email = ?
        """, (email,))
        
        # Prepara os dados do usuário
        user_data = {
            "email": ms_user.get("mail"),
            "nome_completo": ms_user.get("displayName", ""),
            "cargo": ms_user.get("jobTitle", ""),
            "setor": ms_user.get("department", ""),
            "empresa": ms_user.get("companyName", ""),
            "telefone": ms_user.get("businessPhones")[0] if ms_user.get("businessPhones") and len(ms_user.get("businessPhones")) > 0 else "",
            "ramal": "",  # O Microsoft Graph não fornece ramal diretamente
            "ms_id": ms_user.get("id", "")
        }
        
        if existing and len(existing) > 0:
            # Atualiza o usuário existente
            db.execute_non_query("""
            UPDATE [dbo].[users]
            SET nome_completo = ?, cargo = ?, setor = ?, empresa = ?, telefone = ?, ms_id = ?, updated_at = GETDATE()
            WHERE email = ?
            """, (
                user_data["nome_completo"], 
                user_data["cargo"], 
                user_data["setor"], 
                user_data["empresa"], 
                user_data["telefone"], 
                user_data["ms_id"],
                user_data["email"]
            ))
        else:
            # Insere novo usuário
            db.execute_non_query("""
            INSERT INTO [dbo].[users] (email, nome_completo, cargo, setor, empresa, telefone, ramal, ms_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
            """, (
                user_data["email"], 
                user_data["nome_completo"], 
                user_data["cargo"], 
                user_data["setor"], 
                user_data["empresa"], 
                user_data["telefone"], 
                user_data["ramal"],
                user_data["ms_id"]
            ))
        
        return {
            "success": True, 
            "message": f"Usuário {email} sincronizado com sucesso",
            "user_data": user_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao sincronizar usuário {email}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao sincronizar usuário: {str(e)}"
        )

@router.get("/admin-users", response_model=List[AdminUser])
async def get_admin_users(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Obtém a lista de usuários administrativos.
    
    Args:
        current_user: Usuário atual
        
    Returns:
        Lista de usuários administrativos
    """
    try:
        # Verifica se o usuário atual tem permissão (deve ser admin)
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="Permissão negada"
            )
        
        # Consulta os usuários administrativos no banco
        query = """
        SELECT id, username, role, is_active, created_at, updated_at FROM [dbo].[admin_users]
        ORDER BY username
        """
        
        admin_users = db.execute_query(query)
        return admin_users
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter usuários administrativos: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter usuários administrativos: {str(e)}"
        )

@router.post("/admin-users", response_model=bool)
async def create_admin_user(
    admin_user: AdminUser,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Cria um novo usuário administrativo.
    
    Args:
        admin_user: Dados do usuário administrativo
        current_user: Usuário atual
        
    Returns:
        True se bem sucedido
    """
    try:
        # Verifica se o usuário atual tem permissão (deve ser admin)
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="Permissão negada"
            )
        
        # Valida os dados do usuário
        if not admin_user.username or not admin_user.password_hash:
            raise HTTPException(
                status_code=400,
                detail="Username e senha são obrigatórios"
            )
        
        # Cria o usuário administrativo
        result = auth_service.create_admin_user(
            username=admin_user.username,
            password=admin_user.password_hash,  # Será hash pelo serviço
            role=admin_user.role
        )
        
        if result:
            return True
        else:
            raise HTTPException(
                status_code=400,
                detail="Não foi possível criar o usuário administrativo"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar usuário administrativo: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar usuário administrativo: {str(e)}"
        )