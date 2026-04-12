# Base de Conhecimento — Python Agent Challenge

## Composição

### Definição
Composição é quando uma função/classe utiliza outra instância para executar parte do trabalho.

### Na prática
Em Python, composição aparece em `service -> client`, `orquestração -> tool`, `fluxo -> llm_client`.

### Quando usar
Use para reduzir acoplamento e facilitar teste unitário.

### Observação curta
Trocar uma dependência de classe por composição geralmente é mais simples de evoluir depois.

### Ponto de atenção
“Composição é sempre melhor que herança em qualquer cenário.”

---

## Herança

### Definição
Herança permite que uma classe compartilhe atributos e comportamentos de outra.

### Na prática
É útil em hierarquias estáveis: `BaseTool`, `BaseHTTPClient`, `BaseRequest`.

### Quando usar
Use quando há semelhança forte de contrato e comportamento, e baixa chance de mudanças de comportamento por especialização.

### Observação curta
No backend pequeno, muitos times ainda preferem herança por ser mais direta de escrever.

### Ponto de atenção
“Herança costuma ser a melhor opção padrão para integração com LLM/tool.”

---

## Responsabilidade única

### Definição
Cada módulo deve fazer uma parte principal bem definida do fluxo.

### Na prática
Separar API, orquestração, busca de contexto e formatação melhora manutenção.

### Quando usar
Quando o projeto cresce um pouco (até mesmo em desafio), evita endpoint inchado e debugging difícil.

### Observação curta
Responsabilidade misturada gera bugs silenciosos em validação e formatação.

---

## Endpoint de API

### Definição
Endpoint é a borda de entrada da aplicação HTTP, não um “service locator” de toda a lógica.

### Na prática
Ele recebe `message`, valida formato e encaminha para o fluxo interno.

### Quando usar
Quando necessário, coloque validação leve no endpoint e deixe regra de negócio para camadas internas.

### Observação curta
Em MVPs simples pode parecer tentador concentrar fluxo no endpoint, mas isso reduz rastreabilidade.

### Ponto de atenção
“Em projetos pequenos, colocar regra de negócio inteira no endpoint é a forma mais prática e correta.”

---

## Validação

### Definição
Validação garante que a entrada e saída estejam no formato esperado antes de seguir o fluxo.

### Na prática
Verificar `message` vazio, muito curto ou tipo inválido é parte obrigatória.

### Quando usar
Sempre antes de chamar LLM/Tool em produção ou testes.

### Observação curta
Sem validação, a tool pode ser chamada com parâmetros inválidos e retornar contexto irrelevante.

---

## Orquestração

### Definição
A orquestração é quem coordena o fluxo de decisão e chama recursos externos (tool, LLM, etc.).

### Na prática
Recebe a pergunta, decide buscar contexto e organiza prompt/resposta final.

### Quando usar
Use orquestração quando houver decisão explícita de “buscar ou não buscar” contexto e montar resposta com base nisso.

### Observação curta
A orquestração não precisa ter lógica de domínio extensa, mas precisa manter o fluxo consistente.

---

## Instruções de sistema

### Definição
Instruções de sistema orientam comportamento, tom e limites do LLM.

### Na prática
Definem prioridade do contrato (formato de resposta, fallback, foco no contexto).

### Quando usar
Sempre definir que faltando contexto o resultado deve ser transparente e não inventar.

### Observação curta
Prompt robusto ajuda, mas não substitui verificação da saída.

### Ponto de atenção
“Prompts de sistema longos eliminam a necessidade de validação de saída.”

---

## Tool de conhecimento

### Definição
Tool de conhecimento consulta a base (Markdown) para recuperar trechos úteis.

### Na prática
Pode buscar por palavra-chave, por seção e retornar trecho + seção.

### Quando usar
Sempre que a resposta depender de conteúdo específico da base técnica.

### Observação curta
A tool não deve responder usuário final; ela alimenta a orquestração com contexto.

---

## Rastreabilidade

### Definição
Capacidade de apontar de onde veio a informação usada na resposta.

### Na prática
Cada resposta deve incluir seção consultada para facilitar revisão.

### Quando usar
Sempre em desafios com output estruturado.

### Observação curta
Sem rastreabilidade, respostas parecem decoradas e geram baixa confiabilidade.

---

## LLM no fluxo principal

### Definição
LLM transforma pergunta + contexto em resposta final.

### Na prática
O LLM não é fonte primária da verdade: ele interpreta o contexto recuperado.

### Quando usar
Sempre que houver necessidade de linguagem natural baseada na base.

### Observação curta
Formato de resposta depende de prompt + validação; não depende de um único parâmetro de geração.

### Ponto de atenção
“Temperatura baixa já garante formato JSON válido sem validação adicional.”

---

## Resposta estruturada

### Definição
Formato previsível de retorno para a API (ex.: `answer`, `sources`).

### Na prática
Evite texto solto; prefira estrutura única para todos os casos.

### Quando usar
Sempre que a API for consumida por outro sistema.

### Observação curta
Mesmo texto simples precisa de contrato rígido no contrato de resposta.

---

## Falta de contexto

### Definição
Situação em que a KB não cobre a pergunta com segurança.

### Na prática
Responder com limitação explícita protege contra alucinação.

### Quando usar
Se a busca retorna vazio ou baixa relevância, retornar fallback.

### Observação curta
Resposta esperada de fallback:
`{"answer":"Não encontrei informação suficiente na base para responder essa pergunta.","sources":[]}`

---

## Boas práticas gerais

### Definição
Conjunto de escolhas práticas para manter clareza e consistência.

### Na prática
Variáveis explícitas (`KB_URL`), divisão por responsabilidade, testes básicos de contrato.

### Quando usar
Sempre, em qualquer implementação mínima que queira passar revisão.

### Observação curta
Preferir decisões explícitas e simples em vez de soluções “genéricas demais”.

---

## Limites desta base

### Definição
Escopo deliberado: O1 de backend com orquestração, tool, contexto e resposta simples.

### Na prática
Se a pergunta sair desse tema, não inventar; declarar ausência de contexto.

### Quando usar
Sempre que o contexto retornado for baixo ou fora do escopo.

### Observação curta
Exemplo de retorno quando não há cobertura no escopo:
`"Não encontrei informação suficiente na base para responder essa pergunta."`
