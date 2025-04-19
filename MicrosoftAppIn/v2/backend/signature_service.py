import os
import pyodbc
import logging
from dotenv import load_dotenv

load_dotenv()

# 🔹 Carrega variáveis de ambiente
DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

CONN_STRING = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_SERVER};DATABASE={DB_NAME};UID={DB_USER};PWD={DB_PASSWORD}"

# 🔹 Configuração de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# 🔹 Conexão com o banco de dados
def get_db_connection():
    try:
        # Use a CONN_STRING que lê do .env
        conn = pyodbc.connect(CONN_STRING)
        logger.info("Conexão com o banco de dados estabelecida com sucesso.") # Log para confirmar
        return conn
    except pyodbc.Error as e:
        logger.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

# 🔹 Função para buscar assinatura (MODIFICADA)
def get_signature(email: str) -> str:
    conn = get_db_connection() # <-- USA A FUNÇÃO CORRETA AGORA
    if conn is None:
        # Se a conexão falhar (get_db_connection retornou None), retorne um erro
        return "<p>Erro: Falha ao conectar ao banco de dados.</p>"

    try:
        cursor = conn.cursor()
        logger.info(f"Executando query para o email: {email}") # Log para depuração
        cursor.execute("SELECT signature_html FROM [dbo].[signatures] WHERE user_email = ?", email)
        row = cursor.fetchone()
        signature = row.signature_html if row else "<p>Assinatura não encontrada.</p>"
        logger.info(f"Assinatura encontrada para {email}: {'Sim' if row else 'Não'}") # Log
        return signature
    except pyodbc.Error as e:
        # Loga o erro específico do pyodbc
        logger.error(f"Erro na query SQL para {email}: {e}")
        return f"<p>Erro ao executar a consulta no banco de dados: {e}</p>" # Retorna erro mais detalhado (opcional)
    finally:
        # Garante que a conexão seja fechada, mesmo se ocorrer um erro
        if conn:
            conn.close()
            logger.info("Conexão com o banco de dados fechada.") # Log
