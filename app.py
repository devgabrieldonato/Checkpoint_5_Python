"""Interface Streamlit do conversor de moedas."""

from decimal import Decimal
from pathlib import Path

import streamlit as st

from awesomeapi import (
    AwesomeAPIClient,
    AwesomeAPIError,
    Currency,
    CurrencyPair,
    calculate_purchase,
    save_pairs_snapshot,
)


st.set_page_config(
    page_title="Câmbio Fácil",
    page_icon="💱",
    layout="centered",
)

st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(145deg, #f7f9fc 0%, #edf2ff 100%); }
    [data-testid="stHeader"] { background: transparent; }
    .hero { padding: 1.2rem 0 1rem; }
    .eyebrow { color: #635bff; font-weight: 700; letter-spacing: .12em; font-size: .78rem; }
    .hero h1 { color: #17233c; font-size: 2.6rem; margin: .25rem 0; }
    .hero p { color: #64748b; font-size: 1.05rem; }
    .result-card {
        background: #17233c; color: white; padding: 1.5rem; border-radius: 18px;
        box-shadow: 0 16px 40px rgba(23, 35, 60, .18); margin-top: 1rem;
    }
    .result-label { color: #b9c5db; font-size: .9rem; }
    .result-value { font-size: 2rem; font-weight: 750; margin: .2rem 0; }
    .result-rate { color: #d9e2f2; }
    div[data-testid="stForm"] { background: white; border: 0; border-radius: 18px; padding: 1.2rem; box-shadow: 0 12px 35px rgba(52, 67, 101, .08); }
    .stButton button { background: #635bff; color: white; border: 0; border-radius: 10px; font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_client() -> AwesomeAPIClient:
    return AwesomeAPIClient()


@st.cache_data(ttl=3600, show_spinner=False)
def load_catalog() -> tuple[list[Currency], list[CurrencyPair]]:
    client = get_client()
    currencies = client.get_currencies()
    pairs = client.get_pairs()
    try:
        save_pairs_snapshot(pairs, Path("data/moedas.json"))
    except OSError:
        pass
    return currencies, pairs


def format_money(value: Decimal, code: str) -> str:
    formatted = f"{value:,.4f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"{formatted} {code}"


st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">AWESOMEAPI • COTAÇÃO EM TEMPO REAL</div>
      <h1>Câmbio Fácil 💱</h1>
      <p>Descubra quanto você precisa para comprar moedas internacionais.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    with st.spinner("Carregando moedas disponíveis..."):
        currencies, pairs = load_catalog()
except AwesomeAPIError as error:
    st.error(str(error))
    st.info("Confira sua conexão com a internet e tente novamente.")
    st.stop()

currency_names = {currency.code: currency.name for currency in currencies}
buy_codes = sorted({pair.base for pair in pairs})

with st.container(border=True):
    buy_code = st.selectbox(
        "Moeda que deseja comprar",
        buy_codes,
        format_func=lambda code: f"{code} — {currency_names.get(code, code)}",
        index=buy_codes.index("USD") if "USD" in buy_codes else 0,
    )
    available_payment_codes = sorted(
        {pair.quote for pair in pairs if pair.base == buy_code}
    )
    payment_code = st.selectbox(
        "Moeda utilizada no pagamento",
        available_payment_codes,
        format_func=lambda code: f"{code} — {currency_names.get(code, code)}",
        index=(
            available_payment_codes.index("BRL")
            if "BRL" in available_payment_codes
            else 0
        ),
    )
    amount = st.number_input(
        f"Quanto deseja comprar em {buy_code}?",
        min_value=0.01,
        value=100.00,
        step=10.00,
        format="%.2f",
    )
    submitted = st.button("Calcular conversão", use_container_width=True)

if submitted:
    try:
        with st.spinner("Consultando a cotação mais recente..."):
            current_quote = get_client().get_quote(buy_code, payment_code)
        decimal_amount = Decimal(str(amount))
        total = calculate_purchase(decimal_amount, current_quote)
    except (AwesomeAPIError, ValueError) as error:
        st.error(str(error))
    else:
        st.markdown(
            f"""
            <div class="result-card">
              <div class="result-label">Você pagará aproximadamente</div>
              <div class="result-value">{format_money(total, payment_code)}</div>
              <div class="result-rate">
                Para comprar {format_money(decimal_amount, buy_code)}<br>
                1 {buy_code} = {format_money(current_quote.ask, payment_code)}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        first_metric, second_metric, third_metric = st.columns(3)
        first_metric.metric("Máxima", format_money(current_quote.high, payment_code))
        second_metric.metric("Mínima", format_money(current_quote.low, payment_code))
        third_metric.metric("Variação", f"{current_quote.pct_change}%")
        st.caption(f"Cotação: {current_quote.name} • Atualizada em {current_quote.created_at}")

st.caption("Dados fornecidos pela AwesomeAPI. Valores meramente informativos.")
