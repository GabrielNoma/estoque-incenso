"""pt-BR scanning helpers shared by tests (Constitution I)."""
import re

BANNED_ENGLISH = {
    "error", "submit", "loading", "approve", "cancel", "delete", "save", "upload", "download",
    "please", "failed", "invalid", "required", "warning", "success", "search", "close", "back",
    "next", "order", "message", "quantity", "product", "confirm", "review", "retry", "total lines",
    "something went wrong", "not found", "try again",
}
PT_WORDS = {
    "de", "da", "do", "dos", "das", "não", "nao", "o", "a", "os", "as", "um", "uma", "para", "com",
    "por", "em", "e", "sua", "seu", "linha", "linhas", "pedido", "mensagem", "tente", "novamente",
    "revisar", "aprovar", "produto", "quantidade", "planilha", "cole", "analisar", "baixar",
    "confirmar", "mesclar", "adicionar", "remover", "sem", "há", "ha", "nenhum", "histórico",
    "historico", "aprovado", "proposto", "total", "totais", "duplicado", "inválida", "invalida",
    "deve", "ser", "ou", "falta", "que", "se", "na", "no", "nas", "nos", "pelo", "pela", "mas", "já", "ja",
    "agora", "antes", "depois", "ainda", "esta", "está", "foi", "é", "são", "ao", "à", "dos", "uso",
    "use", "defina", "confira", "veja", "rodando", "banco", "dados", "memória", "memoria", "nada",
    "apelido", "apelidos", "reindexados", "falhas", "nenhuma", "migração", "ativado", "desativado", "nenhuma", "concluído", "concluido", "pendentes", "pendente", "continuou", "falhando",
}
ACCENTED = re.compile(r"[áàâãéêíóôõúç]", re.IGNORECASE)


def looks_ptbr(text: str) -> bool:
    words = set(re.findall(r"[a-záàâãéêíóôõúç]+", text.lower()))
    return bool(ACCENTED.search(text)) or bool(words & PT_WORDS)


def english_hits(text: str) -> list[str]:
    lowered = text.lower()
    return [w for w in BANNED_ENGLISH if re.search(rf"\b{re.escape(w)}\b", lowered)]
