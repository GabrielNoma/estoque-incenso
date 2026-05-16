CREATE TABLE IF NOT EXISTS funcionarias (
  id    SERIAL PRIMARY KEY,
  nome  VARCHAR(100) NOT NULL UNIQUE,
  ativa BOOLEAN      NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS registros_diarios (
  id               SERIAL  PRIMARY KEY,
  funcionaria_id   INTEGER NOT NULL REFERENCES funcionarias(id) ON DELETE RESTRICT,
  data             DATE    NOT NULL,
  quantidade       INTEGER CHECK (quantidade >= 0),
  falta            BOOLEAN NOT NULL DEFAULT false,
  motivo_falta     TEXT,
  observacao_falta VARCHAR(500),
  CONSTRAINT uq_registro_funcionaria_data UNIQUE (funcionaria_id, data),
  CONSTRAINT chk_exclusividade            CHECK (NOT (quantidade IS NOT NULL AND falta = true)),
  CONSTRAINT chk_motivo_quando_falta      CHECK ((falta = false AND motivo_falta IS NULL) OR (falta = true AND motivo_falta IS NOT NULL)),
  CONSTRAINT chk_obs_quando_outro         CHECK (motivo_falta <> 'outro' OR (motivo_falta = 'outro' AND observacao_falta IS NOT NULL AND observacao_falta <> ''))
);
