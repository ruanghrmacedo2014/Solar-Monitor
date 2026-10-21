import json
from datetime import datetime, timedelta, timezone
from app.core.security.encryption import decrypt_value, encrypt_value
from sqlalchemy.orm import Session
from app.models.tenant_integration import (
    IntegrationProvider,
    TenantIntegration,
)
from app.core.security.encryption import decrypt_value
from app.services.providers.generation_provider import GenerationProvider
from app.services.integrations.solarman_client import SolarmanClient

class SolarmanProvider(GenerationProvider):
    """Provider de dados de geração através da Solarman."""

    def __init__(self, db: Session):
        self.db = db

    def _get_integration(self, tenant_id: int) -> TenantIntegration:
        integration = (
            self.db.query(TenantIntegration)
            .filter(
                TenantIntegration.tenant_id == tenant_id,
                TenantIntegration.provider == IntegrationProvider.SOLARMAN,
                TenantIntegration.is_active.is_(True),
            )
            .first()
        )

        if integration is None:
            raise ValueError(
                f"Nenhuma integração Solarman ativa encontrada para o tenant {tenant_id}."
            )

        return integration
    
    def _get_credentials(self, integration: TenantIntegration) -> dict:
        if not integration.credentials_encrypted:
            raise ValueError(
                f"A integração {integration.id} não possui credenciais configuradas."
            )

        credentials_json = decrypt_value(
            integration.credentials_encrypted
        )

        return json.loads(credentials_json)

    def _get_client(
        self,
        integration: TenantIntegration,
    ) -> SolarmanClient:
        credentials = self._get_credentials(integration)

        return SolarmanClient(
            app_id=credentials["app_id"],
            app_secret=credentials["app_secret"],
        )

    def _authenticate(
        self,
        integration: TenantIntegration,
    ) -> dict:
        credentials = self._get_credentials(integration)
        client = self._get_client(integration)

        response = client.authenticate(
            email=credentials["email"],
            password_sha256=credentials["password_sha256"],
            org_id=credentials.get("org_id"),
            language=credentials.get("language", "en"),
        )

        access_token = response.get("access_token")
        expires_in = response.get("expires_in")

        if not access_token:
            raise ValueError(
                "A Solarman autenticou, mas não retornou access_token."
            )

        if not expires_in:
            raise ValueError(
                "A Solarman autenticou, mas não retornou expires_in."
            )

        integration.access_token_encrypted = encrypt_value(access_token)

        integration.token_expires_at = (
            datetime.now(timezone.utc)
            + timedelta(seconds=int(expires_in))
        )

        self.db.commit()
        self.db.refresh(integration)

        return response

    def _get_valid_access_token(
        self,
        integration: TenantIntegration,
    ) -> str:
        now = datetime.now(timezone.utc)

        if (
            integration.access_token_encrypted
            and integration.token_expires_at
            and integration.token_expires_at > now
        ):
            return decrypt_value(
                integration.access_token_encrypted
            )

        response = self._authenticate(integration)

        return decrypt_value(
            integration.access_token_encrypted
        )

    def get_account_info(
        self,
        tenant_id: int,
    ) -> dict:
        integration = self._get_integration(tenant_id)

        access_token = self._get_valid_access_token(
            integration
        )

        credentials = self._get_credentials(
            integration
        )

        client = self._get_client(
            integration
        )

        return client.get_account_info(
            access_token=access_token,
            language=credentials.get(
                "language",
                "en",
            ),
        )

    def get_station_base(
        self,
        tenant_id: int,
        station_id: int,
    ) -> dict:
        integration = self._get_integration(tenant_id)

        access_token = self._get_valid_access_token(
            integration
        )

        credentials = self._get_credentials(
            integration
        )

        client = self._get_client(
            integration
        )

        account_info = client.get_account_info(
            access_token=access_token,
            language=credentials.get(
                "language",
                "en",
            ),
        )

        org_info_list = account_info.get(
            "orgInfoList"
        ) or []

        company_id = None

        if org_info_list:
            company_id = org_info_list[0].get(
                "companyId"
            )

        return client.get_station_base(
            access_token=access_token,
            station_id=station_id,
            company_id=company_id,
            language=credentials.get(
                "language",
                "en",
            ),
        )

    def get_station_list(
        self,
        tenant_id: int,
        page: int = 1,
        size: int = 50,
    ) -> dict:
        integration = self._get_integration(tenant_id)

        access_token = self._get_valid_access_token(
            integration
        )

        credentials = self._get_credentials(
            integration
        )

        client = self._get_client(
            integration
        )

        return client.get_station_list(
            access_token=access_token,
            page=page,
            size=size,
            language=credentials.get(
                "language",
                "en",
            ),
        )

    def get_station_devices(
        self,
        tenant_id: int,
        station_id: int,
        page: int = 1,
        size: int = 50,
        device_type: str | None = None,
    ) -> dict:
        integration = self._get_integration(tenant_id)

        access_token = self._get_valid_access_token(
            integration
        )

        credentials = self._get_credentials(
            integration
        )

        client = self._get_client(
            integration
        )

        return client.get_station_devices(
            access_token=access_token,
            station_id=station_id,
            page=page,
            size=size,
            device_type=device_type,
            language=credentials.get(
                "language",
                "en",
            ),
        )

    def get_station_history(
        self,
        tenant_id: int,
        station_id: int,
        start_time: str,
        end_time: str,
        time_type: int = 1,
        language: str = "en",
    ) -> dict:
        integration = self._get_integration(tenant_id)

        access_token = self._get_valid_access_token(integration)
        client = self._get_client(integration)

        return client.get_station_history(
            access_token=access_token,
            station_id=station_id,
            start_time=start_time,
            end_time=end_time,
            time_type=time_type,
            language=language,
        )

    def get_generation(
        self,
        tenant_id: int,
        solar_plant_id: int,
        start_at: datetime,
        end_at: datetime,
    ) -> list[dict]:
        raise NotImplementedError(
            "Integração de geração com a Solarman ainda não implementada."
        )