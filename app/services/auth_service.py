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

def cleanup_expired_sessions():
    """Remove sessões expiradas do banco"""
    try:
        db.execute_non_query(
            "DELETE FROM admin_sessions WHERE expires_at <= GETDATE()"
        )
    except Exception as e:
        logger.error("Erro ao limpar sessões expiradas: %s", str(e))

def validate_session(token: str) -> Optional[Dict[str, Any]]:
    """Valida um token de sessão"""
    if not token:
        logger.warning("Token vazio recebido para validação")
        return None
        
    try:
        # Primeiro, verifica se a sessão está no cache local
        if token in active_sessions and active_sessions[token]["expires_at"] > datetime.now():
            logger.info(f"Sessão válida encontrada no cache para usuário: {active_sessions[token]['username']}")
            return {
                "user_id": active_sessions[token]["user_id"],
                "username": active_sessions[token]["username"],
                "role": active_sessions[token]["role"],
                "session_token": token
            }
            
        # Adicionar log para depuração
        logger.debug(f"Validando token de sessão: {token[:10]}...")
        
        query = """
            SELECT au.id, au.username, au.role, s.expires_at, s.token
            FROM admin_sessions s
            JOIN admin_users au ON s.user_id = au.id
            WHERE s.token = ?
              AND s.expires_at > GETDATE()
              AND au.is_active = 1
        """
        
        result = db.execute_query(query, (token,))
        
        if result and len(result) > 0:
            # Armazenar a sessão no cache
            active_sessions[token] = {
                "user_id": result[0]["id"],
                "username": result[0]["username"],
                "role": result[0]["role"],
                "expires_at": result[0]["expires_at"]
            }
            
            session_data = {
                "user_id": result[0]["id"],
                "username": result[0]["username"],
                "role": result[0]["role"],
                "session_token": result[0]["token"]
            }
            logger.info(f"Sessão válida encontrada no banco para usuário: {result[0]['username']}")
            return session_data
            
        logger.warning(f"Sessão inválida ou expirada - token: {token[:10]}...")
        return None
        
    except Exception as e:
        logger.error(f"Erro ao validar sessão: {str(e)}")
        return None

def invalidate_session(token: str) -> bool:
    """Invalida uma sessão (logout)"""
    try:
        db.execute_non_query(
            "DELETE FROM admin_sessions WHERE token = ?",
            (token,)
        )
        return True
    except Exception as e:
        logger.error("Erro ao invalidar sessão: %s", str(e))
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
