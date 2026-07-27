##Postgres via Docker (27/07/2026)

Se eu precisar de um banco/serviço novo em outro projeto, os passos genéricos são: 

1 escolher o banco ideal para o projeto 

2 ver qual é a biblioteca python espeficica do banco escolhido

3 Escrever a "receita" desse serviço no docker-compose.yml (imagem, usuário, senha, porta)

4 Subir com `docker compose up -d` e confirmar que está rodando com `docker ps`

5 Escrever um código Python importando a biblioteca e passando usuário, senha e porta pra conectar