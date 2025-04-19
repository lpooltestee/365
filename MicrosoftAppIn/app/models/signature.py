"""
Modelos de dados para assinaturas
"""
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class SignatureTemplate(BaseModel):
    """Modelo para template de assinatura"""
    id: Optional[int] = None
    name: str
    template_html: str
    is_default: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SignatureAssignment(BaseModel):
    """Modelo para atribuição de assinatura a um usuário"""
    id: Optional[int] = None
    user_email: EmailStr
    signature_html: str
    template_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SignatureVariables(BaseModel):
    """Modelo para as variáveis disponíveis em um template de assinatura"""
    nome_completo: Optional[str] = Field(None, title="Nome Completo")
    cargo: Optional[str] = Field(None, title="Cargo")
    setor: Optional[str] = Field(None, title="Setor")
    empresa: Optional[str] = Field(None, title="Empresa")
    telefone: Optional[str] = Field(None, title="Telefone")
    ramal: Optional[str] = Field(None, title="Ramal")


class TemplateCreateRequest(BaseModel):
    """Modelo para requisição de criação de template"""
    name: str
    template_html: str
    is_default: bool = False


class TemplateUpdateRequest(BaseModel):
    """Modelo para requisição de atualização de template"""
    name: Optional[str] = None
    template_html: Optional[str] = None
    is_default: Optional[bool] = None


class SignatureAssignRequest(BaseModel):
    """Modelo para requisição de atribuição de assinatura"""
    user_email: EmailStr
    template_id: int
    custom_html: Optional[str] = None


class SignaturePreviewRequest(BaseModel):
    """Modelo para requisição de preview de assinatura"""
    template_id: int
    variables: SignatureVariables
