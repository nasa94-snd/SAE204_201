from pymongo import MongoClient
import requests


def get_stations_by_departement(code_departement):
    client = MongoClient('mongodb://localhost:27017/')
    db = client['Hubleau']
    stations = db.stations.find({"code_departement": code_departement})
    return [s['code_station'] for s in stations]


def get_qualite_dynamique_par_stations(codes):
    url = 'https://hubeau.eaufrance.fr/api/v2/hydrometrie/obs_elab'
    params = {
        "code_station": ",".join(codes),  # API accepte une liste de codes séparés par virgule
        "size": 100  # taille max de résultats
    }
    response = requests.get(url, params=params)
    if response.status_code in [200, 206]:
        return response.json()['data']
    else:
        return []

if __name__ == "__main__":
    departement = "75"
    codes = get_stations_by_departement(departement)
    qualites = get_qualite_dynamique_par_stations(codes)

    print(f"Nombre de stations trouvées : {len(codes)}")
    print(f"Données dynamiques récupérées : {len(qualites)}")

    # Exemple affichage :
    for mesure in qualites[:5]:
        print(f"{mesure['code_station']} : {mesure['resultat_obs_elab']} {mesure['grandeur_hydro_elab']} le {mesure['date_obs_elab']}")
