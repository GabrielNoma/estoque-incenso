# Contract: Registros Diários API

Base URL: `/api/registros`

---

## GET /api/registros

Retorna os registros do mês/ano selecionado. Inclui funcionárias ativas e inativas que possuam registros
no mês (campo `ativa` indica a situação). O frontend não exibe inativas na grade, mas as soma nos totais e no
Resumo Mensal. A exportação Excel (`GET /api/exportacao/excel`) segue a mesma regra, implementada em
`backend/src/queries/producaoMensal.js`. `mes` fora de 1–12 retorna 400.

-------|------|----------------------|
| ano   | int  | Ano (ex: 2026)       |
| mes   | int  | Mês 1–12 (ex: 4)     |

**Response 200:**
```json
{
  "ano": 2026,
  "mes": 4,
  "funcionarias": [
    {
      "id": 1,
      "nome": "Ana Silva",
      "ativa": true,
      "registros": [
        {
          "id": 10,
          "data": "2026-04-01",
          "quantidade": 45,
          "falta": false,
          "motivoFalta": null,
          "observacaoFalta": null
        },
        {
          "id": 11,
          "data": "2026-04-02",
          "quantidade": null,
          "falta": true,
          "motivoFalta": "atestado",
          "observacaoFalta": null
        }
      ]
    }
  ]
}
```

**Notas:**
- Dias sem registro simplesmente não aparecem no array `registros` da funcionária
- `motivoFalta` values: `"atestado"`, `"falta"`, `"outro"`

---

## PUT /api/registros

Upsert de um único registro (cria ou atualiza pelo par funcionária+data).

**Body — registrar produção:**
```json
{
  "funcionariaId": 1,
  "data": "2026-04-03",
  "quantidade": 50,
  "falta": false,
  "motivoFalta": null,
  "observacaoFalta": null
}
```

**Body — registrar falta:**
```json
{
  "funcionariaId": 1,
  "data": "2026-04-04",
  "quantidade": null,
  "falta": true,
  "motivoFalta": "outro",
  "observacaoFalta": "Viagem de emergência"
}
```

**Response 200** — registro salvo:
```json
{
  "id": 12,
  "funcionariaId": 1,
  "data": "2026-04-03",
  "quantidade": 50,
  "falta": false,
  "motivoFalta": null,
  "observacaoFalta": null
}
```

**Response 400** — validação falhou:
```json
{ "error": "Quantidade e falta não podem ser informados simultaneamente." }
```

**Response 404** — funcionária não encontrada.

---

## DELETE /api/registros/{id}

Remove um registro (limpa a célula).

**Response 204** — removido com sucesso.

**Response 404** — registro não encontrado.
