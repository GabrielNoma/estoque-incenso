# Contract: new texts (pt-BR, constants of `messages.py`)

Reply to the customer (normal `resposta`, pending order kept, language model not called):

| Constant | Text |
|---|---|
| `LIMITE_DIARIO` | "Você chegou ao limite de mensagens de hoje. Tente novamente amanhã." |
| `OCUPADO` | "Estamos com muitas mensagens agora. Tente de novo em instantes." |

API errors (`erro`, status): `chave_ausente` 401 "Informe a chave de acesso."; `chave_invalida` 401 "Chave de
acesso inválida."; `sem_permissao` 403 "Esta chave não tem permissão para esta operação.";
`muitas_requisicoes` 429 "Muitas requisições. Aguarde um instante e tente de novo."; `corpo_grande` 413
"A mensagem é grande demais.".

Startup and tools: `ERRO_CHAVES_AUSENTES` (production without keys), `ERRO_CHAVE_MALFORMADA` ("A entrada {n}
de API_KEYS é inválida: use nome:escopos:chave, com chave de pelo menos 32 caracteres."),
`ERRO_MIGRACOES_PENDENTES` (tells to run `python -m pedido.migrate`), `ERRO_MIGRACAO_ALTERADA` (names the
file), `ERRO_MIGRACAO_FALHOU`, `REINDEXAR_RESUMO` ("Reindexados: {feitos}. Falhas: {falhas}."),
`REINDEXAR_SEM_EMBEDDING`.
