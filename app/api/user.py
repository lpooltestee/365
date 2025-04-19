"""
Modelos de dados para usuários
"""
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class User(BaseModel):
    """Modelo para usuário"""
    id: Optional[int] = None
    email: EmailStr
    nome_completo: str
    cargo: Optional[str] = None
    setor: Optional[str] = None
    empresa: Optional[str] = None
    telefone: Optional[str] = None
    ramal: Optional[str] = None
    ms_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AdminUser(BaseModel):
    """Modelo para usuário administrativo"""
    id: Optional[int] = None
    username: str
    password_hash: Optional[str] = None
    role: str = "admin"
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserUpdateRequest(BaseModel):
    """Modelo para requisição de atualização de usuário"""
    nome_completo: Optional[str] = None
    cargo: Optional[str] = None
    setor: Optional[str] = None
    empresa: Optional[str] = None
    telefone: Optional[str] = None
    ramal: Optional[str] = None


class LoginRequest(BaseModel):
    """Modelo para requisição de login"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Modelo para resposta de login"""
    token: str
    username: str
    role: str
