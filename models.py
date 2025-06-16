from pymongo import MongoClient
import pandas as pd
import requests


def init_db():
    # Connexion MongoDB
    client = MongoClient("mongodb://localhost:27017/")
    db = client["Hubleau"]
    return {
        "stations": db["stations"],
        "sites": db["sites"],
        "communes": db["communes"],
        "departements": db["departements"],
        "regions": db["regions"]
    }


def get_mesures_station(code_station):
    url = f"https://hubeau.eaufrance.fr/api/v2/hydrometrie/obs_elab"
    params = {
        "code_station": code_station,
        "size": 1,              # Dernière donnée
        "sort": "asc"
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code in [200, 206]:
            data = response.json()
            if data['data']:
                return response.json()['data']
        return None
    except Exception as e:
        print(f"Erreur API : {e}")
        return None