"""Camada de serviço para acessar Yahoo Finance com cache e telemetria."""

from __future__ import annotations

import json
from typing import Any

import redis
import yfinance as yf
from cachetools import TTLCache
from prometheus_client import Counter, Histogram

from app.config import settings

# Cache local em memória (fallback) para cenários sem Redis.
_memory_cache = TTLCache(maxsize=1_000, ttl=settings.cache_ttl_seconds)

# Métricas Prometheus para observabilidade.
YAHOO_REQUESTS_TOTAL = Counter(
    "yahoo_requests_total",
    "Total de chamadas ao Yahoo Finance por tipo de recurso.",
    ["resource"],
)

YAHOO_REQUEST_DURATION_SECONDS = Histogram(
    "yahoo_request_duration_seconds",
    "Tempo de resposta das consultas ao Yahoo Finance.",
    ["resource"],
)


class YahooFinanceService:
    """Serviço de leitura de dados financeiros com cache Redis + memória."""

    def __init__(self) -> None:
        """Inicializa conexão Redis para cache distribuído.

        Caso Redis esteja indisponível, o serviço continua operando com cache local.
        """
        self.redis_client: redis.Redis | None = None
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password,
                decode_responses=True,
                socket_timeout=2,
                socket_connect_timeout=2,
            )
            self.redis_client.ping()
        except Exception:
            self.redis_client = None

    def _cache_get(self, key: str) -> dict[str, Any] | None:
        """Busca item do cache primeiro em Redis e depois memória local."""
        if self.redis_client:
            try:
                raw = self.redis_client.get(key)
                if raw:
                    loaded = json.loads(raw)
                    if isinstance(loaded, dict):
                        return loaded
            except Exception:
                # Degrada graciosamente para cache em memória quando Redis falhar
                # (indisponibilidade/intermitência/dado inválido).
                pass

        value = _memory_cache.get(key)
        return value if isinstance(value, dict) else None

    def _cache_set(self, key: str, value: dict[str, Any]) -> None:
        """Salva item no cache Redis e em memória para resilência."""
        if self.redis_client:
            try:
                self.redis_client.setex(key, settings.cache_ttl_seconds, json.dumps(value))
            except Exception:
                # Cache distribuído é opcional; nunca deve quebrar o fluxo principal.
                pass
        _memory_cache[key] = value

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        """Normaliza e valida ticker recebido do cliente."""
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("symbol não pode ser vazio.")
        return normalized

    @staticmethod
    def _normalize_dataframe(dataframe: Any) -> dict[str, Any]:
        """Converte DataFrame do pandas em dicionário serializável para MCP."""
        if dataframe is None:
            return {}
        if getattr(dataframe, "empty", True):
            return {}
        return dataframe.fillna("").to_dict()

    def get_cash_flow(self, symbol: str) -> dict[str, Any]:
        """Retorna fluxo de caixa (cash flow) anual para um ticker."""
        normalized_symbol = self._normalize_symbol(symbol)
        cache_key = f"cashflow:{normalized_symbol}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        YAHOO_REQUESTS_TOTAL.labels(resource="cash_flow").inc()
        with YAHOO_REQUEST_DURATION_SECONDS.labels(resource="cash_flow").time():
            ticker = yf.Ticker(normalized_symbol)
            data = self._normalize_dataframe(ticker.cashflow)

        result = {"symbol": normalized_symbol, "cash_flow": data}
        self._cache_set(cache_key, result)
        return result

    def get_income_statement(self, symbol: str) -> dict[str, Any]:
        """Retorna demonstrativo de resultados (income statement)."""
        normalized_symbol = self._normalize_symbol(symbol)
        cache_key = f"income:{normalized_symbol}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        YAHOO_REQUESTS_TOTAL.labels(resource="income_statement").inc()
        with YAHOO_REQUEST_DURATION_SECONDS.labels(resource="income_statement").time():
            ticker = yf.Ticker(normalized_symbol)
            data = self._normalize_dataframe(ticker.financials)

        result = {"symbol": normalized_symbol, "income_statement": data}
        self._cache_set(cache_key, result)
        return result

    def get_balance_sheet(self, symbol: str) -> dict[str, Any]:
        """Retorna balanço patrimonial para um ticker."""
        normalized_symbol = self._normalize_symbol(symbol)
        cache_key = f"balance:{normalized_symbol}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        YAHOO_REQUESTS_TOTAL.labels(resource="balance_sheet").inc()
        with YAHOO_REQUEST_DURATION_SECONDS.labels(resource="balance_sheet").time():
            ticker = yf.Ticker(normalized_symbol)
            data = self._normalize_dataframe(ticker.balance_sheet)

        result = {"symbol": normalized_symbol, "balance_sheet": data}
        self._cache_set(cache_key, result)
        return result

    def get_quote(self, symbol: str) -> dict[str, Any]:
        """Retorna cotação intradiária mais recente de um ticker."""
        normalized_symbol = self._normalize_symbol(symbol)
        cache_key = f"quote:{normalized_symbol}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        YAHOO_REQUESTS_TOTAL.labels(resource="quote").inc()
        with YAHOO_REQUEST_DURATION_SECONDS.labels(resource="quote").time():
            try:
                ticker = yf.Ticker(normalized_symbol)
                history = ticker.history(period="1d", interval="1m")
            except Exception as exc:
                result = {
                    "symbol": normalized_symbol,
                    "quote": {},
                    "error": f"quote_unavailable: {exc}",
                }
                self._cache_set(cache_key, result)
                return result

        if history is None or getattr(history, "empty", True):
            result = {"symbol": normalized_symbol, "quote": {}}
            self._cache_set(cache_key, result)
            return result

        last_row = history.tail(1).iloc[0]
        last_ts = history.index[-1]
        result = {
            "symbol": normalized_symbol,
            "quote": {
                "timestamp": str(last_ts),
                "open": float(last_row["Open"]),
                "high": float(last_row["High"]),
                "low": float(last_row["Low"]),
                "close": float(last_row["Close"]),
                "volume": int(last_row["Volume"]),
            },
        }
        self._cache_set(cache_key, result)
        return result
