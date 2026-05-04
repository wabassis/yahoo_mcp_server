"""Módulo de configuração centralizado.

Responsável por ler variáveis de ambiente com segurança,
validar defaults e expor um objeto único de configuração.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Carrega variáveis do arquivo .env para o ambiente do processo.
# Em produção, o recomendado é injetar variáveis via secret manager.
load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Configurações imutáveis da aplicação.

    Variáveis sensíveis (como API keys) são lidas do ambiente para evitar
    hardcode em código-fonte e vazamento em repositórios.
    """

    # Chave usada para autenticar clientes contra este servidor MCP.
    # Yahoo em si não exige chave para yfinance, mas este controle protege seu serviço.
    app_api_key: str

    # Host/porta para exportação de métricas Prometheus.
    metrics_host: str
    metrics_port: int

    # Configuração de cache Redis (opcional).
    redis_host: str
    redis_port: int
    redis_db: int
    redis_password: str | None

    # TTL do cache em segundos para reduzir risco de rate limiting no Yahoo.
    cache_ttl_seconds: int


settings = Settings(
    app_api_key=os.getenv("APP_API_KEY", ""),
    metrics_host=os.getenv("METRICS_HOST", "0.0.0.0"),
    metrics_port=int(os.getenv("METRICS_PORT", "9100")),
    redis_host=os.getenv("REDIS_HOST", "redis"),
    redis_port=int(os.getenv("REDIS_PORT", "6379")),
    redis_db=int(os.getenv("REDIS_DB", "0")),
    redis_password=os.getenv("REDIS_PASSWORD"),
    cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "300")),
)
