# Contract: Funcionárias API

Base URL: `/api/funcionarias`

> Contrato idêntico ao backend C# — mesmos paths, métodos, query params e payloads.

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
  { "id": 1, "nome": "Ana Silva", "ativa": true },
  { "id": 2, "nome": "Bia Santos", "ativa": false }
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
{ "id": 3, "nome": "Carla Lima", "ativa": true }
```

**Response 409** — nome já existe:
```json
{ "error": "Funcionária com este nome já existe." }
```

---

## PUT /api/funcionarias/:id

Atualiza o nome de uma funcionária.

**Body:**
```json
{ "nome": "Carla Lima Atualizada" }
```

**Response 200:**
```json
{ "id": 3, "nome": "Carla Lima Atualizada", "ativa": true }
```

**Response 404** — não encontrada.

---

## PATCH /api/funcionarias/:id/status

Ativa ou desativa uma funcionária.

**Body:**
```json
{ "ativa": false }
```

**Response 200:**
```json
{ "id": 3, "nome": "Carla Lima", "ativa": false }
```

**Response 404** — não encontrada.
