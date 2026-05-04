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
    """Retorna cash flow anual do ticker informado.

    Args:
        symbol: Código do ativo (ex.: AAPL, MSFT, PETR4.SA).
        api_key: Token de autenticação do cliente MCP.
    """
    _assert_api_key(api_key)
    return service.get_cash_flow(symbol)


@mcp.tool()
def yahoo_income_statement(symbol: str, api_key: str) -> dict:
    """Retorna income statement anual do ticker informado."""
    _assert_api_key(api_key)
    return service.get_income_statement(symbol)


@mcp.tool()
def yahoo_balance_sheet(symbol: str, api_key: str) -> dict:
    """Retorna balance sheet anual do ticker informado."""
    _assert_api_key(api_key)
    return service.get_balance_sheet(symbol)


def _run_mcp_server() -> None:
    """Inicializa o servidor MCP no transporte configurado.

    Importante: para evitar erro de incompatibilidade de parâmetros entre versões
    do pacote `mcp`, o modo `streamable-http` usa apenas `host` e `port`.
    O path pode ser roteado externamente por proxy reverso se necessário.
    """
    # Normaliza o valor para evitar falhas por caixa alta/minúscula.
    transport = settings.mcp_transport.strip().lower()

    # Modo local padrão para integração de agentes em stdio.
    if transport == "stdio":
        logger.info("Iniciando MCP em modo stdio")
        mcp.run(transport="stdio")
        return

    # Modo de servidor para docker/k8s (HTTP).
    if transport == "streamable-http":
        logger.info(
            "Iniciando MCP em modo streamable-http em %s:%s",
            settings.mcp_host,
            settings.mcp_port,
        )
        # OBS: não passamos `path` para evitar TypeError em versões do SDK
        # que não aceitam esse argumento em `run()`.
        mcp.run(
            transport="streamable-http",
            host=settings.mcp_host,
            port=settings.mcp_port,
        )
        return

    # Falha explícita para transporte inválido (erro de configuração).
    raise ValueError(
        f"MCP_TRANSPORT inválido: {settings.mcp_transport}. Use 'stdio' ou 'streamable-http'."
    )


if __name__ == "__main__":
    # Exporta endpoint /metrics para Prometheus em porta dedicada.
    start_http_server(settings.metrics_port, addr=settings.metrics_host)
    logger.info("Métricas Prometheus em %s:%s", settings.metrics_host, settings.metrics_port)

    # Inicializa servidor MCP com logs de startup para diagnóstico.
    _run_mcp_server()
