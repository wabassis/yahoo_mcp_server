"""Servidor MCP para integração de agentes (Hermes) com Yahoo Finance."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from prometheus_client import start_http_server

from app.config import settings
from app.service import YahooFinanceService

mcp = FastMCP("yahoo-finance-mcp")
service = YahooFinanceService()


def _assert_api_key(api_key: str) -> None:
    """Valida chave do cliente para proteger o servidor."""
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
    start_http_server(settings.metrics_port, addr=settings.metrics_host)

    if settings.mcp_transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(
            transport="streamable-http",
            host=settings.mcp_host,
            port=settings.mcp_port,
            path=settings.mcp_path,
        )
