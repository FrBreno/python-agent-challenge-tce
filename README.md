# Python Agent Challenge - Backend com Orquestração + Tool + LLM

## Objetivo da solução

Entregar uma API simples e funcional com fluxo:

1. receber messagem do usuário via `POST /messages`.
2. consulta contexto na KB via tool HTTP.
3. avalia suficiência de contexto e decide fallback se necessário.
4. chama LLM com pergunta + contexto.
5. retorna `answer` e `sources`.

Com fallback obrigatório quando não houver contexto suficiente.

## Arquitetura

Estrutura principal:

- app/main.py
- app/api/routes.py
- app/api/schemas.py
- app/core/orchestrator.py
- app/core/constants.py
- app/tools/kb_tool.py
- app/llm/base.py
- app/llm/factory.py
- app/llm/system_prompt.py
- app/llm/providers/base_http_client.py
- app/llm/providers/gemini_client.py
- app/llm/providers/openai_client.py

Responsabilidades:

- API Layer:
  - valida entrada;
  - expõe POST /messages;
  - mantém contrato de resposta.

- Orchestrator:
  - coordena o fluxo;
  - decide fallback;
  - decide quais seções entram em sources;
  - chama cliente LLM.

- KB Tool:
  - faz GET da KB_URL via HTTP;
  - valida resposta de rede;
  - parseia Markdown em seções;
  - calcula relevância e score (Ranking);
  - devolve contexto estruturado.

- LLM Layer:
  - abstração por interface;
  - factory por LLM_PROVIDER;
  - providers Gemini e OpenAI;
  - prompt compartilhado centralizado em módulo Python.

## Regras de decisão do fluxo

1. A tool sempre faz retrieval de contexto na KB.
2. Se o contexto for vazio ou score insuficiente, retorna fallback.
3. Se houver contexto suficiente, chama LLM.
4. Sources inclui apenas seções efetivamente usadas.
5. Fallback literal obrigatório:

```
"Não encontrei informação suficiente na base para responder essa pergunta."
```
## Contrato da API

Endpoint:
POST /messages

Request mínimo:

~~~json
{
  "message": "O que é composição?"
}
~~~

Request com sessão (opcional):

~~~json
{
  "message": "Pode resumir a resposta anterior?",
  "session_id": "sessao-123"
}
~~~

Response de sucesso:

~~~json
{
  "answer": "Texto de resposta",
  "sources": [
    { "section": "Composição" }
  ]
}
~~~

Response de fallback:

~~~json
{
  "answer": "Não encontrei informação suficiente na base para responder essa pergunta.",
  "sources": []
}
~~~

## Configuração por ambiente

Use arquivo .env com, no mínimo:

~~~dotenv
KB_URL=https://raw.githubusercontent.com/igortce/python-agent-challenge/refs/heads/main/python_agent_knowledge_base.md

LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
LLM_API_KEY=
LLM_BASE_URL=
LLM_TIMEOUT_SECONDS=30

MAX_MESSAGE_CHARS=4000
MIN_SECTION_SCORE=1
MAX_CONTEXT_SECTIONS=3
KB_TIMEOUT_SECONDS=10

LOG_LEVEL=INFO

MEMORY_STORE=
HOST=0.0.0.0
PORT=8000
~~~

Observações:
- LLM_PROVIDER aceita gemini ou openai.
- A troca de provider é feita apenas por configuração, sem mudança de código.
- Para submissão final, KB_URL deve apontar para a URL oficial do desafio.

## Execução local (sem Docker)

1. criar e ativar ambiente virtual
2. instalar dependências
3. iniciar API

~~~bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
~~~

## Execução com Docker Compose

~~~bash
docker compose up -d --build
docker compose ps
docker compose logs -f api
~~~

Parar ambiente:

~~~bash
docker compose down
~~~

## Exemplos de teste

Sucesso com contexto:

~~~bash
curl -X POST "http://localhost:8000/messages" \
  -H "Content-Type: application/json" \
  -d '{"message":"O que é composição?"}'
~~~

Fallback sem contexto:

~~~bash
curl -X POST "http://localhost:8000/messages" \
  -H "Content-Type: application/json" \
  -d '{"message":"Pergunta fora do escopo da KB"}'
~~~

## Estado atual da implementação

Concluído:
- endpoint único POST /messages;
- tool de KB via HTTP com parse e ranking;
- orquestração com fallback obrigatório;
- integração real com LLM no fluxo principal;
- abstração multi-provider com Gemini e OpenAI;
- prompt centralizado e compartilhado;
- docker compose funcional.

Ainda opcional:
- memória por session_id com TTL;
- suíte de testes automatizados mais abrangente;
- Makefile de automação.

## Critérios atendidos

- contrato de entrada e saída;
- answer e sources com section;
- fallback literal em ausência de contexto;
- KB via URL oficial por configuração;
- separação de responsabilidades;
- provider LLM configurável por ambiente.