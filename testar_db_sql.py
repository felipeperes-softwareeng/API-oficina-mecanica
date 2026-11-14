"""Testa as funcoes do db_sql.py num banco TEMPORARIO (nao mexe no taskflow.db).
Uso: python testar_db_sql.py
"""
import os
import sqlite3
import tempfile

from flask import Flask

import db_sql

arquivo = os.path.join(tempfile.mkdtemp(), "teste.db")
app = Flask(__name__)
app.config["SQL_DATABASE"] = arquivo
db_sql.init_app(app)

total = 0


def ok(condicao, descricao):
    global total
    total += 1
    print(("  OK   " if condicao else "  FALHOU  ") + descricao)
    if not condicao:
        raise SystemExit(1)


def levanta(excecao, funcao):
    try:
        funcao()
    except excecao:
        return True
    return False


print("flask init-db")
res = app.test_cli_runner().invoke(args=["init-db"])
ok(res.exit_code == 0 and "inicializado" in res.output, "comando init-db roda e cria o banco")

with app.app_context():
    print("CLIENTE")
    ana = db_sql.criar_cliente("Ana", "111", "", "ana@x.com")
    beto = db_sql.criar_cliente("Beto", "", "", "")
    carla = db_sql.criar_cliente("Carla", "", "", "")
    ok(ana and beto and carla, "criar_cliente devolve o id")
    ok(db_sql.buscar_cliente(ana)["nome"] == "Ana", "buscar_cliente")
    ok(db_sql.buscar_cliente(999) is None, "buscar_cliente inexistente devolve None")
    ok(db_sql.buscar_cliente(beto)["cpf"] is None, "texto em branco vira NULL")
    ok(levanta(sqlite3.IntegrityError, lambda: db_sql.criar_cliente("X", "111", "", "")), "CPF repetido bloqueado (UNIQUE)")
    ok(db_sql.atualizar_cliente(ana, "Ana Souza", "111", "9999", "ana@x.com") == 1, "atualizar_cliente")
    ok(db_sql.buscar_cliente(ana)["nome"] == "Ana Souza", "dado atualizado no banco")

    print("VEICULO")
    v1 = db_sql.criar_veiculo(ana, "abc1d23", "Gol", "VW", 2015)
    v2 = db_sql.criar_veiculo(beto, "xyz9k88", "Uno", "Fiat", None)
    ok(db_sql.buscar_veiculo(v1)["placa"] == "ABC1D23", "placa gravada em maiusculas")
    ok(db_sql.buscar_veiculo_por_placa("abc1d23")["cliente_nome"] == "Ana Souza", "buscar_veiculo_por_placa traz o dono")
    ok(db_sql.buscar_veiculo_por_placa("NAO000") is None, "placa inexistente devolve None")
    ok(len(db_sql.listar_veiculos_do_cliente(ana)) == 1, "listar_veiculos_do_cliente")
    ok(levanta(sqlite3.IntegrityError, lambda: db_sql.criar_veiculo(beto, "ABC1D23", "a", "b", 2000)), "placa repetida bloqueada (UNIQUE)")
    ok(levanta(sqlite3.IntegrityError, lambda: db_sql.criar_veiculo(999, "ZZZ0Z00", "a", "b", 2000)), "cliente inexistente bloqueado (FOREIGN KEY)")
    ok(levanta(sqlite3.IntegrityError, lambda: db_sql.criar_veiculo(ana, "ABC0A00", "a", "b", 1800)), "ano invalido bloqueado (CHECK)")
    ok(db_sql.atualizar_veiculo(v1, ana, "abc1d23", "Gol G6", "VW", 2016) == 1, "atualizar_veiculo")

    print("JOIN x LEFT JOIN")
    ok(len(db_sql.listar_veiculos()) == 2, "listar_veiculos (JOIN) traz os 2 veiculos")
    ok(db_sql.listar_veiculos()[0]["cliente_nome"] in ("Ana Souza", "Beto"), "listar_veiculos traz o nome do dono")
    totais = {c["nome"]: c["total_veiculos"] for c in db_sql.listar_clientes()}
    ok(totais == {"Ana Souza": 1, "Beto": 1, "Carla": 0}, "listar_clientes (LEFT JOIN) inclui Carla com 0 veiculos")

    print("DELETE e CASCADE")
    ok(db_sql.deletar_veiculo(v2) == 1, "deletar_veiculo")
    ok(db_sql.deletar_cliente(ana) == 1, "deletar_cliente")
    ok(len(db_sql.listar_veiculos()) == 0, "CASCADE: veiculos da Ana apagados junto")
    ok(db_sql.deletar_cliente(999) == 0, "deletar inexistente afeta 0 linhas")

with app.test_request_context():
    a = db_sql.get_db()
    ok(db_sql.get_db() is a, "get_db reaproveita a mesma conexao na requisicao")
    ok(a.execute("PRAGMA foreign_keys").fetchone()[0] == 1, "PRAGMA foreign_keys esta ligado")

print(f"\nTodos os {total} testes passaram.")