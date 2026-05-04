"""Servidor MCP para integração de agentes (Hermes) com Yahoo Finance."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from prometheus_client import start_http_server

from app.config import settings
from app.service import YahooFinanceService

# Instância do servidor MCP que expõe ferramentas para o agente Hermes.
mcp = FastMCP("yahoo-finance-mcp")

# Serviço reutilizável para chamadas Yahoo + cache.
service = YahooFinanceService()


def _assert_api_key(api_key: str) -> None:
    """Valida chave do cliente para proteger o servidor.

    Mesmo que o Yahoo não exija token no yfinance, proteger o MCP evita
    uso indevido por clientes não autorizados.
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


if __name__ == "__main__":
    # Exporta métricas para Prometheus em porta separada.
    start_http_server(settings.metrics_port, addr=settings.metrics_host)

    # Executa servidor MCP em stdio (compatível com integração local de agentes).
    mcp.run(transport="stdio")
