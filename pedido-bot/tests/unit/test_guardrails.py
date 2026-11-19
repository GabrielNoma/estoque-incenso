"""Guardrails for the model (Constitution VIII): pure checks, no network."""
import logging
from types import SimpleNamespace

import pytest

from pedido import guardrails


def line(texto="ogum", quantidade=1.0):
    return SimpleNamespace(texto=texto, quantidade=quantidade)


def test_valid_lines_pass_untouched():
    lines = [line("ogum", 2), line("abre caminho", 0.5)]
    assert guardrails.validar_linhas(lines) == lines


@pytest.mark.parametrize("quantidade", [0, 0.0, -1, -0.5, float("nan"), float("inf"), float("-inf"),
                                        True, False, "2", None, [1]])
def test_a_quantity_that_is_not_a_number_above_zero_drops_the_line(quantidade):
    assert guardrails.validar_linhas([line("ogum", quantidade)]) == []


@pytest.mark.parametrize("texto", ["", "   ", None, 5, "x" * 121])
def test_an_empty_non_text_or_too_long_text_drops_the_line(texto):
    assert guardrails.validar_linhas([line(texto, 1)]) == []


def test_a_text_of_exactly_the_maximum_is_kept(monkeypatch):
    monkeypatch.setenv("MAX_TEXTO_LINHA", "10")
    assert len(guardrails.validar_linhas([line("a" * 10)])) == 1
    assert guardrails.validar_linhas([line("a" * 11)]) == []


def test_only_the_first_lines_up_to_the_maximum_are_kept(monkeypatch):
    lines = [line(f"produto {i}") for i in range(60)]
    assert guardrails.validar_linhas(lines) == lines[:50]
    monkeypatch.setenv("MAX_LINHAS", "5")
    assert guardrails.validar_linhas(lines) == lines[:5]


def test_invalid_lines_do_not_use_up_the_maximum(monkeypatch):
    monkeypatch.setenv("MAX_LINHAS", "2")
    lines = [line("a", 0), line("b", 1), line("c", -1), line("d", 1), line("e", 1)]
    assert [l.texto for l in guardrails.validar_linhas(lines)] == ["b", "d"]


def test_checar_quantidade_accepts_exactly_the_limit_and_refuses_one_more():
    assert guardrails.checar_quantidade([(None, 1000.0)]) is True
    assert guardrails.checar_quantidade([(None, 1000.01)]) is False
    assert guardrails.checar_quantidade([(None, 600), (None, 600)]) is True  # different products: not summed here


def test_the_quantity_limit_comes_from_the_configuration(monkeypatch):
    monkeypatch.setenv("MAX_QTD_PRODUTO", "10")
    assert guardrails.checar_quantidade([(None, 11)]) is False


def test_checar_tamanho(monkeypatch):
    assert guardrails.checar_tamanho("x" * 2000) is True
    assert guardrails.checar_tamanho("x" * 2001) is False
    monkeypatch.setenv("MAX_MENSAGEM", "5")
    assert guardrails.checar_tamanho("123456") is False


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_the_rate_limiter_refuses_the_message_after_the_limit_and_the_window_slides(monkeypatch):
    monkeypatch.setenv("LIMITE_MSG_POR_MINUTO", "3")
    clock = Clock()
    limiter = guardrails.RateLimiter(clock=clock)
    assert [limiter.permitir("1") for _ in range(4)] == [True, True, True, False]
    clock.now += 59
    assert limiter.permitir("1") is False  # the first three are still inside the 60 s window
    clock.now += 2
    assert limiter.permitir("1") is True  # they left the window


def test_a_refused_message_does_not_extend_the_block(monkeypatch):
    monkeypatch.setenv("LIMITE_MSG_POR_MINUTO", "1")
    clock = Clock()
    limiter = guardrails.RateLimiter(clock=clock)
    assert limiter.permitir("1") is True
    for _ in range(5):
        clock.now += 10
        assert limiter.permitir("1") is False
    clock.now += 11  # 61 s after the only accepted message
    assert limiter.permitir("1") is True


def test_phone_numbers_are_independent(monkeypatch):
    monkeypatch.setenv("LIMITE_MSG_POR_MINUTO", "1")
    limiter = guardrails.RateLimiter(clock=Clock())
    assert limiter.permitir("1") is True and limiter.permitir("1") is False
    assert limiter.permitir("2") is True


def test_registrar_logs_only_the_type(caplog):
    caplog.set_level(logging.DEBUG)
    guardrails.registrar("taxa")
    assert [r.getMessage() for r in caplog.records] == ["guardrail=taxa"]


def test_dropping_lines_logs_only_types(caplog):
    caplog.set_level(logging.DEBUG)
    guardrails.validar_linhas([line("segredo-do-cliente", 0)] + [line(f"p{i}") for i in range(60)])
    assert "segredo-do-cliente" not in caplog.text
    assert {r.getMessage() for r in caplog.records} == {"guardrail=linhas_invalidas", "guardrail=linhas_demais"}
