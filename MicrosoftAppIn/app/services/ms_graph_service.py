"""
Serviço para comunicação com a Microsoft Graph API
"""
import logging
import requests
import msal
from typing import Dict, Any, List, Optional

from ..config import TENANT_ID, CLIENT_ID, CLIENT_SECRET

logger = logging.getLogger(__name__)

class MSGraphService:
    """
    Classe para comunicação com a Microsoft Graph API
    """
    
    def __init__(self):
        self.tenant_id = TENANT_ID
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scope = ["https://graph.microsoft.com/.default"]
        self.endpoint = "https://graph.microsoft.com/v1.0"

    def _get_token(self) -> Optional[str]:
        """
        Obtém um token de acesso para a API do Microsoft Graph.
        
        Returns:
            Token de acesso ou None se ocorrer algum erro
        """
        try:
            # Criar uma aplicação confidencial
            app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=self.authority
            )
            
            # Adquirir token para a aplicação (não para um usuário)
            result = app.acquire_token_for_client(scopes=self.scope)
            
            if "access_token" in result:
                return result["access_token"]
            else:
                logger.error(f"Falha ao obter token: {result.get('error')}")
                logger.error(f"Descrição: {result.get('error_description')}")
                return None
        except Exception as e:
            logger.error(f"Erro ao obter token de acesso: {str(e)}")
            return None

    def _make_request(self, method: str, endpoint: str, data: Any = None) -> Optional[Dict[str, Any]]:
        """
        Faz uma requisição para a API do Microsoft Graph.
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            endpoint: Endpoint da API
            data: Dados a serem enviados (opcional)
            
        Returns:
            Resposta da API ou None se ocorrer algum erro
        """
        token = self._get_token()
        if not token:
            return None
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.endpoint}/{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == "PATCH":
                response = requests.patch(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                logger.error(f"Método HTTP não suportado: {method}")
                return None
            
            # Verificar se a resposta foi bem-sucedida
            response.raise_for_status()
            
            # Retornar os dados da resposta se houver
            if response.content:
                return response.json()
            else:
                return {}
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para {url}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Resposta: {e.response.text}")
            return None

    def get_users(self, filter_query: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtém a lista de usuários do Microsoft 365.
        
        Args:
            filter_query: Consulta de filtro (opcional)
            limit: Limite de resultados
            
        Returns:
            Lista de usuários
        """
        try:
            endpoint = "users"
            params = []
            
            if filter_query:
                params.append(f"$filter={filter_query}")
            
            params.append(f"$top={limit}")
            params.append("$select=id,displayName,mail,jobTitle,department,companyName,businessPhones")
            
            query_string = "&".join(params)
            endpoint = f"{endpoint}?{query_string}"
            
            response = self._make_request("GET", endpoint)
            
            if response and "value" in response:
                return response["value"]
            else:
                return []
        except Exception as e:
            logger.error(f"Erro ao obter usuários: {str(e)}")
            return []

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Obtém informações de um usuário pelo e-mail.
        
        Args:
            email: E-mail do usuário
            
        Returns:
            Informações do usuário ou None se não encontrado
        """
        try:
            # Usar um filtro para buscar pelo e-mail
            users = self.get_users(f"mail eq '{email}'", 1)
            
            if users and len(users) > 0:
                return users[0]
            else:
                logger.warning(f"Usuário não encontrado para o e-mail: {email}")
                return None
        except Exception as e:
            logger.error(f"Erro ao buscar usuário por e-mail {email}: {str(e)}")
            return None

    def sync_users(self) -> bool:
        """
        Sincroniza todos os usuários do Microsoft 365 com o banco de dados local.
        
        Returns:
            True se a sincronização foi bem-sucedida, False caso contrário
        """
        from .. import db
        
        try:
            # Obtém todos os usuários do Microsoft 365
            users = self.get_users(limit=1000)
            
            if not users:
                logger.warning("Nenhum usuário encontrado no Microsoft 365")
                return False
            
            # Contador de usuários sincronizados
            count = 0
            
            for user in users:
                # Só sincroniza usuários com e-mail
                if not user.get("mail"):
                    continue
                
                # Verifica se o usuário já existe no banco
                existing = db.execute_query("""
                SELECT id FROM [dbo].[users]
                WHERE email = ?
                """, (user.get("mail"),))
                
                # Prepara os dados do usuário
                user_data = {
                    "email": user.get("mail"),
                    "nome_completo": user.get("displayName", ""),
                    "cargo": user.get("jobTitle", ""),
                    "setor": user.get("department", ""),
                    "empresa": user.get("companyName", ""),
                    "telefone": user.get("businessPhones")[0] if user.get("businessPhones") and len(user.get("businessPhones")) > 0 else "",
                    "ramal": "",  # O Microsoft Graph não fornece ramal diretamente
                    "ms_id": user.get("id", "")
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
                
                count += 1
            
            logger.info(f"{count} usuários sincronizados com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao sincronizar usuários: {str(e)}")
            return False