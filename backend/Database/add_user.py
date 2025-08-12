import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.Database.database import SessionLocal, User
from backend.Database.auth import get_password_hash
# Crée une nouvelle session
db = SessionLocal()

# Crée un nouvel utilisateur
new_user = User(
    name="New User Name",
    email="newuser@example.com",
    password_hash=get_password_hash("securepassword123")
)

# Ajoute et commit
db.add(new_user)
db.commit()

# Ferme la session
db.close()

print("✅ Nouvel utilisateur ajouté à la base de données.")