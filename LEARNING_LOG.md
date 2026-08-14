##Postgres via Docker (27/07/2026)

Se eu precisar de um banco/serviço novo em outro projeto, os passos genéricos são: 

1 escolher o banco ideal para o projeto 

2 ver qual é a biblioteca python espeficica do banco escolhido

3 Escrever a "receita" desse serviço no docker-compose.yml (imagem, usuário, senha, porta)

4 Subir com `docker compose up -d` e confirmar que está rodando com `docker ps`

5 Escrever um código Python importando a biblioteca e passando usuário, senha e porta pra conectar

## Prometheus + volumes

Aprendi que nem toda imagem docker se configura do mesmo jeito - Postgres usa váriaveis de ambiente(usuário/senha), prometheus usa um arquivo de configuração emprestado do meu pc pro container através de volumes. Regra geral: sempre conferir na documentação da imagem o docker hub anes de assumir como ela se configura 

## Kernel com ABC (04/08/2026)
Aprendi a usar classe abstrata (ABC) em Python pra forçar um contrato comum entre agentes
diferentes. Cada agente futuro só precisa implementar perceive/plan/act com sua lógica
específica — o "run()" que orquestra a ordem já vem pronto da classe base, e o Python
recusa criar um agente que não implemente todos os métodos obrigatórios.

## Checklist pra entender qualquer código novo:
1 O que essa linha faz, isolada? (mecânica — o "o quê")
2 Por que ela está aqui, que problema ela resolve? (propósito — o "por quê", o mais importante e o mais fácil de pular)
3 O que quebraria se eu tirasse essa parte? (testar na pratica)
4 Eu consigo explicar isso pra alguém em uma frase, sem usar os termos técnicos do código? (se não consigo, ainda não entendi de verdade)

## Primeiro agente real (04/08/2026)
Consegui rodar o Agente de Triagem de Incidentes de ponta a ponta: ele lê alertas reais do
Postgres, manda pra IA analisar, e imprime a sugestão sem executar nada sozinho. Ainda não
consigo recriar esse arquivo sozinho do zero, mas entendo a lógica como uma história (coletar
evidência -> consultar especialista -> reportar pro chefe). O teste de verdade vem no próximo
agente (Backup), quando vou tentar escrever primeiro, antes de pedir ajuda.

## Painel de sugestões (14/08/2026)
Criei um script que lista as sugestões pendentes filtrando por status ('pendente') e
formatando pra leitura. Aprendi a usar WHERE num SELECT pra filtrar linhas, em vez de
sempre trazer a tabela inteira.