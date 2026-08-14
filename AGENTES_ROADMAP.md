# Roadmap de Agentes

Especificação dos agentes candidatos ainda não implementados, seguindo o mesmo contrato
`perceive/plan/act` do kernel. Todos, sem exceção, reportam em modo sugestão — nenhum
executa ação mutante sozinho.

## Cost/FinOps Optimization Agent

**Problema:** PMEs frequentemente pagam por recursos de nuvem superdimensionados ou
esquecidos, sem visibilidade clara de onde o dinheiro está sendo gasto.

- `perceive`: consultaria dados de uso/custo de nuvem (ex.: API de billing do provedor).
- `plan`: pediria à IA pra identificar recursos subutilizados ou picos de custo anormais.
- `act`: reportaria sugestões de economia, pendente de aprovação — mudança de infra custa
  dinheiro real, nunca é automática.

## Security & Patch Compliance Agent

**Problema:** PMEs raramente têm alguém dedicado a rastrear vulnerabilidades e patches
pendentes, ficando expostas por meses sem saber.

- `perceive`: consultaria as dependências instaladas e cruzaria com uma base de
  vulnerabilidades conhecidas.
- `plan`: pediria à IA pra priorizar quais vulnerabilidades são mais críticas.
- `act`: reportaria a lista priorizada, pendente de aprovação — aplicar patch pode quebrar
  sistema em produção.

## Deployment Health & Rollback Agent

**Problema:** depois de um deploy, ninguém monitora ativamente se a saúde da aplicação
piorou, até um cliente reclamar.

- `perceive`: consultaria métricas pós-deploy (taxa de erro, latência), comparando antes e
  depois do deploy mais recente.
- `plan`: pediria à IA pra avaliar se o deploy parece ter piorado a saúde do sistema.
- `act`: reportaria a recomendação (ex.: considerar rollback), pendente de aprovação — nunca
  reverte nada sozinho.

## Infra-as-Code Review Agent

**Problema:** mudanças de infraestrutura (Terraform/Ansible) costumam ser aplicadas sem
revisão cuidadosa, criando risco de erro caro.

- `perceive`: leria o diff de um arquivo de infraestrutura antes de ser aplicado.
- `plan`: pediria à IA pra revisar o diff em busca de riscos (ex.: exclusão acidental de
  recurso crítico).
- `act`: reportaria os riscos encontrados, pendente de aprovação antes de aplicar a mudança.

## Documentation/Runbook Agent

**Problema:** conhecimento operacional fica concentrado numa única pessoa; quando ela sai
ou tira férias, ninguém sabe operar o sistema.

- `perceive`: leria o estado atual da infraestrutura e o histórico de incidentes resolvidos.
- `plan`: pediria à IA pra gerar ou atualizar um rascunho de runbook baseado nesse estado.
- `act`: reportaria o rascunho, pendente de revisão humana antes de publicar oficialmente.