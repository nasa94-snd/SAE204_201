import sqlite3
import requests
import os

# URL de l'API Hub'Eau
url1 = 'https://hubeau.eaufrance.fr/api/v2/hydrometrie/referentiel/sites'
url2 = 'https://hubeau.eaufrance.fr/api/v2/hydrometrie/referentiel/stations'

# Fonction pour créer une connexion SQLite3
def create_connection(db_file):
    """Crée une connexion à la base SQLite3"""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Connexion à {db_file} réussie")
    except sqlite3.Error as e:
        print(f"Erreur lors de la connexion à {db_file}: {e}")
    return conn

def drop_database(db_file):
    """Supprime la base de données si elle existe"""
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"Base de données {db_file} supprimée")
    else:
        print(f"Base de données {db_file} n'existe pas")

# Fonction pour créer les tables SQLite3
def create_tables(conn):
    """Crée les tables dans la base SQLite3"""
    create_sites_table = '''CREATE TABLE IF NOT EXISTS sites (
                                code_site TEXT PRIMARY KEY,
                                code_commune TEXT,
                                libelle_site TEXT,
                                libelle_cours_eau TEXT,
                                FOREIGN KEY (code_commune) REFERENCES communes (code_commune)
                            );'''
    create_stations_table = '''CREATE TABLE IF NOT EXISTS stations (
                                code_station TEXT PRIMARY KEY,
                                code_site TEXT,
                                libelle_station TEXT,
                                libelle_cours_eau TEXT,
                                latitude_station REAL,
                                longitude_station REAL,
                                date_ouverture_station TEXT,
                                en_service INTEGER,
                                FOREIGN KEY (code_site) REFERENCES sites (code_site)
                            );'''
    create_communes_table = '''CREATE TABLE IF NOT EXISTS communes (
                                code_commune TEXT PRIMARY KEY,
                                code_departement TEXT,
                                libelle_commune TEXT,
                                FOREIGN KEY (code_departement) REFERENCES departements (code_departement)
                            );'''
    create_departements_table = '''CREATE TABLE IF NOT EXISTS departements (
                                    code_departement TEXT PRIMARY KEY,
                                    code_region TEXT,
                                    libelle_departement TEXT,
                                    FOREIGN KEY (code_region) REFERENCES regions (code_region)
                                  );'''
    create_regions_table = '''CREATE TABLE IF NOT EXISTS regions (
                                    code_region TEXT PRIMARY KEY,
                                    libelle_region TEXT
                                  );'''

    try:
        cursor = conn.cursor()
        cursor.execute(create_sites_table)
        cursor.execute(create_stations_table)
        cursor.execute(create_communes_table)
        cursor.execute(create_departements_table)
        cursor.execute(create_regions_table)
        conn.commit()
        print("Tables créées avec succès")
    except sqlite3.Error as e:
        print(f"Erreur lors de la création des tables: {e}")

# Fonction pour nettoyer les données (convertir les listes en chaînes)
def clean_data(value):
    """Nettoie les données en convertissant les listes en chaînes ou en retournant None"""
    if value is None:
        return None
    elif isinstance(value, list):
        # Si c'est une liste, prendre le premier élément s'il existe
        return value[0] if len(value) > 0 else None
    elif isinstance(value, (str, int, float)):
        return value
    else:
        return str(value)

# Fonction pour extraire les coordonnées de manière sécurisée
def get_coordinates(item):
    """Extrait les coordonnées de manière sécurisée"""
    try:
        geometry = item.get('geometry', {})
        coordinates = geometry.get('coordinates', [])
        if isinstance(coordinates, list) and len(coordinates) >= 2:
            longitude = coordinates[0] if isinstance(coordinates[0], (int, float)) else None
            latitude = coordinates[1] if isinstance(coordinates[1], (int, float)) else None
            return latitude, longitude
        return None, None
    except (KeyError, IndexError, TypeError):
        return None, None

# Récupérer les données de l'API
def recuperer_donnees(url):
    """
    Récupère toutes les données via l'API en gérant la pagination avec le champ 'next'.
    """
    all_data = []
    while url:
        try:
            response = requests.get(url)
            if response.status_code in [200, 206]:
                data = response.json()
                all_data.extend(data['data'])  # Ajoute les nouveaux documents à la liste
                url = data.get('next')  # Si 'next' est présent, continuer avec la nouvelle URL
            else:
                print(f"Erreur {response.status_code} lors de la récupération des données.")
                break
        except requests.RequestException as e:
            print(f"Erreur de requête: {e}")
            break
    return all_data

# Fonction pour insérer des données dans SQLite3
def insert_data(conn, data, table):
    """Insère des données dans la table spécifiée"""
    cursor = conn.cursor()
    
    # Filtrer les données vides ou None
    filtered_data = [row for row in data if row[0] is not None]
    
    if not filtered_data:
        print(f"Aucune donnée valide à insérer dans la table {table}")
        return

    try:
        if table == "sites":
            insert_query = '''INSERT OR IGNORE INTO sites (code_site, code_commune, libelle_site, libelle_cours_eau) 
                              VALUES (?, ?, ?, ?)'''
            cursor.executemany(insert_query, filtered_data)
        elif table == "stations":
            insert_query = '''INSERT OR IGNORE INTO stations (code_station, code_site, libelle_station, libelle_cours_eau, latitude_station, longitude_station, date_ouverture_station, en_service) 
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?)'''
            cursor.executemany(insert_query, filtered_data)
        elif table == "communes":
            insert_query = '''INSERT OR IGNORE INTO communes (code_commune, code_departement, libelle_commune) 
                              VALUES (?, ?, ?)'''
            cursor.executemany(insert_query, filtered_data)
        elif table == "departements":
            insert_query = '''INSERT OR IGNORE INTO departements (code_departement, code_region, libelle_departement) 
                              VALUES (?, ?, ?)'''
            cursor.executemany(insert_query, filtered_data)
        elif table == "regions":
            insert_query = '''INSERT OR IGNORE INTO regions (code_region, libelle_region) 
                              VALUES (?, ?)'''
            cursor.executemany(insert_query, filtered_data)

        conn.commit()
        print(f"{len(filtered_data)} enregistrements insérés dans la table '{table}'")
    except sqlite3.Error as e:
        print(f"Erreur lors de l'insertion dans {table}: {e}")
        # Afficher quelques exemples de données problématiques pour debug
        print("Exemples de données:")
        for i, row in enumerate(filtered_data[:3]):
            print(f"  Ligne {i+1}: {row}")
            for j, val in enumerate(row):
                print(f"    Paramètre {j+1}: {type(val)} = {val}")

# -----------------------------------------------------------------------------------------------------
print("Récupération des données des sites...")
data_sites = recuperer_donnees(url1)

# Traitement sécurisé des données des sites avec nettoyage
filtré1 = []
for item in data_sites:
    filtré1.append((
        clean_data(item.get('code_site')), 
        clean_data(item.get('code_commune_site')), 
        clean_data(item.get('libelle_site')), 
        clean_data(item.get('libelle_cours_eau'))
    ))

# -----------------------------------------------------------------------------------------------------
print("Récupération des données des stations...")
data_stations = recuperer_donnees(url2)

# Traitement sécurisé des données des stations
filtré2 = []
for item in data_stations:
    latitude, longitude = get_coordinates(item)
    filtré2.append((
        clean_data(item.get('code_station')), 
        clean_data(item.get('code_site')), 
        clean_data(item.get('libelle_station')), 
        clean_data(item.get('libelle_cours_eau')), 
        latitude,
        longitude,
        clean_data(item.get('date_ouverture_station')),
        clean_data(item.get('en_service'))
    ))

# -----------------------------------------------------------------------------------------------------
# Récupérer et insérer les données des communes, départements et régions
communes = list(set([(clean_data(item.get('code_commune_station')), 
                      clean_data(item.get('code_departement')), 
                      clean_data(item.get('libelle_commune'))) 
                    for item in data_stations 
                    if clean_data(item.get('code_commune_station'))]))

departements = list(set([(clean_data(item.get('code_departement')), 
                          clean_data(item.get('code_region')), 
                          clean_data(item.get('libelle_departement'))) 
                        for item in data_stations 
                        if clean_data(item.get('code_departement'))]))

regions = list(set([(clean_data(item.get('code_region')), 
                     clean_data(item.get('libelle_region'))) 
                   for item in data_stations 
                   if clean_data(item.get('code_region'))]))

# -----------------------------------------------------------------------------------------------------
# Suppression et connexion à la base SQLite3
db_file = 'hubleau.db'
drop_database(db_file)  # Supprimer la DB existante
conn = create_connection(db_file)

if conn:
    # Créer les tables
    create_tables(conn)
    
    # Insérer les données dans SQLite3 dans l'ordre des dépendances
    print("\nInsertion des données...")
    insert_data(conn, regions, "regions")
    insert_data(conn, departements, "departements")
    insert_data(conn, communes, "communes")
    insert_data(conn, filtré1, "sites")
    insert_data(conn, filtré2, "stations")
    
    # Fermer la connexion
    conn.close()
    print("\nImportation terminée avec succès!")
else:
    print("Impossible de se connecter à la base de données")
