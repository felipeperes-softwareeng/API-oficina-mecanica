-- TaskFlow - Esquema RELACIONAL (SQL)
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS ordem_servico;

DROP TABLE IF EXISTS veiculo;

DROP TABLE IF EXISTS cliente;

CREATE TABLE cliente (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cpf TEXT UNIQUE,
    telefone TEXT,
    email text
);

CREATE TABLE veiculo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    placa TEXT NOT NULL UNIQUE,
    modelo TEXT NOT NULL,
    marca TEXT NOT NULL,
    ano INTEGER CHECK (
        ano IS NULL
        OR ano >= 1900
    ),
    FOREIGN KEY (cliente_id) REFERENCES cliente (id) ON DELETE CASCADE
);

CREATE TABLE ordem_servico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    veiculo_id INTEGER NOT NULL,
    descricao TEXT NOT NULL,
    valor REAL CHECK (
        valor IS NULL
        OR valor >= 0
    ),
    status TEXT NOT NULL DEFAULT 'Aberta' CHECK (
        status IN ('Aberta', 'Em andamento', 'Concluída')
    ),
    data_abertura DATE NOT NULL DEFAULT CURRENT_DATE,
    FOREIGN KEY (veiculo_id) REFERENCES veiculo (id) ON DELETE CASCADE
);

CREATE INDEX idx_veiculo_cliente ON veiculo(cliente_id);
CREATE INDEX idx_os_veiculo ON ordem_servico(veiculo_id);
CREATE INDEX idx_os_status ON ordem_servico(status);