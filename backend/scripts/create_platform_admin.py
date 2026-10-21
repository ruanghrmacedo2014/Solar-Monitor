from getpass import getpass

from app.api.database import SessionLocal
from app.core.security.password import hash_password
from app.models.user import GlobalRole, User
from app.services.user_service import get_user_by_email


name = input("Nome do PLATFORM_ADMIN: ").strip()
email = input("E-mail do PLATFORM_ADMIN: ").strip().lower()
password = getpass("Senha do PLATFORM_ADMIN: ")

db = SessionLocal()

try:
    existing_user = get_user_by_email(
        db=db,
        email=email,
    )

    if existing_user is not None:
        print("Já existe um usuário com esse e-mail.")
        raise SystemExit(1)

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        global_role=GlobalRole.PLATFORM_ADMIN,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    print()
    print("PLATFORM_ADMIN criado com sucesso.")
    print(f"ID: {user.id}")
    print(f"Nome: {user.name}")
    print(f"E-mail: {user.email}")
finally:
    db.close()