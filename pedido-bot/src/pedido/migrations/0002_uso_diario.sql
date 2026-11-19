-- Migration 0002: the daily message counter per conversation (feature 006).
create table if not exists pedido.uso_diario (
    conversa text not null,
    dia date not null,
    mensagens integer not null default 0,
    primary key (conversa, dia)
);
alter table pedido.uso_diario enable row level security;
