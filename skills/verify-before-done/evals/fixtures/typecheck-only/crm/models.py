from dataclasses import dataclass


@dataclass(frozen=True)
class Contact:
    id: int
    name: str
    email: str
    tier: str = "free"
