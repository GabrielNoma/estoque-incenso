"""The LCEL chains (Constitution V). Order chain: extract | match each line | aggregate."""
from langchain_core.runnables import RunnableLambda

from pedido.export import fill_template, quantities_for_export
from pedido.extract import extract
from pedido.lista import LinhaCasada, ResultadoPedido, aggregate


def build_order_chain(matcher, chat_model):
    """message (str) -> ResultadoPedido: the items summed in Excel order, plus the matched lines."""
    extract_step = RunnableLambda(lambda mensagem: extract(mensagem, chat_model))

    def match_step(lines):
        products = matcher.runnable().invoke([line.texto for line in lines])
        return [LinhaCasada(line.texto, line.quantidade, product)
                for line, product in zip(lines, products) if product is not None]

    def sum_step(matched):
        return ResultadoPedido(aggregate([(l.produto, l.quantidade) for l in matched]), matched)

    return extract_step | RunnableLambda(match_step) | RunnableLambda(sum_step)


def build_export_chain(catalog, template_path=None):
    """Fill step of chain 2: [(produto_id, quantidade), ...] -> .xlsx bytes.

    Runs when the customer says ok, and again when the file is downloaded.
    """
    return (RunnableLambda(lambda finals: quantities_for_export(finals, catalog))
            | RunnableLambda(lambda quantities: fill_template(quantities, template_path)))
