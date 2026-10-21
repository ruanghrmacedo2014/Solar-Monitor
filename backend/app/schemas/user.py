import re

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not re.search(r"[A-Z]", value):
            raise ValueError(
                "A senha deve conter pelo menos uma letra maiúscula."
            )

        if not re.search(r"[a-z]", value):
            raise ValueError(
                "A senha deve conter pelo menos uma letra minúscula."
            )

        if not re.search(r"\d", value):
            raise ValueError(
                "A senha deve conter pelo menos um número."
            )

        if not re.search(r"[^A-Za-z0-9]", value):
            raise ValueError(
                "A senha deve conter pelo menos um caractere especial."
            )

        return value