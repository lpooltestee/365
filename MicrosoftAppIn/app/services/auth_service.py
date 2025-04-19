"""
Serviço para autenticação da área administrativa
"""
import logging
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from .. import db
from ..config import AUTH_ENABLED

logger = logging.getLogger(__name__)

# Dicionário para armazenar sessões ativas
# Na produção, seria melhor usar Redis ou outra solução de cache
active_sessions = {}

def authenticate_user(username: str, password: str) -> Optional[str]:
    """
    Autentica um usuário administrativo.
    
    Args:
        username: Nome de usuário
        password: Senha
        
    Returns:
        Token de sessão ou None se a autenticação falhar
    """
    if not AUTH_ENABLED:
        # Se a autenticação estiver desabilitada, retorna um token fixo
        return "admin_no_auth"
    
    try:
        # Hash da senha para comparação com o banco
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Consulta o usuário no banco
        query = """
        SELECT id, username, role FROM [dbo].[admin_users]
        WHERE username = ? AND password_hash = ? AND is_active = 1
        """
        
        results = db.execute_query(query, (username, hashed_password))
        
        if results and len(results) > 0:
            # Gera um token de sessão
            session_token = secrets.token_urlsafe(32)
            
            # Armazena a sessão
            active_sessions[session_token] = {
                "user_id": results[0]["id"],
                "username": results[0]["username"],
                "role": results[0]["role"],
                "expires_at": datetime.now() + timedelta(hours=24)
            }
            
            return session_token
        else:
            logger.warning(f"Tentativa de login falhou para usuário: {username}")
            return None
    except Exception as e:
        logger.error(f"Erro durante autenticação para usuário {username}: {str(e)}")
        return None

def validate_session(session_token: str) -> Optional[Dict[str, Any]]:
    """
    Valida um token de sessão.
    
    Args:
        session_token: Token de sessão
        
    Returns:
        Informações da sessão ou None se o token for inválido
    """
    if not AUTH_ENABLED:
        # Se a autenticação estiver desabilitada, retorna uma sessão fixa
        return {
            "user_id": 0,
            "username": "admin",
            "role": "admin",
            "expires_at": datetime.now() + timedelta(hours=24)
        }
    
    # Verifica se o token existe
    if session_token not in active_sessions:
        return None
    
    session = active_sessions[session_token]
    
    # Verifica se a sessão expirou
    if session["expires_at"] < datetime.now():
        # Remove a sessão expirada
        del active_sessions[session_token]
        return None
    
    return session

def invalidate_session(session_token: str) -> bool:
    """
    Invalida um token de sessão (logout).
    
    Args:
        session_token: Token de sessão
        
    Returns:
        True se bem sucedido, False caso contrário
    """
    if not AUTH_ENABLED:
        return True
    
    if session_token in active_sessions:
        del active_sessions[session_token]
        return True
    
    return False

def create_admin_user(username: str, password: str, role: str = "admin") -> bool:
    """
    Cria um novo usuário administrativo.
    
    Args:
        username: Nome de usuário
        password: Senha
        role: Papel do usuário (admin, editor, etc.)
        
    Returns:
        True se bem sucedido, False caso contrário
    """
    try:
        # Hash da senha
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Verifica se o usuário já existe
        existing = db.execute_query("""
        SELECT id FROM [dbo].[admin_users]
        WHERE username = ?
        """, (username,))
        
        if existing and len(existing) > 0:
            logger.warning(f"Usuário administrativo já existe: {username}")
            return False
        
        # Insere o novo usuário
        db.execute_non_query("""
        INSERT INTO [dbo].[admin_users] (username, password_hash, role, is_active, created_at, updated_at)
        VALUES (?, ?, ?, 1, GETDATE(), GETDATE())
        """, (username, hashed_password, role))
        
        logger.info(f"Usuário administrativo criado: {username}")
        return True
    except Exception as e:
        logger.error(f"Erro ao criar usuário administrativo {username}: {str(e)}")
        return False

def cleanup_sessions() -> int:
    """
    Limpa sessões expiradas.
    
    Returns:
        Número de sessões removidas
    """
    if not AUTH_ENABLED:
        return 0
    
    count = 0
    # Lista para armazenar tokens a serem removidos
    to_remove = []
    
    # Identifica sessões expiradas
    for token, session in active_sessions.items():
        if session["expires_at"] < datetime.now():
            to_remove.append(token)
    
    # Remove sessões expiradas
    for token in to_remove:
        del active_sessions[token]
        count += 1
    
    return count
