"""Testa as telas do CRUD (Clientes e Veiculos) num banco TEMPORARIO.
Nao mexe no taskflow.db. Uso: python testar_crud.py
"""
import os
import tempfile

import db_sql
from app import app

app.config["SQL_DATABASE"] = os.path.join(tempfile.mkdtemp(), "teste.db")
app.config["TESTING"] = True
with app.app_context():
    db_sql.init_db()
cliente = app.test_client()
total = 0


def ok(descricao):
    global total
    total += 1
    print("  OK   " + descricao)


def pagina(url, codigo=200, contem=(), descricao=""):
    r = cliente.get(url, follow_redirects=True)
    texto = r.get_data(as_text=True)
    assert r.status_code == codigo, f"{url}: esperado {codigo}, veio {r.status_code}"
    for t in contem:
        assert t in texto, f"{url}: nao encontrei '{t}' na pagina"
    ok(descricao or f"GET {url}")


def envia(url, dados=None, contem=(), ausente=(), descricao=""):
    r = cliente.post(url, data=dados or {}, follow_redirects=True)
    texto = r.get_data(as_text=True)
    assert r.status_code == 200, f"{url}: veio {r.status_code}"
    for t in contem:
        assert t in texto, f"{url}: nao encontrei '{t}' na pagina"
    for t in ausente:
        assert t not in texto, f"{url}: '{t}' nao deveria aparecer"
    ok(descricao or f"POST {url}")


print("PAGINAS")
for u in ("/", "/sobre", "/contato", "/clientes", "/veiculos"):
    pagina(u)
pagina("/clientes", contem=["Nenhum cliente"], descricao="lista de clientes vazia")
pagina("/veiculos", contem=["Nenhum veículo"], descricao="lista de veiculos vazia")
pagina("/veiculos/novo", contem=["Cadastre um cliente antes"], descricao="veiculo sem cliente cadastrado e avisado")

print("CLIENTE")
envia("/clientes/novo", {"nome": ""}, ["O nome é obrigatório"], descricao="nome vazio e recusado")
envia("/clientes/novo", {"nome": "Ana <b>", "cpf": "111"}, ["Cliente cadastrado", "Ana &lt;b&gt;"], descricao="cadastra cliente (e escapa HTML)")
envia("/clientes/novo", {"nome": "Outro", "cpf": "111"}, ["CPF já cadastrado"], descricao="CPF repetido avisado")
envia("/clientes/novo", {"nome": "Beto"}, ["Cliente cadastrado"], descricao="cadastra cliente sem CPF")
envia("/clientes/novo", {"nome": "Carla"}, ["Cliente cadastrado"], descricao="dois clientes sem CPF convivem")
pagina("/clientes/1/editar", contem=['value="111"'], descricao="formulario de edicao vem preenchido")
envia("/clientes/1/editar", {"nome": "Ana Souza", "cpf": "111", "telefone": "9"}, ["Cliente atualizado", "Ana Souza"], descricao="edita cliente")
pagina("/clientes/99/editar", 404, descricao="editar cliente inexistente da 404")
pagina("/cliente/99", 404, descricao="detalhe de cliente inexistente da 404")

print("VEICULO")
pagina("/veiculos/novo?cliente_id=2", contem=['value="2" selected'], descricao="dono vem pre-selecionado")
envia("/veiculos/novo", {"cliente_id": "1", "placa": "", "modelo": "x", "marca": "y"}, ["Preencha cliente"], descricao="campo obrigatorio vazio e recusado")
envia("/veiculos/novo", {"cliente_id": "1", "placa": "abc1d23", "modelo": "Gol", "marca": "VW", "ano": "abc"}, ["ano deve ser um número"], descricao="ano nao numerico e recusado")
envia("/veiculos/novo", {"cliente_id": "1", "placa": "abc1d23", "modelo": "Gol", "marca": "VW", "ano": "1800"}, ["Ano inválido"], descricao="ano 1800 e recusado (CHECK)")
envia("/veiculos/novo", {"cliente_id": "1", "placa": "abc1d23", "modelo": "Gol", "marca": "VW", "ano": "2015"}, ["Veículo cadastrado", "ABC1D23"], descricao="cadastra veiculo (placa em maiusculas)")
envia("/veiculos/novo", {"cliente_id": "2", "placa": "ABC1D23", "modelo": "Uno", "marca": "Fiat"}, ["Placa já cadastrada"], descricao="placa repetida avisada")
envia("/veiculos/novo", {"cliente_id": "999", "placa": "ZZZ0Z00", "modelo": "a", "marca": "b"}, ["Cliente inválido"], descricao="cliente inexistente e recusado (FK)")
envia("/veiculos/novo", {"cliente_id": "2", "placa": "xyz9k88", "modelo": "Uno", "marca": "Fiat"}, ["Veículo cadastrado"], descricao="cadastra veiculo sem ano")
pagina("/veiculo/abc1d23", contem=["Gol", "Ana Souza"], descricao="detalhe do veiculo mostra o dono")
pagina("/veiculo/NAO000", 404, descricao="placa inexistente da 404")
pagina("/cliente/1", contem=["ABC1D23"], descricao="detalhe do cliente lista os veiculos dele")
pagina("/cliente/3", contem=["ainda não tem veículos"], descricao="cliente sem veiculo e indicado")
pagina("/clientes", contem=["Carla", ">0<"], descricao="LEFT JOIN: Carla aparece com 0 veiculos")
pagina("/veiculos/1/editar", contem=['value="ABC1D23"', 'value="2015"'], descricao="edicao de veiculo vem preenchida")
envia("/veiculos/1/editar", {"cliente_id": "2", "placa": "ABC1D23", "modelo": "Gol G6", "marca": "VW", "ano": "2016"}, ["Veículo atualizado", "Gol G6"], descricao="edita veiculo (troca de dono)")

print("EXCLUSAO")
assert cliente.get("/clientes/1/excluir").status_code == 405
ok("GET nao exclui (so POST)")
envia("/veiculos/2/excluir", contem=["Veículo excluído"], ausente=["XYZ9K88"], descricao="exclui veiculo")
envia("/veiculos/99/excluir", contem=["Veículo não encontrado"], descricao="excluir veiculo inexistente e avisado")
envia("/clientes/2/excluir", contem=["Cliente excluído"], descricao="exclui cliente")
pagina("/veiculos", contem=["Nenhum veículo"], descricao="CASCADE: veiculos do cliente excluido sumiram")
envia("/clientes/99/excluir", contem=["Cliente não encontrado"], descricao="excluir cliente inexistente e avisado")

print(f"\nTodos os {total} testes passaram.")