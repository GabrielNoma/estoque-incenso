"""Every text the customer sees, in Brazilian Portuguese (Constitution I).

Replies, startup refusals, HTTP error messages and the labels of the test chat page live here; no
other module hard-codes user-facing text. `tests/unit/test_ptbr_strings.py` scans this module:
UPPERCASE str/dict constants only. The exact replies are documented in specs/003.../contracts/replies.md.
"""

# -- the conversation ---------------------------------------------------------------------------------
PERGUNTA_CONFIRMACAO = "ok ou não?"
CONFIRMADO = "Pedido confirmado. Segue a planilha."
CANCELADO = "Pedido cancelado. Pode enviar o pedido novamente."
ENVIE_PEDIDO = "Envie o seu pedido para eu montar a lista."
SEM_ITENS = "Não encontrei itens nessa mensagem. Envie o pedido novamente."
ERRO_LEITURA = "Não consegui ler o pedido agora. Envie de novo em instantes."
ERRO_PLANILHA = "Não consegui gerar a planilha agora. Responda ok de novo em instantes."
ERRO_BANCO = "Não consegui registrar agora. Envie de novo em instantes."

# -- startup: the tool refuses to start and prints one of these ----------------------------------------------
ERRO_BANCO_NAO_CONFIGURADO = (
    "O banco de dados não está configurado. Defina a variável DATABASE_URL com o endereço do "
    "Postgres (veja o arquivo .env.example)."
)
ERRO_BANCO_INACESSIVEL = (
    "Não foi possível conectar ao banco de dados. Confira se o Postgres está rodando "
    "(docker compose up -d db) e se DATABASE_URL está correta."
)
ERRO_LLM_PROVIDER_INVALIDO = "LLM_PROVIDER deve ser 'anthropic' ou 'openai_compatible'."

# -- HTTP errors of the test chat ---------------------------------------------------------------------------
ERRO_REQUISICAO_INVALIDA = "A requisição não é válida. Confira os dados enviados e tente novamente."
ERRO_PEDIDO_NAO_ENCONTRADO = "Pedido não encontrado."
ERRO_PEDIDO_NAO_CONFIRMADO = "Esse pedido ainda não foi confirmado."
ERRO_INTERNO = "Algo deu errado do nosso lado. Tente novamente em instantes."

ERROS = {
    "requisicao_invalida": ERRO_REQUISICAO_INVALIDA,
    "pedido_nao_encontrado": ERRO_PEDIDO_NAO_ENCONTRADO,
    "pedido_nao_confirmado": ERRO_PEDIDO_NAO_CONFIRMADO,
    "erro_interno": ERRO_INTERNO,
}

# -- the test chat page ------------------------------------------------------------------------------------
PAGINA_TITULO = "Bot de pedidos"
PAGINA_SUBTITULO = "Teste da conversa, como no WhatsApp"
PAGINA_TELEFONE = "Seu número"
PAGINA_CAMPO = "Digite o seu pedido"
PAGINA_ENVIAR = "Enviar"
PAGINA_BAIXAR = "Baixar planilha"
PAGINA_SEM_REDE = "Não consegui falar com o servidor. Tente de novo."


# -- feature 004: guardrails, memory and the nicknames script -----------------------------------------
MENSAGEM_LONGA = "Mensagem muito longa. Envie o pedido em partes menores."
MUITAS_MENSAGENS = "Muitas mensagens seguidas. Aguarde um instante e envie de novo."
QUANTIDADE_ALTA = "Quantidade acima do limite. Envie o pedido novamente com uma quantidade menor."
ERRO_VECTOR_INDISPONIVEL = ("A extensão de vetores do banco (pgvector) não está disponível. "
                            "Use um Postgres com pgvector, como a imagem do docker compose.")
ERRO_DIMENSAO_DIFERENTE = ("A memória de apelidos foi criada com vetores de tamanho {guardado}, mas "
                           "EMBED_DIMENSIONS está em {configurado}. Use o mesmo valor ou recrie a tabela.")
APELIDO_NAO_ENCONTRADO = "Apelido não encontrado."
APELIDOS_VAZIO = "Nenhum apelido guardado ainda."
APELIDOS_CABECALHO = ("id", "texto", "produto", "positivos", "negativos", "status", "aplica")
APELIDO_ATIVADO = "Apelido {id} ativado."
APELIDO_DESATIVADO = "Apelido {id} desativado."
SIM = "sim"
NAO = "não"

# -- feature 005: the managed order-form model ----------------------------------------------------------
MODELO_INVALIDO = "Não consegui usar a planilha modelo. Confira o modelo e tente de novo."
MODELO_PRODUTO_AUSENTE = ("Um produto do pedido não está mais na planilha modelo. "
                          "Confira o modelo e envie o pedido novamente.")
MODELO_VAZIO = "O arquivo está vazio. Confira o modelo e envie de novo."
MODELO_XLS = "Esse arquivo é do formato antigo (.xls). Salve o modelo como .xlsx e envie de novo."
MODELO_ILEGIVEL = "Não consegui ler o arquivo como planilha .xlsx. Confira o modelo e envie de novo."
MODELO_SEM_PRODUTOS = ("Não encontrei produtos nas colunas esperadas (C, G, K, O e S, linhas 4 a 46). "
                       "Confira o modelo e envie de novo.")
MODELO_NOME_REPETIDO = 'O produto "{nome}" aparece mais de uma vez. Confira o modelo e envie de novo.'
MODELO_CELULA_MESCLADA = "A célula de quantidade {celula} está mesclada. Confira o modelo e envie de novo."
MODELO_GRANDE = "O arquivo é grande demais (limite de {limite} MB). Confira o modelo e envie de novo."
ERROS["modelo_invalido"] = MODELO_INVALIDO
ERROS["modelo_grande"] = MODELO_GRANDE
ERROS["modelo_indisponivel"] = MODELO_INVALIDO
APELIDO_PRODUTO_MUDOU = "(o produto mudou no modelo)"

# -- feature 006: access, hosting, migrations, cost limits ------------------------------------------------
LIMITE_DIARIO = "Você chegou ao limite de mensagens de hoje. Tente novamente amanhã."
OCUPADO = "Estamos com muitas mensagens agora. Tente de novo em instantes."
ERROS["chave_ausente"] = "Informe a chave de acesso."
ERROS["chave_invalida"] = "Chave de acesso inválida."
ERROS["sem_permissao"] = "Esta chave não tem permissão para esta operação."
ERROS["muitas_requisicoes"] = "Muitas requisições. Aguarde um instante e tente de novo."
ERROS["corpo_grande"] = "A mensagem é grande demais."
ERRO_CHAVES_AUSENTES = ("Em produção é obrigatório configurar pelo menos uma chave de acesso em API_KEYS "
                        "(formato nome:escopos:chave).")
ERRO_CHAVE_MALFORMADA = ("A entrada {n} de API_KEYS é inválida: use nome:escopos:chave, "
                         "com chave de pelo menos 32 caracteres.")
ERRO_CHAVE_DUPLICADA = "O nome {nome} aparece mais de uma vez em API_KEYS."
ERRO_ESCOPO_DESCONHECIDO = "A entrada {n} de API_KEYS usa um escopo desconhecido: {escopo}."
ERRO_MIGRACOES_PENDENTES = ("Há migrações do banco pendentes. Rode antes: python -m pedido.migrate "
                            "(pendentes: {lista}).")
ERRO_MIGRACAO_ALTERADA = "A migração {arquivo} já foi aplicada e o arquivo foi alterado depois. Restaure o arquivo original."
ERRO_MIGRACAO_FALHOU = "A migração {arquivo} falhou e foi desfeita. Nada foi gravado."
MIGRACAO_APLICADA = "Migração {arquivo} aplicada."
MIGRACAO_NADA = "Nenhuma migração pendente."
MIGRACAO_ESTADOS = {"aplicada": "aplicada", "pendente": "pendente", "alterada": "alterada"}
REINDEXAR_RESUMO = "Reindexados: {feitos}. Falhas: {falhas}."
REINDEXAR_SEM_EMBEDDING = "Os embeddings não estão configurados (EMBED_BASE_URL e EMBED_MODEL). Nada foi feito."
