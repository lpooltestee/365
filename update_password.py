import hashlib
import pyodbc
from app.config import DB_CONNECTION_STRING

def update_admin_password():
    password = 'admin123'
    correct_hash = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        # Conecta diretamente ao banco
        conn = pyodbc.connect(DB_CONNECTION_STRING)
        cursor = conn.cursor()
        
        # Atualiza a senha
        cursor.execute(
            "UPDATE admin_users SET password_hash = ? WHERE username = 'admin'",
            (correct_hash,)
        )
        conn.commit()
        
        print(f"Senha do admin atualizada com sucesso!")
        print(f"Username: admin")
        print(f"Password: {password}")
        print(f"Hash: {correct_hash}")
        
    except Exception as e:
        print(f"Erro ao atualizar senha: {str(e)}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    update_admin_password()
