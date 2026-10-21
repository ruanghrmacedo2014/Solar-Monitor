from pathlib import Path
from uuid import uuid4


class TicketAttachmentStorageService:
    def __init__(self, base_path: str = "storage"):
        self.base_path = Path(base_path)

    def save_file(
        self,
        tenant_id: int,
        ticket_id: int,
        file_extension: str,
        content: bytes,
    ) -> tuple[str, str]:
        ticket_path = (
            self.base_path
            / "tickets"
            / str(tenant_id)
            / str(ticket_id)
        )

        ticket_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        stored_filename = (
            f"{uuid4().hex}{file_extension}"
        )

        file_path = ticket_path / stored_filename

        file_path.write_bytes(content)

        return (
            stored_filename,
            str(file_path),
        )

    def delete_file(self, storage_path: str) -> None:
        file_path = Path(storage_path)

        if file_path.exists():
            file_path.unlink()