# Câmbio Fácil — Conversor com AwesomeAPI

Aplicação web desenvolvida em Python e Streamlit para descobrir quanto é necessário pagar ao comprar determinado montante de uma moeda estrangeira.

## Problema resolvido

As taxas de câmbio mudam constantemente e calcular manualmente o custo de uma compra pode gerar erros. O Câmbio Fácil consulta a cotação atual, apresenta somente combinações realmente disponíveis e calcula o valor estimado do pagamento em tela.

## Funcionalidades

- carrega dinamicamente as moedas e os pares disponíveis;
- permite escolher a moeda que será comprada;
- mostra apenas moedas de pagamento compatíveis;
- consulta a cotação mais recente ao solicitar a conversão;
- calcula o custo pela taxa de venda (`ask`);
- exibe máxima, mínima e variação diária;
- trata falhas de conexão, timeout e respostas inválidas;
- salva em `data/moedas.json` um snapshot dos pares retornados pela API.

## API utilizada

A [AwesomeAPI — API de Cotações](https://docs.awesomeapi.com.br/api-de-moedas) fornece cotações de mais de 150 moedas. O projeto utiliza:

- `GET /xml/available/uniq`: códigos e nomes das moedas;
- `GET /xml/available`: combinações de moedas aceitas;
- `GET /json/last/{MOEDA-PAGAMENTO}`: cotação mais recente do par.

A lista é disponibilizada em XML e a cotação em JSON. O módulo `awesomeapi.py` transforma essas respostas em objetos Python antes de serem usadas pela interface.

## Como executar

Requer Python 3.10 ou superior.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

No Windows, ative o ambiente com `.venv\\Scripts\\activate`.

## Testes

Os testes não acessam a internet: eles simulam respostas da API.

```bash
python -m unittest discover -s tests -v
```

## Estrutura

```text
.
├── app.py                 # interface Streamlit
├── awesomeapi.py          # cliente HTTP e regra de conversão
├── data/moedas.json       # dados obtidos da API
├── tests/test_awesomeapi.py
├── requirements.txt
└── README.md
```

## Regra da conversão

Para comprar a moeda-base, a aplicação utiliza a taxa `ask` (venda):

```text
valor a pagar = montante desejado × cotação de venda
```

Exemplo: para comprar `100 USD` com cotação de venda de `5,12 BRL`, o valor estimado é `512,00 BRL`.

Os valores são informativos e podem variar entre a consulta e uma operação financeira real.
