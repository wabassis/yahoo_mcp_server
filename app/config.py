"""Módulo de configuração centralizado.

Responsável por ler variáveis de ambiente com segurança,
validar defaults e expor um objeto único de configuração.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Carrega variáveis do arquivo `.env` quando presente.
# Em produção, prefira injetar variáveis por secret manager/orquestrador.
load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Configurações imutáveis da aplicação."""

    app_api_key: str

    metrics_host: str
    metrics_port: int

    redis_host: str
    redis_port: int
    redis_db: int
    redis_password: str | None

    cache_ttl_seconds: int

    # Transporte MCP: `stdio` (local) ou `streamable-http` (container/server).
    mcp_transport: str
    mcp_host: str
    mcp_port: int
    mcp_path: str


settings = Settings(
    app_api_key=os.getenv("APP_API_KEY", ""),
    metrics_host=os.getenv("METRICS_HOST", "0.0.0.0"),
    metrics_port=int(os.getenv("METRICS_PORT", "9100")),
    redis_host=os.getenv("REDIS_HOST", "redis"),
    redis_port=int(os.getenv("REDIS_PORT", "6379")),
    redis_db=int(os.getenv("REDIS_DB", "0")),
    redis_password=os.getenv("REDIS_PASSWORD"),
    cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "300")),
    mcp_transport=os.getenv("MCP_TRANSPORT", "streamable-http"),
    mcp_host=os.getenv("MCP_HOST", "0.0.0.0"),
    mcp_port=int(os.getenv("MCP_PORT", "8000")),
    mcp_path=os.getenv("MCP_PATH", "/mcp"),
)
