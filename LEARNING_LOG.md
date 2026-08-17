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

## Terceiro agente - fonte de dado via API HTTP (dd/mm/aaaa)
Conectei o Prometheus usando a biblioteca requests, consultando a API HTTP dele (diferente
do padrão SQL usado nos outros agentes). Só o perceive() mudou - plan() e act() continuam
idênticos aos outros agentes. Isso prova que o kernel realmente não se importa com a fonte
do dado, só com o formato que cada agente devolve.

## Aprendizado de segurança
Com a senha espalhada em 8 arquivos, bastava esquecer de atualizar 1 deles pra criar inconsistência ou vazar credencial num commit futuro. Com um único config.py, existe um só lugar pra proteger, revisar e trocar. 

O erro do modelo do Groq só apareceu pois antes os arquivos agente_backup.py e agente_infra.py já tinham código pronto há um tempo, mas ninguém tinha executado pra confirmar que ainda funcionavam. código que não roda não é código que funciona 

## Bug Tool
A PostgresQueryTool não sabe (nem precisa saber) se a query é sobre backups ou alertas — ela só devolve linhas. Quem traduz isso pro vocabulário do agente é o perceive() de cada um."

Query é o pedido que você manda pro banco de dados pedindo um dado específico

## Outputs estruturados — Finding (17/08/2026)

Antes, os agentes devolviam a sugestão como um texto solto, tipo um parágrafo que só um humano lia. Isso funcionava pra aprovar no painel, mas não dava pra comparar sugestões entre si, filtrar por gravidade ou medir se o agente estava acertando ao longo do tempo — era só string, não dado.

Com o `Finding` (causa_provavel, confianca, proxima_acao), a IA agora responde em JSON, e esse JSON vira um objeto Python de verdade, salvo em colunas separadas no banco. Isso é o que permite, no futuro, perguntas tipo "quantas sugestões de alta confiança foram aprovadas?" — coisa que com texto livre seria impossível responder sem reler tudo manualmente.

Um ponto importante que discutimos: o campo `confianca` não é uma métrica calculada de verdade — é a própria IA "achando" o quanto ela confia na resposta dela, sem checar nada de fato. Isso é uma limitação conhecida dos modelos de linguagem, não um bug meu. Por enquanto esse campo é uma hipótese: a gente ainda não sabe se "alta confiança" realmente significa "mais correto". É pra isso que vai servir o Eval Harness mais pra frente — comparar, com dados reais, se esse número significa alguma coisa ou se é só decoração.