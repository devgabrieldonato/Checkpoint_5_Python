"""Cliente HTTP e regras de conversão para a API de moedas AwesomeAPI."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from xml.etree import ElementTree
import json

import requests


BASE_URL = "https://economia.awesomeapi.com.br"
AVAILABLE_PAIRS_URL = f"{BASE_URL}/xml/available"
AVAILABLE_CURRENCIES_URL = f"{BASE_URL}/xml/available/uniq"


class AwesomeAPIError(RuntimeError):
    """Erro legível relacionado à comunicação ou aos dados da AwesomeAPI."""


@dataclass(frozen=True, slots=True)
class Currency:
    code: str
    name: str


@dataclass(frozen=True, slots=True)
class CurrencyPair:
    code: str
    base: str
    quote: str
    name: str


@dataclass(frozen=True, slots=True)
class Quote:
    pair: str
    name: str
    bid: Decimal
    ask: Decimal
    high: Decimal
    low: Decimal
    pct_change: Decimal
    created_at: str


def _parse_xml_items(content: bytes, context: str) -> dict[str, str]:
    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError as error:
        raise AwesomeAPIError(f"A AwesomeAPI retornou XML inválido para {context}.") from error

    return {
        child.tag.strip(): (child.text or "").strip()
        for child in root
        if child.tag.strip()
    }


def _to_decimal(value: Any, field: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise AwesomeAPIError(f"O campo '{field}' da cotação é inválido.") from error


class AwesomeAPIClient:
    def __init__(self, timeout: float = 10.0, session: requests.Session | None = None):
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": "ConversorMoedasFIAP/1.0"})

    def _get(self, url: str) -> requests.Response:
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response
        except requests.Timeout as error:
            raise AwesomeAPIError("A AwesomeAPI demorou demais para responder.") from error
        except requests.RequestException as error:
            raise AwesomeAPIError("Não foi possível acessar a AwesomeAPI.") from error

    def get_currencies(self) -> list[Currency]:
        response = self._get(AVAILABLE_CURRENCIES_URL)
        items = _parse_xml_items(response.content, "a lista de moedas")
        return sorted(
            (Currency(code=code, name=name) for code, name in items.items()),
            key=lambda currency: currency.code,
        )

    def get_pairs(self) -> list[CurrencyPair]:
        response = self._get(AVAILABLE_PAIRS_URL)
        items = _parse_xml_items(response.content, "a lista de pares")
        pairs: list[CurrencyPair] = []
        for code, name in items.items():
            try:
                base, quote = code.split("-", maxsplit=1)
            except ValueError:
                continue
            pairs.append(CurrencyPair(code=code, base=base, quote=quote, name=name))
        return sorted(pairs, key=lambda pair: (pair.base, pair.quote))

    def get_quote(self, base: str, quote: str) -> Quote:
        pair = f"{base.upper()}-{quote.upper()}"
        response = self._get(f"{BASE_URL}/json/last/{pair}")
        try:
            payload = response.json()
        except requests.JSONDecodeError as error:
            raise AwesomeAPIError("A AwesomeAPI retornou uma resposta JSON inválida.") from error

        data = payload.get(pair.replace("-", ""))
        if not isinstance(data, dict):
            message = payload.get("message", "Cotação não encontrada.")
            raise AwesomeAPIError(str(message))

        return Quote(
            pair=pair,
            name=str(data.get("name", pair)),
            bid=_to_decimal(data.get("bid"), "bid"),
            ask=_to_decimal(data.get("ask"), "ask"),
            high=_to_decimal(data.get("high"), "high"),
            low=_to_decimal(data.get("low"), "low"),
            pct_change=_to_decimal(data.get("pctChange"), "pctChange"),
            created_at=str(data.get("create_date", "")),
        )


def calculate_purchase(amount: Decimal, quote: Quote) -> Decimal:
    if amount <= 0:
        raise ValueError("O montante deve ser maior que zero.")
    return amount * quote.ask


def save_pairs_snapshot(pairs: list[CurrencyPair], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": AVAILABLE_PAIRS_URL,
        "description": "Pares de moedas disponibilizados pela AwesomeAPI.",
        "pairs": [asdict(pair) for pair in pairs],
    }
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

