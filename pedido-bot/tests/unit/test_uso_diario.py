"""The daily message counter (spec US5): shared through the database, restarts each day (America/Sao_Paulo)."""
from datetime import date, datetime, timezone

from pedido import guardrails
from pedido.store import Store

DIA = date(2026, 11, 18)


def test_it_counts_accepted_messages_and_refuses_once_the_limit_is_reached(store):
    assert [store.registrar_mensagem("5511", DIA, 3) for _ in range(5)] == [1, 2, 3, None, None]


def test_a_new_day_starts_again_and_conversations_are_kept_apart(store):
    for _ in range(2):
        store.registrar_mensagem("5511", DIA, 2)
    assert store.registrar_mensagem("5511", DIA, 2) is None
    assert store.registrar_mensagem("5511", date(2026, 11, 19), 2) == 1
    assert store.registrar_mensagem("5512", DIA, 2) == 1


def test_two_store_instances_share_the_count(clean_db):
    a, b = Store(clean_db), Store(clean_db)
    a.registrar_mensagem("5511", DIA, 2)
    b.registrar_mensagem("5511", DIA, 2)
    assert a.registrar_mensagem("5511", DIA, 2) is None  # the count lives in the database


def test_the_day_is_the_business_day_in_sao_paulo():
    # 02:30 UTC on the 19th is still the 18th at 23:30 in Sao Paulo (UTC-3)
    assert guardrails.dia_atual(lambda: datetime(2026, 11, 19, 2, 30, tzinfo=timezone.utc)) == date(2026, 11, 18)
    assert guardrails.dia_atual(lambda: datetime(2026, 11, 19, 3, 30, tzinfo=timezone.utc)) == date(2026, 11, 19)
    assert isinstance(guardrails.dia_atual(), date)
