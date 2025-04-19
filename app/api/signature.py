"""
Rotas da API para assinaturas
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List

from ..services import signature_service
from ..models.signature import (
    SignatureTemplate, 
    TemplateCreateRequest, 
    TemplateUpdateRequest,
    SignatureAssignRequest
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/signature", response_model=str)
async def get_signature(email: str = Query(...)):
    """
    Obtém a assinatura HTML para um determinado e-mail.
    
    Args:
        email: E-mail do usuário
        
    Returns:
        HTML da assinatura renderizada
    """
    try:
        signature_html = signature_service.get_rendered_signature(email)
        
        if signature_html:
            return signature_html
        else:
            # Retorna um HTML padrão se não houver assinatura
            return """
            <html>
            <body>
            <p>Assinatura não configurada para este usuário.</p>
            </body>
            </html>
            """
    except Exception as e:
        logger.error(f"Erro ao obter assinatura para {email}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter assinatura: {str(e)}"
        )

@router.get("/templates", response_model=List[SignatureTemplate])
async def get_templates():
    """
    Obtém todos os templates de assinatura.
    
    Returns:
        Lista de templates
    """
    try:
        templates = signature_service.get_all_templates()
        return templates
    except Exception as e:
        logger.error(f"Erro ao obter templates: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter templates: {str(e)}"
        )

@router.post("/templates", response_model=int)
async def create_template(template: TemplateCreateRequest):
    """
    Cria um novo template de assinatura.
    
    Args:
        template: Dados do novo template
        
    Returns:
        ID do template criado
    """
    try:
        template_id = signature_service.save_signature_template(
            name=template.name,
            html=template.template_html,
            is_default=template.is_default
        )
        
        return template_id
    except Exception as e:
        logger.error(f"Erro ao criar template: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar template: {str(e)}"
        )

@router.put("/templates/{template_id}", response_model=bool)
async def update_template(template_id: int, template: TemplateUpdateRequest):
    """
    Atualiza um template de assinatura existente.
    
    Args:
        template_id: ID do template
        template: Dados do template atualizados
        
    Returns:
        True se bem sucedido
    """
    try:
        # Obtém o template atual
        templates = signature_service.get_all_templates()
        current_template = next((t for t in templates if t["id"] == template_id), None)
        
        if not current_template:
            raise HTTPException(
                status_code=404,
                detail=f"Template ID {template_id} não encontrado"
            )
        
        # Atualiza o template com os novos valores
        signature_service.save_signature_template(
            name=template.name if template.name is not None else current_template["name"],
            html=template.template_html if template.template_html is not None else current_template["template_html"],
            is_default=template.is_default if template.is_default is not None else current_template["is_default"]
        )
        
        return True
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar template {template_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao atualizar template: {str(e)}"
        )

@router.post("/assign", response_model=bool)
async def assign_signature(assignment: SignatureAssignRequest):
    """
    Atribui uma assinatura a um usuário.
    
    Args:
        assignment: Dados da atribuição
        
    Returns:
        True se bem sucedido
    """
    try:
        result = signature_service.assign_signature_to_user(
            user_email=assignment.user_email,
            template_id=assignment.template_id,
            custom_html=assignment.custom_html
        )
        
        if result:
            return True
        else:
            raise HTTPException(
                status_code=400,
                detail="Não foi possível atribuir a assinatura ao usuário"
            )
    except Exception as e:
        logger.error(f"Erro ao atribuir assinatura: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao atribuir assinatura: {str(e)}"
        )

@router.get("/preview", response_model=str)
async def preview_signature(template_id: int, email: str = Query(...)):
    """
    Obtém um preview da assinatura de um usuário.
    
    Args:
        template_id: ID do template
        email: E-mail do usuário
        
    Returns:
        HTML da assinatura renderizada
    """
    try:
        # Obtém o template
        templates = signature_service.get_all_templates()
        template = next((t for t in templates if t["id"] == template_id), None)
        
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template ID {template_id} não encontrado"
            )
        
        # Obtém os dados do usuário
        user_data = signature_service.get_user_data(email)
        
        if not user_data:
            raise HTTPException(
                status_code=404,
                detail=f"Usuário não encontrado para o e-mail: {email}"
            )
        
        # Renderiza a assinatura
        signature_html = signature_service.render_signature(template["template_html"], user_data)
        
        return signature_html
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar preview de assinatura: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar preview de assinatura: {str(e)}"
        )
