from app.core.config import settings
from app.services.providers.generation_provider import GenerationProvider
from app.services.providers.mock_generation_provider import MockGenerationProvider
from app.services.providers.solarman_provider import SolarmanProvider
from sqlalchemy.orm import Session


def get_generation_provider(db: Session) -> GenerationProvider:
    provider_name = settings.generation_data_provider.lower()

    if provider_name == "mock":
        return MockGenerationProvider()

    if provider_name == "solarman":
        return SolarmanProvider(db)

    raise ValueError(
        f"Provider de geração não suportado: {settings.generation_data_provider}"
    )