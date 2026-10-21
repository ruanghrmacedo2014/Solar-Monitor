from getpass import getpass

from app.api.database import SessionLocal
from app.core.security.password import hash_password
from app.models.user import GlobalRole
from app.services.user_service import get_user_by_email


email = input("E-mail do usuário: ").strip().lower()
password = getpass("Nova senha do PLATFORM_ADMIN: ")

db = SessionLocal()

try:
    user = get_user_by_email(
        db=db,
        email=email,
    )

    if user is None:
        print("Usuário não encontrado.")
        raise SystemExit(1)

    user.password_hash = hash_password(password)
    user.global_role = GlobalRole.PLATFORM_ADMIN

    db.commit()
    db.refresh(user)

    print()
    print("Usuário promovido para PLATFORM_ADMIN com sucesso.")
    print(f"ID: {user.id}")
    print(f"Nome: {user.name}")
    print(f"E-mail: {user.email}")
finally:
    db.close()