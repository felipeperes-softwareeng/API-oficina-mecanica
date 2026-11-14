from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/contato')
def contato():
    return render_template('contato.html')

@app.route('/cliente/<int:cliente_id>')
def detalhe_cliente(cliente_id):
    return f"Página de detalhes do Cliente ID: {cliente_id}"

@app.route('/veiculo/<string:placa>')
def detalhe_veiculo(placa):
    return f"Página de detalhes do Veículo com a placa: {placa.upper()}"