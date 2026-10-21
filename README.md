# SMB DevOps Agent Kernel

Base multiagente customizável para automação de operações (DevOps) em pequenas e médias
empresas (PMEs), construída como projeto de aprendizado prático — do zero em Python, Docker
e agentes de IA.

## O problema

PMEs raramente têm equipe de DevOps/SRE dedicada. Quando algo quebra — um alerta dispara,
um backup falha silenciosamente — normalmente não existe um processo estruturado nem uma
pessoa dedicada pra tratar isso rapidamente. As soluções agenticas de operações do mercado
(AWS DevOps Agent, Azure SRE Agent) são enterprise-first: pesadas e caras. Este projeto
constrói uma base leve e customizável, pensada pro porte de uma PME.

## Como funciona

O núcleo do projeto é um **kernel** (`kernel/agent.py`) que define um contrato comum que
todo agente segue: **perceive → plan → act**.

- `perceive()` — cada agente coleta o dado que precisa observar (ex.: alertas, backups).
- `plan()` — o agente organiza esse dado e consulta um modelo de IA (Groq) pra obter
  uma análise ou diagnóstico.
- `act()` — o agente reporta a sugestão, **sempre em modo aprovação humana** — nenhum agente
  executa ação nenhuma sozinho neste projeto.

O acesso a dado é feito através de **Tools** (`kernel/tools.py`) — componentes read-only
reutilizáveis entre agentes (ex.: `PostgresQueryTool`), em vez de cada agente reimplementar
sua própria conexão. O resultado da análise de cada agente é um **Finding** estruturado
(`kernel/schemas.py`: causa provável, nível de confiança, próxima ação), não mais texto livre.

Qualquer agente novo herda dessa base e só precisa implementar esses três métodos com sua
lógica específica — o ciclo de execução (`run()`) e o registro de sugestões
(`registrar_sugestao()`) já vêm prontos, compartilhados por todos.

## Agentes implementados

- **Agente de Triagem de Incidentes** (`agente_triagem_incidentes.py`) — lê alertas do
  banco, aponta causa provável e próximo passo.
- **Agente de Backup & DR Verification** (`agente_backup.py`) — lê o status das rotinas de
  backup simuladas, aponta falhas e sugere ação.
- **Agente de Infraestrutura** (`agente_infra.py`) — consulta métricas do Prometheus (via
  API HTTP) e reporta a saúde dos serviços monitorados.

Todas as sugestões geradas ficam registradas na tabela `sugestoes_pendentes`, podem ser
revisadas com `painel.py`, e aprovadas ou rejeitadas diretamente por ali.

## Stack

- Python 3.12
- Docker + Docker Compose (Postgres, Prometheus)
- Groq API (openai/gpt-oss-120b) para as chamadas de IA
- Postgres como fonte de dados do ambiente-demo
- pytest para testes automatizados do kernel

## Como rodar

Requer Python 3.12 (`py install 3.12` no Windows, se não tiver) e Docker Desktop.

```bash
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

Copie `.env.example` para `.env` e preencha `GROQ_API_KEY` e `PG_PASSWORD`
(no ambiente-demo, use `demo123`).

Se já existir um PostgreSQL instalado na máquina usando a porta 5432, defina outra porta
no `.env` (ex.: `PG_PORT=5433`). O Docker e o código leem esse mesmo valor.

Sobe a infraestrutura (Postgres e Prometheus):
```bash
docker compose up -d
```

Cria as tabelas e dados de exemplo (rodar uma vez só; rodar de novo duplica os dados):
```bash
python test_db.py
python test_backups.py
python criar_tabela_sugestoes.py
```

Roda os agentes e o painel:
```bash
python agente_triagem_incidentes.py
python agente_backup.py
python painel.py
```

Roda os testes automatizados do kernel:
```bash
pytest
```

## Status e próximos passos

O projeto segue o Product Blueprint V2 como documento canônico, evoluindo de kernel
experimental para produto de Operational Intelligence. Construção em 8 estágios:

- [ ] **Stage 1 — Kernel Trust Foundation** (reaberto em 15/10 — ver DECISION_LOG)
- [ ] Stage 2 — Investigation Engine
- [ ] Stage 3 — Eval Harness
- [ ] Stage 4 — Risk + Approval + Audit
- [ ] Stage 5 — Action + Verification
- [ ] Stage 6 — Memory
- [ ] Stage 7 — Product Layer
- [ ] Stage 8 — Commercial Agent Packs

Decisões e justificativas de cada etapa em [`DECISION_LOG.md`](DECISION_LOG.md).
Agentes verticais candidatos (fora de escopo até o Stage 8) documentados em
[`AGENTES_ROADMAP.md`](AGENTES_ROADMAP.md).

## Segurança / Configuração

Todas as credenciais (Postgres, Groq) são lidas de variáveis de ambiente via
`kernel/config.py`, nunca hardcoded no código. Para rodar localmente, copie `.env.example`
para `.env` e preencha os valores.

## Aprendizado

Este foi meu primeiro projeto de IA aplicada, construído do zero — incluindo Python, Docker,
Git e os fundamentos de agentes de LLM. Decisões e processo de aprendizado documentados em
`LEARNING_LOG.md`.