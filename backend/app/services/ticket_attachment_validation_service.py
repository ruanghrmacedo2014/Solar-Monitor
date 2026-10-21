from pathlib import Path


class TicketAttachmentValidationService:
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    ALLOWED_EXTENSIONS = {
        ".pdf",
        ".txt",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }

    ALLOWED_CONTENT_TYPES = {
        "application/pdf",
        "text/plain",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    def validate(
        self,
        filename: str,
        content_type: str,
        file_size: int,
    ) -> str:
        extension = Path(filename).suffix.lower()

        if not extension:
            raise ValueError(
                "O arquivo precisa possuir uma extensão."
            )

        if extension not in self.ALLOWED_EXTENSIONS:
            raise ValueError(
                "Tipo de arquivo não permitido."
            )

        if content_type not in self.ALLOWED_CONTENT_TYPES:
            raise ValueError(
                "Tipo MIME não permitido."
            )

        if file_size <= 0:
            raise ValueError(
                "O arquivo não pode estar vazio."
            )

        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(
                "O arquivo excede o tamanho máximo permitido de 10 MB."
            )

        return extension