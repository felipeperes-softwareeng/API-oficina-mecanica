"""Aplicação Flask da Oficina Mecânica (CRUD de Clientes e Veículos)."""
import sqlite3

from flask import (Flask, abort, flash, redirect, render_template, request,
                   url_for)

import db_sql

app = Flask(__name__)
app.secret_key = "oficina-mecanica-chave-de-desenvolvimento"  # necessária para flash()
db_sql.init_app(app)  # conexão por requisição + comando "flask init-db"


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------
def mensagem_de_erro(erro):
    """Traduz um sqlite3.IntegrityError para uma mensagem amigável."""
    texto = str(erro)
    if "cliente.cpf" in texto:
        return "CPF já cadastrado para outro cliente."
    if "veiculo.placa" in texto:
        return "Placa já cadastrada para outro veículo."
    if "CHECK" in texto and "ano" in texto:
        return "Ano inválido: informe 1900 ou mais."
    if "FOREIGN KEY" in texto:
        return "Cliente inválido."
    return f"Erro no banco de dados: {texto}"


def ler_form_cliente():
    return {campo: request.form.get(campo, "").strip()
            for campo in ("nome", "cpf", "telefone", "email")}


def ler_form_veiculo():
    return {campo: request.form.get(campo, "").strip()
            for campo in ("cliente_id", "placa", "modelo", "marca", "ano")}


def validar_veiculo(dados):
    """Confere os campos do veículo. Retorna (valores, erro)."""
    if not (dados["cliente_id"] and dados["placa"]
            and dados["modelo"] and dados["marca"]):
        return None, "Preencha cliente, placa, modelo e marca."
    try:
        cliente_id = int(dados["cliente_id"])
    except ValueError:
        return None, "Cliente inválido."
    ano = None
    if dados["ano"]:
        try:
            ano = int(dados["ano"])
        except ValueError:
            return None, "O ano deve ser um número."
    return {"cliente_id": cliente_id, "placa": dados["placa"],
            "modelo": dados["modelo"], "marca": dados["marca"],
            "ano": ano}, None


# ---------------------------------------------------------------------------
# Páginas institucionais
# ---------------------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/sobre')
def sobre():
    return render_template('sobre.html')


@app.route('/contato')
def contato():
    return render_template('contato.html')


# ---------------------------------------------------------------------------
# CLIENTES (CRUD)
# ---------------------------------------------------------------------------
@app.route('/clientes')
def lista_clientes():                                   # READ (lista)
    return render_template('clientes/lista.html',
                           clientes=db_sql.listar_clientes())


@app.route('/cliente/<int:cliente_id>')
def detalhe_cliente(cliente_id):                        # READ (um)
    cliente = db_sql.buscar_cliente(cliente_id)
    if cliente is None:
        abort(404)
    return render_template('clientes/detalhe.html', cliente=cliente,
                           veiculos=db_sql.listar_veiculos_do_cliente(cliente_id))


@app.route('/clientes/novo', methods=['GET', 'POST'])
def novo_cliente():                                     # CREATE
    dados = {"nome": "", "cpf": "", "telefone": "", "email": ""}
    if request.method == 'POST':
        dados = ler_form_cliente()
        if not dados["nome"]:
            flash("O nome é obrigatório.", "erro")
        else:
            try:
                db_sql.criar_cliente(**dados)
                flash("Cliente cadastrado com sucesso.", "sucesso")
                return redirect(url_for('lista_clientes'))
            except sqlite3.IntegrityError as erro:
                flash(mensagem_de_erro(erro), "erro")
    return render_template('clientes/form.html', dados=dados, editando=False)


@app.route('/clientes/<int:cliente_id>/editar', methods=['GET', 'POST'])
def editar_cliente(cliente_id):                         # UPDATE
    cliente = db_sql.buscar_cliente(cliente_id)
    if cliente is None:
        abort(404)
    dados = {k: ("" if v is None else v) for k, v in dict(cliente).items()}
    if request.method == 'POST':
        dados = ler_form_cliente()
        if not dados["nome"]:
            flash("O nome é obrigatório.", "erro")
        else:
            try:
                db_sql.atualizar_cliente(cliente_id, **dados)
                flash("Cliente atualizado com sucesso.", "sucesso")
                return redirect(url_for('lista_clientes'))
            except sqlite3.IntegrityError as erro:
                flash(mensagem_de_erro(erro), "erro")
    return render_template('clientes/form.html', dados=dados, editando=True,
                           cliente_id=cliente_id)


@app.route('/clientes/<int:cliente_id>/excluir', methods=['POST'])
def excluir_cliente(cliente_id):                        # DELETE
    if db_sql.deletar_cliente(cliente_id):
        flash("Cliente excluído (veículos e ordens dele também).", "sucesso")
    else:
        flash("Cliente não encontrado.", "erro")
    return redirect(url_for('lista_clientes'))


# ---------------------------------------------------------------------------
# VEÍCULOS (CRUD)
# ---------------------------------------------------------------------------
@app.route('/veiculos')
def lista_veiculos():                                   # READ (lista)
    return render_template('veiculos/lista.html',
                           veiculos=db_sql.listar_veiculos())


@app.route('/veiculo/<string:placa>')
def detalhe_veiculo(placa):                             # READ (um)
    veiculo = db_sql.buscar_veiculo_por_placa(placa)
    if veiculo is None:
        abort(404)
    return render_template('veiculos/detalhe.html', veiculo=veiculo)


@app.route('/veiculos/novo', methods=['GET', 'POST'])
def novo_veiculo():                                     # CREATE
    clientes = db_sql.listar_clientes()
    if not clientes:
        flash("Cadastre um cliente antes de cadastrar um veículo.", "erro")
        return redirect(url_for('novo_cliente'))
    dados = {"cliente_id": request.args.get("cliente_id", ""), "placa": "",
             "modelo": "", "marca": "", "ano": ""}
    if request.method == 'POST':
        dados = ler_form_veiculo()
        valores, erro = validar_veiculo(dados)
        if erro:
            flash(erro, "erro")
        else:
            try:
                db_sql.criar_veiculo(**valores)
                flash("Veículo cadastrado com sucesso.", "sucesso")
                return redirect(url_for('lista_veiculos'))
            except sqlite3.IntegrityError as e:
                flash(mensagem_de_erro(e), "erro")
    return render_template('veiculos/form.html', dados=dados, clientes=clientes,
                           editando=False)


@app.route('/veiculos/<int:veiculo_id>/editar', methods=['GET', 'POST'])
def editar_veiculo(veiculo_id):                         # UPDATE
    veiculo = db_sql.buscar_veiculo(veiculo_id)
    if veiculo is None:
        abort(404)
    dados = {k: ("" if v is None else v) for k, v in dict(veiculo).items()}
    if request.method == 'POST':
        dados = ler_form_veiculo()
        valores, erro = validar_veiculo(dados)
        if erro:
            flash(erro, "erro")
        else:
            try:
                db_sql.atualizar_veiculo(veiculo_id, **valores)
                flash("Veículo atualizado com sucesso.", "sucesso")
                return redirect(url_for('lista_veiculos'))
            except sqlite3.IntegrityError as e:
                flash(mensagem_de_erro(e), "erro")
    return render_template('veiculos/form.html', dados=dados,
                           clientes=db_sql.listar_clientes(), editando=True,
                           veiculo_id=veiculo_id)


@app.route('/veiculos/<int:veiculo_id>/excluir', methods=['POST'])
def excluir_veiculo(veiculo_id):                        # DELETE
    if db_sql.deletar_veiculo(veiculo_id):
        flash("Veículo excluído (e suas ordens de serviço).", "sucesso")
    else:
        flash("Veículo não encontrado.", "erro")
    return redirect(url_for('lista_veiculos'))


if __name__ == '__main__':
    app.run(debug=True)
