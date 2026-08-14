import requests

resposta = requests.get(
    "http://localhost:9090/api/v1/query",
    params={"query": "up"},
)

dados = resposta.json()
print(dados)