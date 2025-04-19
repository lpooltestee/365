import sys
import os
import hashlib

# Adiciona o diretório raiz do projeto ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import db

def update_admin_password():
    password = 'admin123'
    correct_hash = hashlib.sha256(password.encode()).hexdigest()
    
    update_query = """
    UPDATE admin_users 
    SET password_hash = ? 
    WHERE username = 'admin'
    """
    
    try:
        db.execute_non_query(update_query, (correct_hash,))
        print(f"Senha do admin atualizada com sucesso!")
        print(f"Username: admin")
        print(f"Password: {password}")
        print(f"Hash: {correct_hash}")
    except Exception as e:
        print(f"Erro ao atualizar senha: {str(e)}")

if __name__ == "__main__":
    update_admin_password()
