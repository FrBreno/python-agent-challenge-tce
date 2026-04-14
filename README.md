# Python Agent Challenge - Backend com Orquestração + Tool + LLM

## Objetivo da solução

Entregar uma API simples e funcional com fluxo:

1. receber mensagem do usuário via `POST /messages`.
2. consulta contexto na KB via tool HTTP.
3. avalia suficiência de contexto e decide fallback se necessário.
4. chama LLM com pergunta + contexto.
5. retorna `answer` e `sources`.

Com fallback obrigatório quando não houver contexto suficiente.

---

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

### Responsabilidades

**API Layer**
  - valida entrada
  - expõe `POST /messages`
  - mantém contrato de resposta

**Orchestrator**
  - coordena o fluxo
  - decide fallback
  - define quais seções entram em `sources`
  - chama cliente LLM

**KB Tool**
  - faz GET da `KB_URL` via HTTP
  - valida resposta de rede
  - parseia Markdown em seções
  - calcula relevância (ranking lexical)
  - devolve contexto estruturado

**LLM Layer**
  - abstração por interface
  - factory baseada em `LLM_PROVIDER`
  - providers Gemini e OpenAI
  - composição de prompt centralizada

---

## Regras de decisão do fluxo

Resumo das regras aplicadas (sem expor prompt completo):

1. **Quando chamar a tool**
  - o fluxo sempre consulta a tool para buscar contexto na KB antes de decidir a resposta.

2. **Quais partes do contexto entram no LLM**
  - entram apenas as seções recuperadas como relevantes no ranking;
  - `sources` inclui somente seções realmente usadas na resposta.

3. **Quando retornar fallback**
  - retorna fallback quando não houver contexto suficiente (ex.: contexto vazio ou score abaixo do limiar).

Fallback literal obrigatório:

```
"Não encontrei informação suficiente na base para responder essa pergunta."
```

---

## Decisões técnicas

- FastAPI foi escolhido pela simplicidade de desenvolvimento de API e validação com Pydantic.
- A arquitetura foi separada em camadas (API, orquestração, tool de KB e cliente LLM) para manter responsabilidade única e facilitar testes.
- A integração de LLM usa abstração por interface + factory, permitindo troca de provider (`gemini`/`openai`) apenas por variável de ambiente.
- A busca na KB fica fora do LLM, com ranking lexical controlado no backend para reduzir respostas fora de contexto.

---

## Contrato da API

**Endpoint**  
`POST /messages`

### Request mínimo

```json
{
  "message": "O que é composição?"
}
```

### Request com sessão (opcional)

```json
{
  "message": "Pode resumir a resposta anterior?",
  "session_id": "sessao-123"
}
```

### Response de sucesso

```json
{
  "answer": "Texto de resposta",
  "sources": [
    { "section": "Composição" }
  ]
}
```

### Response de fallback

```json
{
  "answer": "Não encontrei informação suficiente na base para responder essa pergunta.",
  "sources": []
}
```

---

## Documentação da API (Swagger/OpenAPI)

Disponível automaticamente via FastAPI:

- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

---

## Configuração por ambiente

Arquivo `.env` mínimo:

```dotenv
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
SESSION_TTL_SECONDS=1800
SESSION_MAX_TURNS=5

HOST=0.0.0.0
PORT=8000
```

### Observações

- `LLM_PROVIDER`: `gemini` ou `openai`
- Troca de provider feita apenas via configuração
- `session_id` é tratado internamente (não enviado ao provider)
- Para submissão final, `KB_URL` deve apontar para a URL oficial

---

## Execução local (sem Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Execução com Docker Compose

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f api
```

Parar ambiente:

```bash
docker compose down
```

---

## Automação com Makefile

```bash
make up       # sobe o ambiente
make down     # encerra o ambiente
make logs     # acompanha logs do serviço api
make rebuild  # recria o ambiente
make test     # executa testes automatizados
```

---

## Exemplos de teste

### Sucesso com contexto

```bash
curl -X POST "http://localhost:8000/messages" \
  -H "Content-Type: application/json" \
  -d '{"message":"O que é composição?"}'
```

### Fallback sem contexto

```bash
curl -X POST "http://localhost:8000/messages" \
  -H "Content-Type: application/json" \
  -d '{"message":"Pergunta fora do escopo da KB"}'
```

---

## Estado atual da implementação

### Concluído

- endpoint único `POST /messages`
- tool de KB via HTTP com parse e ranking
- orquestração com fallback obrigatório
- integração real com LLM no fluxo principal
- abstração multi-provider (Gemini e OpenAI)
- prompt centralizado
- memória por `session_id` (janela curta + TTL em memória)
- documentação automática (Swagger/OpenAPI)
- testes automatizados (contrato mínimo, fallback e sessão)
- Makefile para automação
- docker compose funcional

### Opcional (não implementado)

- persistência de sessão fora do processo (ex.: Redis)
- testes E2E com provider real
- ampliação de cenários de falha externa

---

## Critérios atendidos

- contrato de entrada e saída correto
- `answer` e `sources` com `section`
- fallback literal implementado corretamente
- uso da KB oficial via URL
- separação de responsabilidades
- provider LLM configurável por ambiente