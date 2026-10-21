import json
import hashlib
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.security.encryption import decrypt_value, encrypt_value
from app.models.tenant_integration import (
    SyncStatus,
    TenantIntegration,
)
from app.schemas.tenant_integration import SolarmanCredentialsUpdate
from app.services.integrations.solarman_client import SolarmanClient
from datetime import datetime, timedelta, timezone


def create_tenant_integration(
    db: Session,
    tenant_id: int,
    provider,
    name: str,
) -> TenantIntegration:
    integration = TenantIntegration(
        tenant_id=tenant_id,
        provider=provider,
        name=name.strip(),
    )

    db.add(integration)
    db.commit()
    db.refresh(integration)

    return integration


def get_tenant_integrations(
    db: Session,
    tenant_id: int,
) -> list[TenantIntegration]:
    statement = (
        select(TenantIntegration)
        .where(
            TenantIntegration.tenant_id == tenant_id,
        )
        .order_by(TenantIntegration.name)
    )

    return list(db.scalars(statement).all())


def get_tenant_integration_by_id(
    db: Session,
    tenant_id: int,
    integration_id: int,
) -> TenantIntegration | None:
    statement = (
        select(TenantIntegration)
        .where(
            TenantIntegration.id == integration_id,
            TenantIntegration.tenant_id == tenant_id,
        )
    )

    return db.scalar(statement)

def update_solarman_credentials(
    db: Session,
    tenant_id: int,
    integration_id: int,
    credentials: SolarmanCredentialsUpdate,
) -> TenantIntegration | None:
    integration = get_tenant_integration_by_id(
        db=db,
        tenant_id=tenant_id,
        integration_id=integration_id,
    )

    if integration is None:
        return None

    password_sha256 = hashlib.sha256(
    credentials.password.encode("utf-8")
    ).hexdigest()

    credentials_data = {
        "app_id": credentials.app_id,
        "app_secret": credentials.app_secret,
        "email": credentials.email,
        "password_sha256": password_sha256,
        "org_id": credentials.org_id,
        "language": credentials.language,
    }

    credentials_json = json.dumps(credentials_data)

    integration.credentials_encrypted = encrypt_value(credentials_json)

    db.commit()
    db.refresh(integration)

    return integration

def get_solarman_credentials(
    db: Session,
    tenant_id: int,
    integration_id: int,
) -> dict | None:
    integration = get_tenant_integration_by_id(
        db=db,
        tenant_id=tenant_id,
        integration_id=integration_id,
    )

    if integration is None:
        return None

    if not integration.credentials_encrypted:
        return None

    credentials_json = decrypt_value(
        integration.credentials_encrypted
    )

    return json.loads(credentials_json)

def get_solarman_client(
    db: Session,
    tenant_id: int,
    integration_id: int,
) -> SolarmanClient | None:
    credentials = get_solarman_credentials(
        db=db,
        tenant_id=tenant_id,
        integration_id=integration_id,
    )

    if credentials is None:
        return None

    return SolarmanClient(
        app_id=credentials["app_id"],
        app_secret=credentials["app_secret"],
    )

def authenticate_solarman_integration(
    db: Session,
    tenant_id: int,
    integration_id: int,
) -> dict | None:
    credentials = get_solarman_credentials(
        db=db,
        tenant_id=tenant_id,
        integration_id=integration_id,
    )

    if credentials is None:
        return None

    client = SolarmanClient(
        app_id=credentials["app_id"],
        app_secret=credentials["app_secret"],
    )

    return client.authenticate(
        email=credentials["email"],
        password_sha256=credentials["password_sha256"],
        org_id=credentials.get("org_id"),
        language=credentials.get("language", "en"),
    )

def save_solarman_token(
    db: Session,
    tenant_id: int,
    integration_id: int,
    access_token: str,
    expires_in: int,
) -> TenantIntegration:
    integration = get_tenant_integration_by_id(
        db=db,
        tenant_id=tenant_id,
        integration_id=integration_id,
    )

    if integration is None:
        raise ValueError("Integração não encontrada.")

    integration.access_token_encrypted = encrypt_value(
        access_token
    )

    integration.token_expires_at = (
        datetime.now(timezone.utc)
        + timedelta(seconds=expires_in)
    )

    integration.last_sync_at = datetime.now(timezone.utc)
    integration.last_sync_status = SyncStatus.SUCCESS
    integration.last_sync_error = None

    db.commit()
    db.refresh(integration)

    return integration

def get_solarman_access_token(
    db: Session,
    tenant_id: int,
    integration_id: int,
) -> str | None:
    integration = get_tenant_integration_by_id(
        db=db,
        tenant_id=tenant_id,
        integration_id=integration_id,
    )

    if integration is None:
        return None

    if not integration.access_token_encrypted:
        return None

    return decrypt_value(
        integration.access_token_encrypted
    )

def solarman_token_is_valid(
    integration: TenantIntegration,
) -> bool:
    if not integration.access_token_encrypted:
        return False

    if integration.token_expires_at is None:
        return False

    return integration.token_expires_at > datetime.now(
        timezone.utc
    )

def save_solarman_sync_error(
    db: Session,
    tenant_id: int,
    integration_id: int,
    error_message: str,
) -> TenantIntegration:
    integration = get_tenant_integration_by_id(
        db=db,
        tenant_id=tenant_id,
        integration_id=integration_id,
    )

    if integration is None:
        raise ValueError("Integração não encontrada.")

    integration.last_sync_at = datetime.now(timezone.utc)
    integration.last_sync_status = SyncStatus.ERROR
    integration.last_sync_error = error_message

    db.commit()
    db.refresh(integration)

    return integration

def get_valid_solarman_token(
    db: Session,
    tenant_id: int,
    integration_id: int,
) -> str | None:
    integration = get_tenant_integration_by_id(
        db=db,
        tenant_id=tenant_id,
        integration_id=integration_id,
    )

    if integration is None:
        return None

    if solarman_token_is_valid(integration):
        return get_solarman_access_token(
            db=db,
            tenant_id=tenant_id,
            integration_id=integration_id,
        )

    credentials = get_solarman_credentials(
        db=db,
        tenant_id=tenant_id,
        integration_id=integration_id,
    )

    if credentials is None:
        return None

    client = SolarmanClient(
        app_id=credentials["app_id"],
        app_secret=credentials["app_secret"],
    )

    response = client.authenticate(
        email=credentials["email"],
        password_sha256=credentials["password_sha256"],
        org_id=credentials.get("org_id"),
        language=credentials.get("language", "en"),
    )

    if response.get("code") not in (0, "0"):
        message = (
            response.get("msg")
            or response.get("message")
            or "A Solarman recusou a autenticação."
        )

        save_solarman_sync_error(
            db=db,
            tenant_id=tenant_id,
            integration_id=integration_id,
            error_message=message,
        )

        raise ValueError(
            f"Falha na autenticação da Solarman: {message}"
        )

    access_token = response.get("access_token")
    expires_in = response.get("expires_in")

    if not access_token or not expires_in:
        raise ValueError(
            "Resposta da Solarman não contém access_token ou expires_in."
        )

    save_solarman_token(
        db=db,
        tenant_id=tenant_id,
        integration_id=integration_id,
        access_token=access_token,
        expires_in=int(expires_in),
    )

    return access_token

def get_solarman_account_info(
    db: Session,
    tenant_id: int,
    integration_id: int,
) -> dict:
    access_token = get_valid_solarman_token(
        db=db,
        tenant_id=tenant_id,
        integration_id=integration_id,
    )

    if not access_token:
        raise ValueError(
            "Não foi possível obter um token válido da Solarman."
        )

    credentials = get_solarman_credentials(
        db=db,
        tenant_id=tenant_id,
        integration_id=integration_id,
    )

    if credentials is None:
        raise ValueError(
            "Credenciais da Solarman não configuradas."
        )

    client = SolarmanClient(
        app_id=credentials["app_id"],
        app_secret=credentials["app_secret"],
    )

    try:
        return client.get_account_info(
            access_token=access_token,
        )

    except Exception as exc:
        save_solarman_sync_error(
            db=db,
            tenant_id=tenant_id,
            integration_id=integration_id,
            error_message=str(exc),
        )

        raise

def authenticate_solarman_integration_for_tenant(
    db: Session,
    tenant_id: int,
    integration_id: int,
) -> dict:
    access_token = get_valid_solarman_token(
        db=db,
        tenant_id=tenant_id,
        integration_id=integration_id,
    )

    if not access_token:
        raise ValueError(
            "Não foi possível obter um token válido da Solarman."
        )

    return {
        "success": True,
        "message": "Integração Solarman autenticada com sucesso.",
    }