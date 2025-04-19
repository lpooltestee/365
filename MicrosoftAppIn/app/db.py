"""
Módulo para conexão com o banco de dados SQL Server
"""
import logging
import pyodbc
from contextlib import contextmanager
from typing import Optional, Dict, List, Any

from .config import DB_CONNECTION_STRING

# Configuração de logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='addin_db.log'
)
logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    """
    Gerenciador de contexto para conexão com o banco de dados.
    Garante que a conexão seja fechada após o uso, mesmo em caso de erro.
    """
    conn = None
    try:
        conn = pyodbc.connect(DB_CONNECTION_STRING)
        yield conn
    except pyodbc.Error as e:
        logger.error(f"Erro ao conectar ao banco de dados: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

def execute_query(query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    """
    Executa uma consulta SQL e retorna os resultados como uma lista de dicionários.
    
    Args:
        query: Consulta SQL a ser executada
        params: Parâmetros para a consulta (opcional)
        
    Returns:
        Lista de dicionários com os resultados da consulta
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            # Se a consulta possui resultados
            if cursor.description:
                # Obter nomes das colunas
                columns = [column[0] for column in cursor.description]
                
                # Converter os resultados em lista de dicionários
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                
                return results
            else:
                conn.commit()
                return []
    except pyodbc.Error as e:
        logger.error(f"Erro na execução da consulta: {str(e)}")
        logger.error(f"Query: {query}")
        if params:
            logger.error(f"Params: {params}")
        raise

def execute_non_query(query: str, params: Optional[tuple] = None) -> int:
    """
    Executa uma instrução SQL que não retorna resultados (INSERT, UPDATE, DELETE).
    
    Args:
        query: Instrução SQL a ser executada
        params: Parâmetros para a instrução (opcional)
        
    Returns:
        Número de linhas afetadas
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            conn.commit()
            return cursor.rowcount
    except pyodbc.Error as e:
        logger.error(f"Erro na execução da instrução: {str(e)}")
        logger.error(f"Query: {query}")
        if params:
            logger.error(f"Params: {params}")
        raise
