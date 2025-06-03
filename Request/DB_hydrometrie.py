import pymongo
import requests
from pymongo import MongoClient

# Connexion à MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["DB_hydrometrie"]

# Collections
Stations = db["Stations"]
Sites = db["Sites"]
Departements = db["Departements"]
Regions = db["Regions"]

# URL de l'API des sites (contenant aussi infos de stations)
url ="https://hubeau.eaufrance.fr/api/v2/hydrometrie/referentiel/stations"
# Paramètres de la requête
params = {
    "size": 10000,  # Nombre d'éléments à récupérer
}
# Requête HTTP
response = requests.get(url, params=params)
# Même si c'est 206, les données sont valides
if response.status_code in [200, 206]:
    data = response.json()["data"]
    print(f"{len(data)} éléments reçus")
else:
    print("Erreur HTTP :", response.status_code)

# Accès aux données (clé "data")
data = response.json()["data"]

# Boucle sur chaque enregistrement
for item in data:
    code_region = item.get("code_region")
    if isinstance(code_region, list):
        code_region = code_region[0]  # prend le premier élément si liste
    code_departement = item.get("code_departement")
    if isinstance(code_departement, list):
        code_departement = code_departement[0]  # prend le premier élément si liste
    code_site = item.get("code_site")
    if isinstance(code_site, list):
        code_site = code_site[0]  # prend le premier élément si liste
    code_station = item.get("code_station")
    if isinstance(code_station, list):
        code_station = code_station[0]  # prend le premier élément si liste
    # Région
    Regions_data = {
        "_id": code_region,
        "libelle_region": item.get("libelle_region")
    }
    Regions.update_one(
        {"_id": Regions_data["_id"]},
        {"$set": Regions_data},
        upsert=True
    )

    #  Département
    Departements_data = {
        "_id": code_departement,
        "libelle_departement": item.get("libelle_departement"),
        "code_region": Regions_data["_id"]
    }
    Departements.update_one(
        {"_id": Departements_data["_id"]},
        {"$set": Departements_data},
        upsert=True
    )

    # Site
    Sites_data = {
        "_id": code_site,
        "libelle_site": item.get("libelle_site"),
        "code_departement": Departements_data["_id"],
        "latitude": item.get("latitude"),
        "longitude": item.get("longitude"),
        "libelle_cours_eau": item.get("libelle_cours_eau")
    }
    Sites.update_one(
        {"_id": Sites_data["_id"]},
        {"$set": Sites_data},
        upsert=True
    )

    #  Tous les items n'ont pas toujours une station associée
    if "code_station" in item and code_station:
        Stations_data = {
            "_id": code_station,
            "libelle_station": item.get("libelle_station"),
            "code_site": Sites_data["_id"],
            "code_sandre_reseau_station": item.get("code_sandre_reseau_station"),
            "latitude": item.get("latitude"),
            "longitude": item.get("longitude"),
            "date_ouverture_station": item.get("date_ouverture_station"),
            "en_service": item.get("en_service")
        }
        Stations.update_one(
            {"_id": Stations_data["_id"]},
            {"$set": Stations_data},
            upsert=True
        )

print("✅ Importation terminée avec succès !")

nb_regions = Regions.count_documents({})
nb_departements = Departements.count_documents({})
nb_sites = Sites.count_documents({})
nb_stations = Stations.count_documents({})

print(f"✅ Importation terminée avec succès !")
print(f"📊 Résumé des données insérées :")
print(f"   - Régions      : {nb_regions}")
print(f"   - Départements : {nb_departements}")
print(f"   - Sites        : {nb_sites}")
print(f"   - Stations     : {nb_stations}")