"""
Configurações da aplicação carregadas a partir do arquivo .env
"""
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações do Azure AD
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# Configurações do banco de dados
DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# String de conexão com o SQL Server
DB_CONNECTION_STRING = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_SERVER};DATABASE={DB_NAME};UID={DB_USER};PWD={DB_PASSWORD}"

# Configurações do servidor
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8010"))
SSL_CERTFILE = os.getenv("SSL_CERTFILE")
SSL_KEYFILE = os.getenv("SSL_KEYFILE")

# URL base para o Add-in
BASE_URL = "https://assinaturas.hoffmanndh.com"

# Configurações de autenticação
AUTH_ENABLED = True  # Define se a autenticação está habilitada
