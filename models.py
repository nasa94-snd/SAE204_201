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
        stations_data.append({
            "nom": station.get("libelle_station"),
            "dpt": station.get("code_departement"),
            "code": code_station,
            "site": station.get("libelle_site")
        })
    return stations_data
