"""Servidor MCP para integração de agentes (Hermes) com Yahoo Finance.

Este módulo concentra:
1) Registro das ferramentas MCP expostas para o agente.
2) Validação de autenticação por API key.
3) Bootstrap de métricas Prometheus e inicialização do servidor MCP.
"""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP
from prometheus_client import start_http_server

from app.config import settings
from app.service import YahooFinanceService

# Logger padronizado para facilitar troubleshooting em containers.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Instância do servidor MCP (camada de protocolo e tools).
mcp = FastMCP("yahoo-finance-mcp")

# Serviço de domínio para acesso Yahoo Finance (com cache/telemetria).
service = YahooFinanceService()
_metrics_started = False


def _configure_runtime() -> None:
    """Aplica configuração de runtime para execução via python e via ASGI."""
    global _metrics_started

    mcp.settings.host = settings.mcp_host
    mcp.settings.port = settings.mcp_port
    mcp.settings.streamable_http_path = settings.mcp_path

    if not _metrics_started:
        start_http_server(settings.metrics_port, addr=settings.metrics_host)
        _metrics_started = True


def _assert_api_key(api_key: str) -> None:
    """Valida chave de acesso do cliente.

    Observação: o Yahoo Finance (via yfinance) não exige token nativo,
    porém este servidor MCP exige APP_API_KEY para restringir acesso.
    """
    if not settings.app_api_key:
        raise ValueError("APP_API_KEY não configurada no ambiente (.env).")
    if api_key != settings.app_api_key:
        raise PermissionError("API key inválida.")


@mcp.tool()
def yahoo_cash_flow(symbol: str, api_key: str) -> dict:
    """Consulta cash flow anual do ticker informado."""
    _assert_api_key(api_key)
    return service.get_cash_flow(symbol)


@mcp.tool()
def yahoo_income_statement(symbol: str, api_key: str) -> dict:
    """Consulta demonstrativo de resultados anual do ticker."""
    _assert_api_key(api_key)
    return service.get_income_statement(symbol)


@mcp.tool()
def yahoo_balance_sheet(symbol: str, api_key: str) -> dict:
    """Consulta balanço patrimonial anual do ticker."""
    _assert_api_key(api_key)
    return service.get_balance_sheet(symbol)


@mcp.tool()
def yahoo_quote(symbol: str, api_key: str) -> dict:
    """Consulta a cotação intradiária mais recente do ticker."""
    _assert_api_key(api_key)
    return service.get_quote(symbol)


if __name__ == "__main__":
    _configure_runtime()

    if settings.mcp_transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", mount_path=settings.mcp_path)


# Compatibilidade com execução via uvicorn/gunicorn, por exemplo:
# `uvicorn app.main:app --host 0.0.0.0 --port 8000`
_configure_runtime()
app = mcp.streamable_http_app()
