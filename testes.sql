-- TESTES DO BANCO (rode depois de recriar o banco com schema.sql)
-- Uso: python executar.py testes.sql

-- 1. ESTRUTURA: tabelas e indices criados
SELECT type, name FROM sqlite_master WHERE type IN ('table', 'index') AND name NOT LIKE 'sqlite_%' ORDER BY type, name;
PRAGMA foreign_keys;

-- 2. INSERTS VALIDOS (todos devem dar OK)
INSERT INTO cliente (nome, cpf, telefone, email) VALUES ('Ana Souza', '000.000.000-01', '11 90000-0001', 'ana@exemplo.com');
INSERT INTO cliente (nome, cpf) VALUES ('Beto Lima', '000.000.000-02');
INSERT INTO cliente (nome) VALUES ('Carla Dias');
INSERT INTO veiculo (cliente_id, placa, modelo, marca, ano) VALUES ((SELECT id FROM cliente WHERE cpf = '000.000.000-01'), 'AAA1A11', 'Gol', 'Volkswagen', 2015);
INSERT INTO veiculo (cliente_id, placa, modelo, marca, ano) VALUES ((SELECT id FROM cliente WHERE cpf = '000.000.000-01'), 'BBB2B22', 'Onix', 'Chevrolet', 2020);
INSERT INTO veiculo (cliente_id, placa, modelo, marca) VALUES ((SELECT id FROM cliente WHERE cpf = '000.000.000-02'), 'CCC3C33', 'Uno', 'Fiat');
INSERT INTO ordem_servico (veiculo_id, descricao, valor) VALUES ((SELECT id FROM veiculo WHERE placa = 'AAA1A11'), 'Troca de oleo', 150.00);
INSERT INTO ordem_servico (veiculo_id, descricao, status) VALUES ((SELECT id FROM veiculo WHERE placa = 'CCC3C33'), 'Revisao de freios', 'Em andamento');
SELECT id, nome, cpf FROM cliente;
SELECT id, cliente_id, placa, modelo FROM veiculo;
SELECT id, veiculo_id, descricao, status, data_abertura FROM ordem_servico;

-- 3. ERROS ESPERADOS (todos devem dar ERRO)
INSERT INTO cliente (nome, cpf) VALUES ('Outro', '000.000.000-01');
INSERT INTO veiculo (cliente_id, placa, modelo, marca) VALUES ((SELECT id FROM cliente WHERE cpf = '000.000.000-02'), 'AAA1A11', 'Palio', 'Fiat');
INSERT INTO veiculo (cliente_id, placa, modelo, marca) VALUES (9999, 'ZZZ9Z99', 'Fusca', 'Volkswagen');
INSERT INTO cliente (nome) VALUES (NULL);
INSERT INTO veiculo (cliente_id, placa, modelo, marca, ano) VALUES ((SELECT id FROM cliente WHERE cpf = '000.000.000-02'), 'DDD4D44', 'Antigo', 'Ford', 1800);
INSERT INTO ordem_servico (veiculo_id, descricao, valor) VALUES ((SELECT id FROM veiculo WHERE placa = 'AAA1A11'), 'Valor negativo', -10);
INSERT INTO ordem_servico (veiculo_id, descricao, status) VALUES ((SELECT id FROM veiculo WHERE placa = 'AAA1A11'), 'Status invalido', 'Inventado');

-- 4. UPDATE
UPDATE cliente SET telefone = '11 98888-8888' WHERE cpf = '000.000.000-02';
SELECT nome, telefone FROM cliente WHERE cpf = '000.000.000-02';

-- 5. JOIN x LEFT JOIN (Carla nao tem veiculo)
SELECT c.nome, v.placa FROM cliente c JOIN veiculo v ON v.cliente_id = c.id ORDER BY c.nome, v.placa;
SELECT c.nome, v.placa FROM cliente c LEFT JOIN veiculo v ON v.cliente_id = c.id ORDER BY c.nome, v.placa;

-- 6. ON DELETE CASCADE: apagar a Ana apaga os veiculos e as ordens dela
DELETE FROM cliente WHERE cpf = '000.000.000-01';
SELECT COUNT(*) AS veiculos_restantes FROM veiculo;
SELECT COUNT(*) AS ordens_restantes FROM ordem_servico;

-- 7. LIMPEZA
DELETE FROM cliente;
SELECT COUNT(*) AS clientes_restantes FROM cliente;