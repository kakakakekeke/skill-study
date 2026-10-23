import json
from dataclasses import dataclass
from pathlib import Path

DEFAULTS = {"timeout": 30, "retries": 3, "verbose": False}


@dataclass
class Config:
    host: str
    port: int
    timeout: int
    retries: int
    verbose: bool


def load_config(path: str | Path) -> Config:
    raw = json.loads(Path(path).read_text())
    merged = dict(raw)
    for key in ("retries", "verbose"):
        merged.setdefault(key, DEFAULTS[key])
    return Config(
        host=merged["host"],
        port=int(merged["port"]),
        timeout=int(merged["timeout"]) if "timeout" in merged else None,
        retries=int(merged["retries"]),
        verbose=bool(merged["verbose"]),
    )
