# Contract: Exportação Excel API

Base URL: `/api/exportacao`

> Contrato idêntico ao backend C# — mesmo path, método, query params e estrutura do arquivo.

---

## GET /api/exportacao/excel

Gera e retorna o arquivo `.xlsx` do mês selecionado.

**Query params (obrigatórios):**

| Param | Tipo | Descrição         |
|-------|------|-------------------|
| ano   | int  | Ano (ex: 2026)    |
| mes   | int  | Mês 1–12 (ex: 4)  |

**Response 200:**

- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Content-Disposition: `attachment; filename="producao_2026_04.xlsx"`
- Body: bytes do arquivo `.xlsx`

**Estrutura do arquivo Excel:**

Aba **Produção**:
```
          | Dia 1 | Dia 2 | ... | Sem 1 | Dia 7 | ... | Sem 2 | ... | Total
Ana Silva |   45  |       | ... |  220  |  30   | ... |  180  | ... |  850
Bia Santos|   32  |  FALTA| ... |  160  |       | ... |  140  | ... |  620
TOTAL DIA |   77  |       | ... |       |  30   | ... |       | ... | 1470
```

- Células de fim de semana: fundo cinza claro
- Células de falta: texto "FALTA" com fundo amarelo
- Linha de total do dia: negrito, fundo cinza
- Coluna de total mensal: negrito
- Colunas de total semanal ISO: fundo azul claro

Aba **Faltas**:
```
Funcionária | Data       | Motivo   | Observação
Ana Silva   | 2026-04-02 | Atestado |
Bia Santos  | 2026-04-10 | Outro    | Viagem de emergência
```

**Response 400** — parâmetros inválidos:
```json
{ "error": "Ano e mês são obrigatórios e devem ser válidos." }
```
