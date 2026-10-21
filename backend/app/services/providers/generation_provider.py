from abc import ABC, abstractmethod
from datetime import datetime


class GenerationProvider(ABC):
    """Contrato para provedores de dados de geração solar."""

    @abstractmethod
    def get_generation(
        self,
        tenant_id: int,
        solar_plant_id: int,
        start_at: datetime,
        end_at: datetime,
    ) -> list[dict]:
        """
        Retorna dados de geração de uma usina dentro de um período.
        """
        raise NotImplementedError