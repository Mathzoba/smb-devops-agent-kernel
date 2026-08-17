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