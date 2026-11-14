"""Camada de acesso ao banco RELACIONAL (SQLite) da Oficina Mecânica.

Todo o SQL do sistema fica aqui. As rotas do Flask só chamam estas funções.
Os valores sempre vão em parâmetros (?), nunca concatenados no texto do SQL,
o que evita SQL injection.

Erros de restrição (CPF/placa repetidos, FK inválida) sobem como
sqlite3.IntegrityError, para a rota tratar e avisar o usuário.
"""
import sqlite3
from pathlib import Path

import click
from flask import current_app, g
from flask.cli import with_appcontext

BASE_DIR = Path(__file__).resolve().parent
SCHEMA_FILE = BASE_DIR / "schema.sql"

STATUSES = ["Aberta", "Em andamento", "Concluída"]


# ---------------------------------------------------------------------------
# Conexão
# ---------------------------------------------------------------------------
def get_db():
    """Uma conexão por requisição, guardada em g."""
    if "sql" not in g:
        g.sql = sqlite3.connect(current_app.config["SQL_DATABASE"])
        g.sql.row_factory = sqlite3.Row  # permite linha["nome"]
        g.sql.execute("PRAGMA foreign_keys = ON")  # liga a checagem de FK
    return g.sql


def close_db(_exc=None):
    """Fecha a conexão ao final da requisição."""
    conn = g.pop("sql", None)
    if conn is not None:
        conn.close()


def init_db():
    """Cria (ou recria) as tabelas a partir de schema.sql."""
    db = get_db()
    db.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
    db.commit()


def _vazio_para_none(valor):
    """Texto em branco vira NULL (evita dois CPFs '' quebrarem o UNIQUE)."""
    valor = (valor or "").strip()
    return valor or None


# ---------------------------------------------------------------------------
# CLIENTE
# ---------------------------------------------------------------------------
def listar_clientes():
    """READ: todos os clientes e quantos veículos cada um tem.
    LEFT JOIN + GROUP BY: clientes sem veículo também aparecem (total = 0)."""
    sql = """
        SELECT c.*, COUNT(v.id) AS total_veiculos
        FROM cliente c
        LEFT JOIN veiculo v ON v.cliente_id = c.id
        GROUP BY c.id
        ORDER BY c.nome
    """
    return get_db().execute(sql).fetchall()


def buscar_cliente(cliente_id):
    """READ: um cliente pelo id (ou None)."""
    return get_db().execute(
        "SELECT * FROM cliente WHERE id = ?", (cliente_id,)
    ).fetchone()


def criar_cliente(nome, cpf, telefone, email):
    """CREATE: insere um cliente e devolve o id gerado."""
    db = get_db()
    cur = db.execute(
        "INSERT INTO cliente (nome, cpf, telefone, email) VALUES (?, ?, ?, ?)",
        (
            nome.strip(),
            _vazio_para_none(cpf),
            _vazio_para_none(telefone),
            _vazio_para_none(email),
        ),
    )
    db.commit()
    return cur.lastrowid


def atualizar_cliente(cliente_id, nome, cpf, telefone, email):
    """UPDATE: altera um cliente. Retorna quantas linhas foram afetadas."""
    db = get_db()
    cur = db.execute(
        "UPDATE cliente SET nome = ?, cpf = ?, telefone = ?, email = ? WHERE id = ?",
        (
            nome.strip(),
            _vazio_para_none(cpf),
            _vazio_para_none(telefone),
            _vazio_para_none(email),
            cliente_id,
        ),
    )
    db.commit()
    return cur.rowcount


def deletar_cliente(cliente_id):
    """DELETE: apaga o cliente. O ON DELETE CASCADE apaga os veículos dele
    (e, por sua vez, as ordens de serviço desses veículos)."""
    db = get_db()
    cur = db.execute("DELETE FROM cliente WHERE id = ?", (cliente_id,))
    db.commit()
    return cur.rowcount


# ---------------------------------------------------------------------------
# VEÍCULO
# ---------------------------------------------------------------------------
def listar_veiculos():
    """READ: todos os veículos com o nome do dono.
    INNER JOIN: todo veículo tem dono (cliente_id é NOT NULL)."""
    sql = """
        SELECT v.*, c.nome AS cliente_nome
        FROM veiculo v
        JOIN cliente c ON c.id = v.cliente_id
        ORDER BY v.placa
    """
    return get_db().execute(sql).fetchall()


def listar_veiculos_do_cliente(cliente_id):
    """READ: veículos de um cliente."""
    return get_db().execute(
        "SELECT * FROM veiculo WHERE cliente_id = ? ORDER BY placa",
        (cliente_id,),
    ).fetchall()


def buscar_veiculo(veiculo_id):
    """READ: um veículo pelo id (ou None)."""
    return get_db().execute(
        "SELECT * FROM veiculo WHERE id = ?", (veiculo_id,)
    ).fetchone()


def buscar_veiculo_por_placa(placa):
    """READ: um veículo pela placa, com o nome do dono (ou None)."""
    sql = """
        SELECT v.*, c.nome AS cliente_nome
        FROM veiculo v
        JOIN cliente c ON c.id = v.cliente_id
        WHERE v.placa = ?
    """
    return get_db().execute(sql, (placa.strip().upper(),)).fetchone()


def criar_veiculo(cliente_id, placa, modelo, marca, ano):
    """CREATE: insere um veículo e devolve o id gerado."""
    db = get_db()
    cur = db.execute(
        """
        INSERT INTO veiculo (cliente_id, placa, modelo, marca, ano)
        VALUES (?, ?, ?, ?, ?)
        """,
        (cliente_id, placa.strip().upper(), modelo.strip(), marca.strip(), ano),
    )
    db.commit()
    return cur.lastrowid


def atualizar_veiculo(veiculo_id, cliente_id, placa, modelo, marca, ano):
    """UPDATE: altera um veículo. Retorna quantas linhas foram afetadas."""
    db = get_db()
    cur = db.execute(
        """
        UPDATE veiculo
        SET cliente_id = ?, placa = ?, modelo = ?, marca = ?, ano = ?
        WHERE id = ?
        """,
        (
            cliente_id,
            placa.strip().upper(),
            modelo.strip(),
            marca.strip(),
            ano,
            veiculo_id,
        ),
    )
    db.commit()
    return cur.rowcount


def deletar_veiculo(veiculo_id):
    """DELETE: apaga o veículo (e suas ordens de serviço, por CASCADE)."""
    db = get_db()
    cur = db.execute("DELETE FROM veiculo WHERE id = ?", (veiculo_id,))
    db.commit()
    return cur.rowcount


# ---------------------------------------------------------------------------
# Integração com o Flask: comando "flask init-db"
# ---------------------------------------------------------------------------
@click.command("init-db")
@with_appcontext
def init_db_command():
    """Recria as tabelas do banco a partir do schema.sql."""
    init_db()
    click.echo("Banco de dados inicializado.")


def init_app(app):
    """Registra o fechamento da conexão e o comando 'flask init-db'."""
    app.config.setdefault("SQL_DATABASE", str(BASE_DIR / "taskflow.db"))
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)