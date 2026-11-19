"""Validation of an uploaded model: the catalog it gives, or one Portuguese message (research D2)."""
import pytest

from pedido import messages
from pedido.catalog import ModeloInvalido, load_catalog, validar_modelo


def test_load_catalog_accepts_bytes_and_gives_the_same_catalog_as_the_path(modelo_bytes, catalog):
    assert load_catalog(modelo_bytes) == load_catalog()
    assert len(load_catalog(modelo_bytes)) == len(catalog) == 167


def test_the_seed_and_a_model_with_a_new_product_are_valid(modelo_bytes, variante):
    assert len(validar_modelo(modelo_bytes)) == 167
    novo = validar_modelo(variante.com_produto_novo("Incenso Teste"))
    assert len(novo) == 168 and "Incenso Teste" in {p.nome for p in novo}


def test_the_new_product_has_a_quantity_cell_two_columns_to_the_left(variante):
    produto = next(p for p in validar_modelo(variante.com_produto_novo("Incenso Teste")) if p.nome == "Incenso Teste")
    assert produto.celula_qtd[0] in "AEIMQ" and produto.categoria in ("Defumadores", "Incensos")


@pytest.mark.parametrize("nome, mensagem", [
    ("VAZIO", messages.MODELO_VAZIO),
    ("XLS_ANTIGO", messages.MODELO_XLS),
    ("LIXO", messages.MODELO_ILEGIVEL),
])
def test_unusable_files_give_their_message(variante, nome, mensagem):
    with pytest.raises(ModeloInvalido) as error:
        validar_modelo(getattr(variante, nome))
    assert error.value.mensagem == mensagem and str(error.value) == mensagem


def test_a_model_without_products_is_refused(variante):
    with pytest.raises(ModeloInvalido) as error:
        validar_modelo(variante.sem_produtos())
    assert error.value.mensagem == messages.MODELO_SEM_PRODUTOS


def test_a_repeated_product_name_is_refused_and_named(variante):
    with pytest.raises(ModeloInvalido) as error:
        validar_modelo(variante.nome_repetido("Ogum"))
    assert error.value.mensagem == messages.MODELO_NOME_REPETIDO.format(nome="Ogum")


def test_a_merged_quantity_cell_is_refused_and_named(variante, by_name):
    with pytest.raises(ModeloInvalido) as error:
        validar_modelo(variante.celula_mesclada("Ogum"))
    assert error.value.mensagem == messages.MODELO_CELULA_MESCLADA.format(celula=by_name["Ogum"].celula_qtd)


def test_every_message_asks_to_check_or_to_save_as_xlsx():
    for texto in (messages.MODELO_VAZIO, messages.MODELO_XLS, messages.MODELO_ILEGIVEL, messages.MODELO_SEM_PRODUTOS,
                  messages.MODELO_NOME_REPETIDO, messages.MODELO_CELULA_MESCLADA, messages.MODELO_GRANDE):
        assert "Confira o modelo" in texto or "Salve o modelo" in texto
