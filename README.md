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
- `plan()` — o agente organiza esse dado e consulta um modelo de IA (Groq/Llama) pra obter
  uma análise ou diagnóstico.
- `act()` — o agente reporta a sugestão, **sempre em modo aprovação humana** — nenhum agente
  executa ação nenhuma sozinho neste projeto.

Qualquer agente novo herda dessa base e só precisa implementar esses três métodos com sua
lógica específica — o ciclo de execução (`run()`) e o registro de sugestões
(`registrar_sugestao()`) já vêm prontos, compartilhados por todos.

## Agentes implementados

- **Agente de Triagem de Incidentes** (`agente_triagem_incidentes.py`) — lê alertas do
  banco, aponta causa provável e próximo passo.
- **Agente de Backup & DR Verification** (`agente_backup.py`) — lê o status das rotinas de
  backup simuladas, aponta falhas e sugere ação.

Todas as sugestões geradas ficam registradas na tabela `sugestoes_pendentes` e podem ser
revisadas de uma vez com `painel.py`.

## Stack

- Python 3.12
- Docker + Docker Compose (Postgres, Prometheus, Grafana)
- Groq API (Llama 3.3 70B) para as chamadas de IA
- Postgres como fonte de dados do ambiente-demo

## Como rodar

```bash
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Cria um `.env` na raiz com:

GROQ_API_KEY=sua_chave_aqui

Sobe a infraestrutura:
```bash
docker compose up -d
```

Cria as tabelas e dados de exemplo:
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

## Status e próximos passos

- [x] Ambiente-demo (Postgres, Prometheus, Grafana) via Docker
- [x] Kernel com contrato perceive/plan/act
- [x] Agente de Triagem de Incidentes
- [x] Agente de Backup & DR Verification
- [x] Registro compartilhado de sugestões + painel de revisão
- [ ] Conectar métricas do Prometheus a algum agente (hoje ele está no ar, mas nenhum agente
      ainda o consulta)
- [ ] Fluxo de aprovação/rejeição real das sugestões (hoje só lista, não marca como
      aprovado)
- [ ] Outros agentes candidatos documentados: Cost/FinOps, Security & Patch Compliance,
      Deployment Health, Infra-as-Code Review, Documentation/Runbook

## Aprendizado

Este foi meu primeiro projeto de IA aplicada, construído do zero — incluindo Python, Docker,
Git e os fundamentos de agentes de LLM. Decisões e processo de aprendizado documentados em
`LEARNING_LOG.md`.