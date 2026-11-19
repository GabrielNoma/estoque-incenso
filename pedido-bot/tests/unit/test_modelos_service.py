"""The service that decides which model is active (research D1, D4)."""
import pytest

from pedido import modelos
from pedido.catalog import ModeloInvalido, load_catalog
from pedido.modelos import ModeloIndisponivel, ModeloService


@pytest.fixture
def service(store):
    svc = ModeloService(store)
    svc.garantir_semente()
    return svc


def test_the_seed_is_installed_once_as_version_1(store):
    svc = ModeloService(store)
    svc.garantir_semente()
    svc.garantir_semente()
    assert [(m["versao"], m["arquivo"], m["ativo"], m["produtos"]) for m in store.listar_modelos()] == [
        (1, "PLANILHA_2024.xlsx", True, 167)]


def test_atual_gives_the_catalog_and_the_bytes_of_the_active_model(service, modelo_bytes):
    ativo = service.atual()
    assert ativo.versao == 1 and ativo.catalog == load_catalog(modelo_bytes) and ativo.conteudo == modelo_bytes
    assert ativo.arquivo == "PLANILHA_2024.xlsx"


def test_the_catalog_is_rebuilt_only_when_the_version_changes(service, monkeypatch):
    chamadas = []
    real = modelos.load_catalog
    monkeypatch.setattr(modelos, "load_catalog", lambda *a, **k: chamadas.append(1) or real(*a, **k))
    service.atual(); service.atual(); service.atual()
    assert len(chamadas) <= 1


def test_another_process_activating_a_model_is_seen_without_restart(store, service, variante):
    outro = ModeloService(store)
    assert len(outro.atual().catalog) == 167
    service.importar(variante.com_produto_novo(), "novo.xlsx")
    assert len(outro.atual().catalog) == 168 and outro.atual().versao == 2


def test_importar_activates_a_valid_model_and_summarizes_the_changes(service, variante):
    resumo = service.importar(variante.com_produto_novo("Incenso Teste"), "novo.xlsx")
    assert resumo["versao"] == 2 and resumo["arquivo"] == "novo.xlsx" and resumo["produtos"] == 168
    assert resumo["adicionados"] == ["Incenso Teste"] and resumo["removidos"] == [] and resumo["renomeados"] == []
    assert service.atual().versao == 2 and len(service.atual().catalog) == 168


def test_importar_reports_removed_and_renamed_products(service, variante):
    modelo = variante.renomeado("Arruda", "Arruda Pura", variante.sem_produto("Ogum"))
    resumo = service.importar(modelo, "editado.xlsx")
    assert resumo["removidos"] == ["Ogum"] and resumo["renomeados"] == [{"de": "Arruda", "para": "Arruda Pura"}]
    assert resumo["adicionados"] == [] and resumo["produtos"] == 166


def test_importing_the_same_file_again_reports_no_change(service, modelo_bytes):
    resumo = service.importar(modelo_bytes, "igual.xlsx")
    assert resumo["adicionados"] == resumo["removidos"] == resumo["renomeados"] == [] and resumo["versao"] == 2


def test_an_invalid_model_changes_nothing(service, store, variante):
    antes = store.listar_modelos()
    for ruim in (variante.VAZIO, variante.XLS_ANTIGO, variante.LIXO, variante.sem_produtos(),
                 variante.nome_repetido(), variante.celula_mesclada()):
        with pytest.raises(ModeloInvalido):
            service.importar(ruim, "ruim.xlsx")
    assert store.listar_modelos() == antes and service.atual().versao == 1


def test_a_model_that_cannot_be_read_or_has_no_products_is_unavailable(store, variante):
    store.salvar_modelo("quebrado.xlsx", variante.LIXO, 0)
    with pytest.raises(ModeloIndisponivel):
        ModeloService(store).atual()
    store.salvar_modelo("vazio.xlsx", variante.sem_produtos(), 0)
    with pytest.raises(ModeloIndisponivel):
        ModeloService(store).atual()


def test_por_versao_gives_an_older_model(service, variante, modelo_bytes):
    service.importar(variante.com_produto_novo(), "novo.xlsx")
    assert len(service.por_versao(1).catalog) == 167 and service.por_versao(1).conteudo == modelo_bytes
    assert len(service.por_versao(2).catalog) == 168


def test_info(service, variante):
    info = service.info()
    assert (info["versao"], info["arquivo"], info["produtos"]) == (1, "PLANILHA_2024.xlsx", 167) and info["ativado_em"]
    service.importar(variante.com_produto_novo(), "novo.xlsx")
    assert (service.info()["versao"], service.info()["produtos"]) == (2, 168)
