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

    
def afficher_stations(page=1, per_page=20):
    collections = init_db()
    stations_collection = collections["stations"]
    stations_list = stations_collection.find()
    
    # Pagination MongoDB
    skip = (page - 1) * per_page
    stations_list = stations_collection.find().skip(skip).limit(per_page)


    stations_data = []
    for station in stations_list:
        code_station = station.get("_id")  # ou la bonne clé
        mesure = get_mesures_station(code_station)
        m = mesure[0]  # maintenant m est un dictionnaire
        stations_data.append({
            "nom": station.get("libelle_station"),
            "dpt": station.get("code_departement"),
            "code": code_station,
            "site": station.get("libelle_site"),
            "commune": station.get("libelle_commune"),
            "grandeur": m.get("grandeur_hydro_elab"),
            "valeur": m.get("resultat_obs_elab"),
            "date": m.get("date_obs_elab")
        })
    return stations_data

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