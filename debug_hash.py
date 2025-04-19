import hashlib
from app import db

def generate_hash(password: str) -> str:
    """Gera hash SHA-256 da senha"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def check_stored_hash():
    """Verifica o hash armazenado no banco"""
    query = "SELECT username, password_hash FROM admin_users WHERE username = 'admin'"
    result = db.execute_query(query)
    if result:
        print(f"Hash armazenado: {result[0]['password_hash']}")
    else:
        print("Usuário admin não encontrado")

if __name__ == "__main__":
    password = 'admin123'
    hash_value = generate_hash(password)
    print(f"Senha: {password}")
    print(f"Hash gerado: {hash_value}")
    print("\nVerificando hash no banco:")
    check_stored_hash()
