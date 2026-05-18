CREATE TABLE IF NOT EXISTS funcionarias (
  id    SERIAL PRIMARY KEY,
  nome  VARCHAR(100) NOT NULL,
  ativa BOOLEAN      NOT NULL DEFAULT true,
  CONSTRAINT uq_funcionaria_nome UNIQUE (nome)
);

CREATE TABLE IF NOT EXISTS registros_diarios (
  id               SERIAL  PRIMARY KEY,
  funcionaria_id   INTEGER NOT NULL REFERENCES funcionarias(id) ON DELETE RESTRICT,
  data             DATE    NOT NULL,
  quantidade       INTEGER,
  falta            BOOLEAN NOT NULL DEFAULT false,
  motivo_falta     TEXT,
  observacao_falta VARCHAR(500),
  CONSTRAINT uq_registro_funcionaria_data  UNIQUE (funcionaria_id, data),
  CONSTRAINT chk_quantidade_positiva       CHECK ((quantidade >= 0) OR (quantidade IS NULL)),
  CONSTRAINT chk_exclusividade             CHECK (NOT ((quantidade IS NOT NULL) AND (falta = true))),
  CONSTRAINT chk_motivo_quando_falta       CHECK (((falta = false) AND (motivo_falta IS NULL)) OR ((falta = true) AND (motivo_falta IS NOT NULL))),
  CONSTRAINT chk_obs_quando_outro          CHECK ((motivo_falta <> 'outro') OR ((motivo_falta = 'outro') AND (observacao_falta IS NOT NULL) AND (observacao_falta <> '')))
);
