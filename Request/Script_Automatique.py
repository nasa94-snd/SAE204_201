import requests
import json
from pymongo import MongoClient

# URL1 de l'API Hub'Eau pour récupérer des données sur les sites hydrométriques
url1 = 'https://hubeau.eaufrance.fr/api/v2/hydrometrie/referentiel/sites'
url2 = 'https://hubeau.eaufrance.fr/api/v2/hydrometrie/referentiel/stations'

# Récupérer les données de l'API
def recuperer_donnees(url):
    """
    Récupère toutes les données via l'API en gérant la pagination avec le champ 'next'.
    """
    all_data = []
    while url:
        response = requests.get(url)
        if response.status_code in [206, 200]:
            data = response.json()
            all_data.extend(data['data'])  # Ajoute les nouveaux documents à la liste
            # Récupère l'URL de la page suivante (s'il y en a une)
            url = data.get('next')  # Si 'next' est présent, on continue avec la nouvelle URL
        else:
            print(f"Erreur {response.status_code} lors de la récupération des données.")
            break
    return all_data

# -----------------------------------------------------------------------------------------------------
# Sites

# Vérifier si la requête 1 à reussi
data_sites = recuperer_donnees(url1)
    
    # Liste des champs que tu veux extraire (par exemple, 'code_site', 'nom', 'latitude', 'longitude')
filtré1 = []
for item in data_sites:
    filtré_sites = {
        'code_site': item.get('code_site'),
        'code_departement': item.get('code_departement'),
        'libelle_site': item.get('libelle_site'),
        'libelle_cours_eau': item.get('libelle_cours_eau'),
        'latitude_station': item['geometry'].get('coordinates', [])[0],
        'longitude_station': item['geometry'].get('coordinates', [])[1]
    }
            
    filtré1.append(filtré_sites)

for doc in filtré1:
    if '_id' in doc:
        del doc['_id']

# -----------------------------------------------------------------------------------------------------
# Stations
    
# Vérifier si la requête 2 à reussi
data_stations = recuperer_donnees(url2)
    
    # Liste des champs que tu veux extraire (par exemple, 'code_site', 'nom', 'latitude', 'longitude')
filtré2 = []
for item in data_stations: 
    filtré_stations = {
        'code_station': item.get('code_station'),
        'code_site': item.get('code_site'),
        'code_departement': item.get('code_departement'),
        'libelle_station': item.get('libelle_station'),
        'libelle_cours_eau': item.get('libelle_cours_eau'),
        'latitude_station': item['geometry'].get('coordinates', [])[0],
        'longitude_station': item['geometry'].get('coordinates', [])[1],
        'date_ouverture_station': item.get('date_ouverture_station'),
        'en_service': item.get('en_service')
    }
    
    
    filtré2.append(filtré_stations)

for doc in filtré2:
    if '_id' in doc:
        del doc['_id']

regions = []
for item in data_stations:
    region = {
        '_id': item.get('code_region'),
        "libelle_region": item.get("libelle_region")
    }
            
    regions.append(region)


departements = []
for item in data_stations:
    departement = {
        '_id': item.get('code_departement'),
        "code_region": item.get('code_region'),
        "libelle_departement": item.get("libelle_departement")
    }
            
    departements.append(departement)
    

regions_uniques = {}
for item in data_stations:
    code_region = item.get('code_region')
    libelle_region = item.get('libelle_region')
    if code_region and code_region not in regions_uniques:
        regions_uniques[code_region] = {
            '_id': code_region,
            'libelle_region': libelle_region
        }

# Dédupliquer les départements
departements_uniques = {}
for item in data_stations:
    code_dept = item.get('code_departement')
    if code_dept and code_dept not in departements_uniques:
        departements_uniques[code_dept] = {
            '_id': code_dept,
            "code_region": item.get('code_region'),
            "libelle_departement": item.get("libelle_departement")
        }

# Connexion à MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['Hubleau']

db.sites.drop()
db.stations.drop()
db.regions.drop()
db.departements.drop()

Sites = db['sites']
Stations = db['stations']
Regions = db['regions']
Departements = db['departements']

Sites.insert_many(filtré1)
Stations.insert_many(filtré2)
Regions.insert_many(regions_uniques.values())
Departements.insert_many(departements_uniques.values())

print(f"{len(filtré1)} documents insérés dans la collection 'sites'.")
print(f"{len(filtré2)} documents insérés dans la collection 'stations'.")
print(f"{len(regions_uniques)} documents insérés dans la collection 'regions'.")
print(f"{len(departements_uniques)} documents insérés dans la collection 'departements'.")

def extraire_communes(data_stations):
    communes_uniques = {}
    for item in data_stations:
        code_com = item.get('code_commune')
        if code_com and code_com not in communes_uniques:
            communes_uniques[code_com] = {
                '_id': code_com,
                "code_departement": item.get('code_departement'),
                "libelle_commune": item.get("libelle_commune")
            }
    return list(communes_uniques.values())

def extraire_regions(data_stations):
    regions_uniques = {}
    for item in data_stations:
        code_region = item.get('code_region')
        libelle_region = item.get('libelle_region')
        if code_region and code_region not in regions_uniques:
            regions_uniques[code_region] = {
                '_id': code_region,
                'libelle_region': libelle_region
            }
    return list(regions_uniques.values())

def extraire_departements(data_stations):
    departements_uniques = {}
    for item in data_stations:
        code_dept = item.get('code_departement')
        if code_dept and code_dept not in departements_uniques:
            departements_uniques[code_dept] = {
                '_id': code_dept,
                "code_region": item.get('code_region'),
                "libelle_departement": item.get("libelle_departement")
            }
    return list(departements_uniques.values())

def extraire_stations(data_stations):
    return [{
        'code_station': item.get('code_station'),
        'code_site': item.get('code_site'),
        'code_departement': item.get('code_departement'),
        'libelle_station': item.get('libelle_station'),
        'libelle_cours_eau': item.get('libelle_cours_eau'),
        'latitude_station': item['geometry'].get('coordinates', [])[0],
        'longitude_station': item['geometry'].get('coordinates', [])[1],
        'date_ouverture_station': item.get('date_ouverture_station'),
        'en_service': item.get('en_service')
    } for item in data_stations]
