import os
import pyfiglet
from flask import Flask, jsonify
from flask_migrate import Migrate
from models.user import db
from api import CnpjAPI

__author__ = "Cleiton Leonel Creton"
__version__ = "0.0.1"

__message__ = f"""
Use com moderação, pois gerenciamento é tudo!
suporte: cleiton.leonel@gmail.com ou +55 (27) 9 9577-2291
"""

app = Flask(__name__)
migrate = Migrate()

basedir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "data")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'pycnpj.db')

db.init_app(app)
migrate.init_app(app, db)

with app.app_context():
    db.create_all()


custom_font = pyfiglet.Figlet(font="statics/fonts/ANSI_Shadow")
ascii_art = custom_font.renderText("Cnpja")
art_effect = f"""
{ascii_art}

author: {__author__} versão: {__version__}
{__message__}
"""

print(art_effect)


@app.route('/', methods=['GET'])
def index():
    return "PyCnpj 2023, Bem vindo!!!"


@app.route('/api/v1/cnpj/<cnpj>', methods=['GET'])
def get_cnpj(cnpj):
    client = CnpjAPI()
    client.accounts_manager()
    result = client.check_cnpj(cnpj)
    return jsonify(result)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=9005)
