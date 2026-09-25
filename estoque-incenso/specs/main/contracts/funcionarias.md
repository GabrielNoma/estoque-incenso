# Contract: Funcionárias API

Base URL: `/api/funcionarias`

---

## GET /api/funcionarias

Lista funcionárias. Por padrão retorna apenas ativas.

**Query params:**

| Param            | Tipo | Default | Descrição                              |
|------------------|------|---------|----------------------------------------|
| includeInactive  | bool | false   | Se true, retorna também as desativadas |

**Response 200:**
```json
[
  { "id": 1, "nome": "Ana Silva", "ativa": true, "inativadaEm": null },
  { "id": 2, "nome": "Bia Santos", "ativa": false, "inativadaEm": "2026-08-31" }
]
```

---

## POST /api/funcionarias

Cria uma nova funcionária.

**Body:**
```json
{ "nome": "Carla Lima" }
```

**Response 201:**
```json
{ "id": 3, "nome": "Carla Lima", "ativa": true, "inativadaEm": null }
```

**Response 409** — nome já existe:
```json
{ "error": "Funcionária com este nome já existe." }
```

---

## PUT /api/funcionarias/{id}

Atualiza o nome de uma funcionária.

**Body:**
```json
{ "nome": "Carla Lima Atualizada" }
```

**Response 200:**
```json
{ "id": 3, "nome": "Carla Lima Atualizada", "ativa": true, "inativadaEm": null }
```

**Response 404** — não encontrada.

---

## PATCH /api/funcionarias/{id}/status

Ativa ou desativa uma funcionária. Ao desativar, grava `inativadaEm` com a data do dia
(America/Sao_Paulo); ao reativar, `inativadaEm` volta a `null`.

**Body:**
```json
{ "ativa": false }
```

**Response 200:**
```json
{ "id": 3, "nome": "Carla Lima", "ativa": false, "inativadaEm": "2026-09-25" }
```

**Response 404** — não encontrada.
