# Decision Log

## 2026-08-17 — Adoção do Product Blueprint V2 como documento canônico

**Contexto:** o projeto era um kernel experimental de aprendizado (3 agentes, aprovação humana via CLI). Foi entregue um blueprint (SMB/MSP Operational Intelligence Product Blueprint V2) redefinindo o objetivo como produto vendável de Operational Intelligence para times de TI enxutos e MSPs.

**Decisão:** adotar o blueprint como documento governante. Construção reordenada em 8 estágios: Kernel Trust Foundation → Investigation Engine → Eval Harness → Risk+Approval+Audit → Action+Verification → Memory → Product Layer → Commercial Agent Packs. Não criar novos agentes verticais até essas fundações existirem.

**Evidência/justificativa:** o blueprint aponta lacunas concretas no estado atual (credenciais hardcoded, ausência de output estruturado, ausência de testes) que bloqueiam qualquer venda real do produto — não é preferência estética, é pré-requisito de confiança comercial.

**Alternativas consideradas:** continuar adicionando agentes verticais (rejeitado — cresce a superfície sem resolver os problemas de confiança/qualidade da fundação).

## 2026-08-17 — Eliminação de credenciais hardcoded

**Contexto:** `kernel/agent.py` e mais 6 arquivos tinham usuário/senha/host do Postgres escritos diretamente no código; a chave da Groq também era lida solta de `os.environ` em cada arquivo.

**Decisão:** criar `kernel/config.py` como única fonte de configuração (lê `.env` via `python-dotenv`, expõe `settings`). Todos os arquivos passam a importar `settings` em vez de repetir valores ou lógica de leitura de ambiente.

**Evidência/justificativa:** critério de aceite explícito do Stage 1 do blueprint ("nenhuma credencial hardcoded"). Validado por busca (`demo123`) restrita a `.env`/`docker-compose.yml`, e por execução real dos 3 agentes sem erro.

**Efeito colateral descoberto:** durante a validação, o modelo `llama-3.3-70b-versatile` da Groq foi desativado (16/08/2026). Migrado para `openai/gpt-oss-120b` nos 3 agentes.

## 2026-08-17 — Introdução do Tool Registry (Postgres)

**Contexto:** `agente_triagem_incidentes.py` e `agente_backup.py` tinham lógica de conexão/query ao Postgres duplicada, cada um com sua própria chamada `psycopg2.connect(...)` dentro do `perceive()`.

**Decisão:** criar `kernel/tools.py` (contrato abstrato `Tool`) e `tool_postgres_query.py` (`PostgresQueryTool`, implementação concreta reutilizável). Os dois agentes agora chamam a mesma Tool, cada um só fornecendo sua própria query SQL.

**Evidência/justificativa:** duplicação real entre 2 agentes eliminada; Tool Registry é pré-requisito do Investigation Engine (Stage 2), que precisa escolher fontes de dado dinamicamente por hipótese.

**Escopo explicitamente adiado:** não foi criada uma Tool pra Prometheus — `agente_infra.py` é o único consumidor daquela fonte hoje, sem duplicação a resolver. Vira Tool quando houver um segundo consumidor real.

## 2026-08-17 — Outputs estruturados (Finding)

**Contexto:** os 3 agentes devolviam sugestão em texto livre (`{"sugestao": "..."}`), impossível de filtrar, comparar ou avaliar automaticamente.

**Decisão:** criar `kernel/schemas.py` com o dataclass `Finding` (causa_provavel, confianca, proxima_acao). Os 3 agentes agora pedem resposta em JSON à Groq (`response_format={"type": "json_object"}`), parseiam pro `Finding`, e `registrar_sugestao` persiste os 3 campos em colunas próprias na tabela `sugestoes_pendentes` (schema recriado).

**Evidência/justificativa:** item explícito do Stage 1 do blueprint; pré-requisito do Eval Harness (Stage 3), que precisa comparar sugestões de forma automatizada, não só ler texto.

**Limitação conhecida e registrada:** o campo `confianca` é autoavaliação do modelo, não uma métrica calibrada — não há hoje evidência de que "alta confiança" correlaciona com sugestões corretas. É exatamente isso que o Eval Harness vai medir mais pra frente.

## 2026-08-17 — Testes automatizados básicos (fecha Stage 1)

**Contexto:** o projeto não tinha nenhum teste automatizado; toda verificação era manual, rodando cada agente e lendo a saída.

**Decisão:** introduzir pytest, restrito à pasta `tests/` (via `testpaths` no `pyproject.toml`) para não colidir com os scripts legados `test_*.py` da raiz, que não são testes automatizados de verdade. Primeiro teste cobre o contrato mais crítico do projeto: `Agent.run()` chama `perceive/plan/act` em ordem — sem depender de banco, API ou infraestrutura externa.

**Evidência/justificativa:** critério de aceite explícito do Stage 1; dois bugs reais nesta sessão (indentação quebrando métodos abstratos) só foram pegos rodando manualmente — um teste automatizado pegaria isso sem depender de lembrar de rodar.

**Efeito:** Stage 1 (Kernel Trust Foundation) do blueprint está completo.

## 2026-08-18 — Primeira fatia do Investigation Engine (cruzamento de evidência)

**Contexto:** agentes decidiam com base numa fonte só de dado (ex.: só alertas), sem checagem
cruzada. Isso deixava o campo `confianca` sem lastro real (limitação já registrada no marco
de outputs estruturados).

**Decisão:** criar `tool_prometheus_query.py` (`PrometheusUpTool`), reaproveitada tanto pelo
`agente_infra.py` (substituindo a chamada direta a `requests`) quanto pelo
`agente_triagem_incidentes.py`, que agora consulta essa segunda fonte antes de concluir. O
cruzamento em si (bater o serviço do alerta com os alvos monitorados) é feito pelo modelo via
instrução no prompt, não por lógica Python — escolha deliberada de simplicidade em troca de
previsibilidade.

**Evidência/justificativa:** validado ao vivo — o mesmo alerta que antes gerava confiança
"alta" (sugestão #1) passou a gerar confiança "baixa" (sugestão #5) depois de cruzar com o
Prometheus, onde `api-pagamentos` não está monitorado.

**Limitação observada:** o modelo ajustou a confiança corretamente, mas nem sempre cita
explicitamente a falta de monitoramento na causa provável, mesmo instruído a fazer isso. Fica
registrado como candidato a métrica do Eval Harness (Stage 3), não como bug a corrigir agora.

## 2026-10-15 — Stage 1 reaberto: estava parcial, não completo

**Contexto:** a entrada de 17/08 declarou o Stage 1 completo. Uma auditoria em 15/10 comparou o código com os acceptance criteria do Blueprint v2.0 (seção 30) e encontrou lacunas.

**Decisão:** reabrir o Stage 1 e só fechá-lo quando os 4 critérios do Blueprint forem atendidos.

**Evidência:**
- *Credenciais:* atendido no código, mas `docker-compose.yml` ainda tem `POSTGRES_PASSWORD: demo123`.
- *Finding/Hypothesis/Recommendation persistidos:* não atendido. O `Finding` atual é a conclusão do LLM, não evidência; Hypothesis, Recommendation e Evidence Store não existem.
- *Tools read-only padronizados:* parcial. `PostgresQueryTool` executa qualquer SQL (nada impede DELETE/DROP), sem timeout; URL do Prometheus fixa no código.
- *Testes básicos:* atendido (1 teste do contrato `run()`).

**Alternativas consideradas:** seguir para o Stage 2 com a fundação incompleta (rejeitado: o Investigation Engine precisa registrar evidência a favor/contra hipóteses, e não existe tipo de evidência).

**Reversão:** o Stage 1 fecha quando os 4 critérios estiverem atendidos e validados por teste.

## 2026-10-20 — Correção do requirements.txt

**Contexto:** ao clonar o repo numa máquina nova (15/10), `pip install -r requirements.txt` falhou.

**Decisão:** remover a linha que instalava o próprio projeto, adicionar `pytest` com versão fixa e regravar o arquivo em UTF-8. O kernel passa a ser instalado em modo editável por comando separado (`pip install -e .`).

**Evidência:** o arquivo foi gerado com `pip freeze` enquanto o kernel estava instalado em modo editável; o freeze registrou `-e git+...@7c69521`, commit anterior ao `pyproject.toml`, e o pip não encontrava um projeto Python ali. O `pytest` não constava na lista. O arquivo estava em UTF-16 (padrão do `>` no PowerShell). Na máquina antiga o erro nunca apareceu porque o ambiente nunca tinha sido montado do zero a partir do arquivo.

**Alternativas consideradas:** manter o arquivo e instalar manualmente (rejeitado: o projeto deixa de ser reproduzível em outra máquina).

**Reversão:** se o `requirements.txt` for regenerado, usar `pip freeze --exclude-editable`.

## 2026-10-20 — Porta do Postgres configurável via .env

**Contexto:** na máquina nova, o Python conectava num PostgreSQL 18 instalado no Windows (serviço `postgresql-x64-18`), também escutando na porta 5432, em vez do container. A recusa veio em português e o psycopg2 a exibiu como `UnicodeDecodeError`, mascarando o erro real (autenticação recusada).

**Decisão:** mudar o mapeamento para `"${PG_PORT:-5432}:5432"`. A porta do lado do host vem de `PG_PORT` no `.env` (o mesmo valor que o `kernel/config.py` já lia); a porta interna do container continua 5432.

**Evidência:** `netstat -ano | findstr :5432` mostrou dois processos escutando (o Postgres do Windows e o Docker). Com `PG_PORT=5433`, conexão e agentes funcionaram.

**Alternativas consideradas:** parar o serviço do Postgres local (rejeitado: exige admin na máquina corporativa e volta a subir no reboot).

**Reversão:** sem conflito na máquina, basta não definir `PG_PORT`; o padrão continua 5432.

## 2026-10-20 — Remoção do Grafana do ambiente-demo

**Contexto:** o Grafana foi adicionado na fase de aprendizado, por sugestão numa conversa que não foi registrada. Na máquina nova, a porta 3000 já estava ocupada e o serviço não subiu.

**Decisão:** remover o serviço `grafana` e o volume `grafana_data` do `docker-compose.yml`.

**Evidência:** busca por "grafana" e "3000" em todos os `.py` não encontrou uso; após a remoção, o agente de triagem rodou de ponta a ponta normalmente.

**Alternativas consideradas:** mudar a porta do Grafana (rejeitado: mantém uma peça sem função, que adiciona atrito a quem clona o projeto).

**Reversão:** reintroduzir se o Executive View (Blueprint, seção 25) precisar de dashboard, com justificativa registrada aqui.

## 2026-10-20 — Evidence: separação entre fato observado e conclusão do LLM

**Contexto:** o agente de triagem enviava texto cru ao LLM e deixava a comparação alerta × Prometheus a cargo do modelo. Em 18/08 foi registrado que o modelo "nem sempre" citava a falta de monitoramento.

**Decisão:** criar a dataclass `Evidence` (tipo, fonte, timestamp, assunto, observacao). Evidências são produzidas por funções puras em Python (`alertas_para_evidencias`, `alvos_para_evidencias`), testadas sem banco nem rede. O `perceive()` coleta e transforma; o `plan()` só monta o prompt a partir das evidências. O fato "serviço não monitorado" passa a ser produzido pelo Python, não pelo LLM.

**Evidência:** 4 testes automatizados passando, inclusive com o Docker desligado. Experimento manual (3 execuções por versão de prompt):
- Prompt A: cita monitoramento na causa 3/3; confiança media 3/3; trata falta de monitoramento como causa do timeout 2/3.
- Prompt B (adotado): cita monitoramento na causa 0/3 (só na próxima ação); confiança media/alta/media; trata como causa 0/3.

**Alternativas consideradas:** continuar ajustando o prompt manualmente (rejeitado: cada ajuste corrigiu um comportamento e piorou outro; amostra de 3 execuções não permite conclusão confiável). Prompt B adotado porque inventar uma causa é mais perigoso do que omitir uma informação.

**Limitações conhecidas:**
- A comparação usa o nome do serviço do alerta = nome do job no Prometheus; nomes diferentes gerariam falso "não monitorado".
- A confiança continua sendo autoavaliação do LLM e ignorou a instrução nas 6 execuções. Candidato a primeiro item do Stage 2: regra determinística (serviço sem monitoramento → confiança no máximo baixa), com teste.
- Alertas duplicados no banco levaram o LLM a falar em "múltiplos timeouts".
- O agente sugere "reiniciar" (ação mutante) mesmo com confiança não alta, em 4/6 execuções. Caso para o Eval Harness e o Risk Engine.

**Reversão:** revisar o prompt quando o Eval Harness permitir comparar versões com amostra maior.

## 2026-10-21 — PostgresQueryTool read-only de verdade

**Contexto:** a classe `Tool` diz que tools são read-only, mas nada garantia isso. A `PostgresQueryTool` executava qualquer SQL, não tinha limite de tempo e deixava a conexão aberta quando dava erro.

**Decisão:** três proteções na Tool:
- `conn.set_session(readonly=True)`: o próprio Postgres recusa escrita;
- `statement_timeout=5000`: consultas acima de 5 segundos são canceladas;
- `try/finally`: a conexão fecha sempre, mesmo com erro.

**Evidência:** teste `test_postgres_tool_recusa_escrita` falhou antes da correção (o banco aceitou um DELETE) e passou depois. Teste `test_postgres_tool_cancela_consulta_lenta` falhou antes (a consulta rodou os 10s inteiros) e passou depois. Agente de triagem continua funcionando.

**Alternativas consideradas:** bloquear palavras como DELETE/DROP no texto da query (rejeitado: fácil de burlar; o banco sabe o que cada comando faz, o Python só vê texto).

**Sem teste para o try/finally:** testar conexão vazando é complexo e a mudança é pequena e conhecida.

**Observação:** antes da correção, escritas eram desfeitas por acidente, porque a Tool nunca fazia `commit()`. A proteção existia por acaso, não por projeto.

**Reversão:** o timeout de 5s pode ser ajustado se consultas legítimas de investigação precisarem de mais tempo.