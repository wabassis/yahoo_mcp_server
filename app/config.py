"""Módulo de configuração centralizado.

Objetivo:
- Ler variáveis de ambiente com segurança.
- Definir defaults sensatos para desenvolvimento.
- Evitar hardcode de segredos no código-fonte.
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
    """Representa todas as configurações de runtime da aplicação."""

    # Token de autenticação do servidor MCP (obrigatório para chamadas de tools).
    app_api_key: str

    # Endereço de bind do exportador de métricas Prometheus.
    metrics_host: str
    metrics_port: int

    # Configuração do cache Redis (opcional; app possui fallback em memória).
    redis_host: str
    redis_port: int
    redis_db: int
    redis_password: str | None

    # Tempo de vida (TTL) do cache em segundos.
    cache_ttl_seconds: int

    # Configuração do transporte MCP.
    # - stdio: ideal para integração local com agente anexado ao processo.
    # - streamable-http: ideal para execução em container/servidor.
    mcp_transport: str
    mcp_host: str
    mcp_port: int


settings = Settings(
    # Segurança: padrão vazio força erro explícito se não configurado.
    app_api_key=os.getenv("APP_API_KEY", ""),
    # Prometheus: por padrão escuta em todas as interfaces do container.
    metrics_host=os.getenv("METRICS_HOST", "0.0.0.0"),
    metrics_port=int(os.getenv("METRICS_PORT", "9100")),
    # Redis: valores padrão compatíveis com docker-compose.
    redis_host=os.getenv("REDIS_HOST", "redis"),
    redis_port=int(os.getenv("REDIS_PORT", "6379")),
    redis_db=int(os.getenv("REDIS_DB", "0")),
    redis_password=os.getenv("REDIS_PASSWORD"),
    # TTL padrão de 5 min para reduzir chamadas repetidas ao Yahoo.
    cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "300")),
    # Em container, `streamable-http` evita dependência de stdin anexado.
    mcp_transport=os.getenv("MCP_TRANSPORT", "streamable-http"),
    mcp_host=os.getenv("MCP_HOST", "0.0.0.0"),
    mcp_port=int(os.getenv("MCP_PORT", "8000")),
)
