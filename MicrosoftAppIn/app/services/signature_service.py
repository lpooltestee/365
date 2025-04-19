"""
Serviço para gerenciar assinaturas de e-mail
"""
import logging
from typing import Dict, Any, Optional, List

from .. import db

logger = logging.getLogger(__name__)

def get_signature_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Obtém a assinatura HTML para um determinado e-mail.
    
    Args:
        email: E-mail do usuário
        
    Returns:
        Dicionário com informações da assinatura ou None se não encontrada
    """
    try:
        query = """
        SELECT * FROM [dbo].[signatures]
        WHERE user_email = ?
        """
        
        results = db.execute_query(query, (email,))
        
        if results and len(results) > 0:
            return results[0]
        else:
            logger.warning(f"Assinatura não encontrada para o e-mail: {email}")
            return None
    except Exception as e:
        logger.error(f"Erro ao buscar assinatura para o e-mail {email}: {str(e)}")
        return None

def get_user_data(email: str) -> Optional[Dict[str, Any]]:
    """
    Obtém os dados do usuário para popular a assinatura.
    
    Args:
        email: E-mail do usuário
        
    Returns:
        Dicionário com os dados do usuário ou None se não encontrado
    """
    try:
        query = """
        SELECT u.* 
        FROM [dbo].[users] u
        WHERE u.email = ?
        """
        
        results = db.execute_query(query, (email,))
        
        if results and len(results) > 0:
            return results[0]
        else:
            logger.warning(f"Dados do usuário não encontrados para o e-mail: {email}")
            return None
    except Exception as e:
        logger.error(f"Erro ao buscar dados do usuário para o e-mail {email}: {str(e)}")
        return None

def render_signature(template: str, user_data: Dict[str, Any]) -> str:
    """
    Renderiza a assinatura substituindo as variáveis pelo dados do usuário.
    
    Args:
        template: Template HTML da assinatura com variáveis como {{NomeCompleto}}
        user_data: Dicionário com os dados do usuário
        
    Returns:
        HTML da assinatura com as variáveis substituídas
    """
    # Começamos com o template
    rendered = template
    
    # Lista de variáveis possíveis e seus mapeamentos para as colunas do banco
    variable_mappings = {
        "{{NomeCompleto}}": user_data.get("nome_completo", ""),
        "{{Cargo}}": user_data.get("cargo", ""),
        "{{Setor}}": user_data.get("setor", ""),
        "{{Empresa}}": user_data.get("empresa", ""),
        "{{Telefone}}": user_data.get("telefone", ""),
        "{{Ramal}}": user_data.get("ramal", "")
    }
    
    # Substitui cada variável pelo valor correspondente
    for var, value in variable_mappings.items():
        rendered = rendered.replace(var, value)
    
    return rendered

def get_rendered_signature(email: str) -> Optional[str]:
    """
    Obtém a assinatura renderizada com os dados do usuário.
    
    Args:
        email: E-mail do usuário
        
    Returns:
        HTML da assinatura renderizada ou None se ocorrer algum erro
    """
    try:
        # Obtém a assinatura do banco
        signature_data = get_signature_by_email(email)
        if not signature_data:
            # Se não encontrar assinatura específica, busca o template padrão
            query = """
            SELECT * FROM [dbo].[signature_templates]
            WHERE is_default = 1
            """
            templates = db.execute_query(query)
            if not templates or len(templates) == 0:
                logger.error("Nenhum template padrão encontrado")
                return None
            
            template_html = templates[0]["template_html"]
        else:
            template_html = signature_data["signature_html"]
        
        # Obtém os dados do usuário
        user_data = get_user_data(email)
        if not user_data:
            logger.warning(f"Dados do usuário não encontrados para o e-mail: {email}")
            # Podemos retornar um template com dados vazios ou um fallback
            user_data = {
                "nome_completo": email.split('@')[0],
                "cargo": "",
                "setor": "",
                "empresa": email.split('@')[1],
                "telefone": "",
                "ramal": ""
            }
        
        # Renderiza a assinatura com os dados do usuário
        return render_signature(template_html, user_data)
    except Exception as e:
        logger.error(f"Erro ao gerar assinatura renderizada para {email}: {str(e)}")
        return None

def save_signature_template(name: str, html: str, is_default: bool = False) -> int:
    """
    Salva um template de assinatura no banco de dados.
    
    Args:
        name: Nome do template
        html: HTML do template
        is_default: Se é o template padrão
        
    Returns:
        ID do template salvo
    """
    try:
        # Se for padrão, remove o padrão atual
        if is_default:
            db.execute_non_query("""
            UPDATE [dbo].[signature_templates]
            SET is_default = 0
            WHERE is_default = 1
            """)
        
        # Verifica se o template já existe
        existing = db.execute_query("""
        SELECT id FROM [dbo].[signature_templates]
        WHERE name = ?
        """, (name,))
        
        if existing and len(existing) > 0:
            # Atualiza o template existente
            db.execute_non_query("""
            UPDATE [dbo].[signature_templates]
            SET template_html = ?, is_default = ?, updated_at = GETDATE()
            WHERE name = ?
            """, (html, 1 if is_default else 0, name))
            return existing[0]["id"]
        else:
            # Insere novo template
            db.execute_non_query("""
            INSERT INTO [dbo].[signature_templates] (name, template_html, is_default, created_at, updated_at)
            VALUES (?, ?, ?, GETDATE(), GETDATE())
            """, (name, html, 1 if is_default else 0))
            
            # Obtém o ID do template inserido
            result = db.execute_query("""
            SELECT id FROM [dbo].[signature_templates]
            WHERE name = ?
            """, (name,))
            
            return result[0]["id"]
    except Exception as e:
        logger.error(f"Erro ao salvar template de assinatura: {str(e)}")
        raise

def get_all_templates() -> List[Dict[str, Any]]:
    """
    Obtém todos os templates de assinatura.
    
    Returns:
        Lista de templates
    """
    try:
        return db.execute_query("""
        SELECT * FROM [dbo].[signature_templates]
        ORDER BY is_default DESC, name ASC
        """)
    except Exception as e:
        logger.error(f"Erro ao obter templates de assinatura: {str(e)}")
        return []

def assign_signature_to_user(user_email: str, template_id: int, custom_html: Optional[str] = None) -> bool:
    """
    Atribui uma assinatura a um usuário.
    
    Args:
        user_email: E-mail do usuário
        template_id: ID do template de assinatura
        custom_html: HTML personalizado (opcional)
        
    Returns:
        True se bem sucedido, False caso contrário
    """
    try:
        # Verifica se já existe uma assinatura para o usuário
        existing = db.execute_query("""
        SELECT id FROM [dbo].[signatures]
        WHERE user_email = ?
        """, (user_email,))
        
        if custom_html is None:
            # Obtém o HTML do template
            template = db.execute_query("""
            SELECT template_html FROM [dbo].[signature_templates]
            WHERE id = ?
            """, (template_id,))
            
            if not template or len(template) == 0:
                logger.error(f"Template ID {template_id} não encontrado")
                return False
            
            signature_html = template[0]["template_html"]
        else:
            signature_html = custom_html
        
        if existing and len(existing) > 0:
            # Atualiza a assinatura existente
            db.execute_non_query("""
            UPDATE [dbo].[signatures]
            SET signature_html = ?, template_id = ?, updated_at = GETDATE()
            WHERE user_email = ?
            """, (signature_html, template_id, user_email))
        else:
            # Insere nova assinatura
            db.execute_non_query("""
            INSERT INTO [dbo].[signatures] (user_email, signature_html, template_id, created_at, updated_at)
            VALUES (?, ?, ?, GETDATE(), GETDATE())
            """, (user_email, signature_html, template_id))
        
        return True
    except Exception as e:
        logger.error(f"Erro ao atribuir assinatura ao usuário {user_email}: {str(e)}")
        return False
