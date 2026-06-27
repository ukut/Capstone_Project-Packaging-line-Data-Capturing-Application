"""Pydantic schema for the login form.

Trivial today, but it keeps validation consistent with the rest of the app
(every inbound payload becomes a validated model before the service sees it) and
gives one obvious place to add rules later, e.g. a max length or a username
normalisation step.
"""

from pydantic import BaseModel, field_validator


class LoginInput(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def _strip_username(cls, v: str) -> str:
        return v.strip()
