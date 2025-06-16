from flask import Flask, render_template, request
import requests
from pymongo import MongoClient
from models import *

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    page = int(request.args.get('page', 1))
    stations_data = afficher_stations(page=page, per_page=20)
    return render_template("index.html", stations=stations_data, page=page)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)