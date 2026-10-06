from decimal import Decimal
import unittest

from awesomeapi import (
    AwesomeAPIClient,
    AwesomeAPIError,
    Quote,
    calculate_purchase,
)


class FakeResponse:
    def __init__(self, content=b"", payload=None):
        self.content = content
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.headers = {}

    def get(self, _url, timeout):
        return next(self.responses)


class AwesomeAPIClientTests(unittest.TestCase):
    def test_parses_available_pairs(self):
        xml = b"<xml><USD-BRL>Dolar/Real</USD-BRL><EUR-USD>Euro/Dolar</EUR-USD></xml>"
        client = AwesomeAPIClient(session=FakeSession([FakeResponse(content=xml)]))

        pairs = client.get_pairs()

        self.assertEqual(pairs[0].code, "EUR-USD")
        self.assertEqual(pairs[1].base, "USD")
        self.assertEqual(pairs[1].quote, "BRL")

    def test_parses_quote(self):
        payload = {
            "USDBRL": {
                "name": "Dolar/Real",
                "bid": "5.10",
                "ask": "5.12",
                "high": "5.20",
                "low": "5.00",
                "pctChange": "0.5",
                "create_date": "2026-01-01 10:00:00",
            }
        }
        client = AwesomeAPIClient(session=FakeSession([FakeResponse(payload=payload)]))

        quote = client.get_quote("usd", "brl")

        self.assertEqual(quote.ask, Decimal("5.12"))
        self.assertEqual(quote.pair, "USD-BRL")

    def test_calculates_purchase_using_ask_rate(self):
        quote = Quote(
            pair="USD-BRL",
            name="Dolar/Real",
            bid=Decimal("5.10"),
            ask=Decimal("5.12"),
            high=Decimal("5.20"),
            low=Decimal("5.00"),
            pct_change=Decimal("0.5"),
            created_at="2026-01-01 10:00:00",
        )

        self.assertEqual(calculate_purchase(Decimal("100"), quote), Decimal("512.00"))

    def test_rejects_non_positive_amount(self):
        quote = Quote(
            "USD-BRL", "Dolar/Real", Decimal("1"), Decimal("1"),
            Decimal("1"), Decimal("1"), Decimal("0"), "",
        )
        with self.assertRaises(ValueError):
            calculate_purchase(Decimal("0"), quote)

    def test_rejects_invalid_xml(self):
        client = AwesomeAPIClient(session=FakeSession([FakeResponse(content=b"invalid")]))
        with self.assertRaises(AwesomeAPIError):
            client.get_pairs()


if __name__ == "__main__":
    unittest.main()

