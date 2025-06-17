import sqlite3
import requests
from datetime import datetime, timedelta

class DatabaseManager:
    def __init__(self, db_path='hubleau.db'):
        self.db_path = db_path
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def get_regions(self):
        """Récupère toutes les régions"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT code_region, libelle_region FROM regions ORDER BY libelle_region")
        regions = cursor.fetchall()
        conn.close()
        return regions
    
    def get_departements(self, region_code=None):
        """Récupère les départements, optionnellement filtrés par région"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if region_code:
            cursor.execute("""
                SELECT DISTINCT code_departement, libelle_departement 
                FROM departements 
                WHERE code_region = ? 
                ORDER BY libelle_departement
            """, (region_code,))
        else:
            cursor.execute("""
                SELECT DISTINCT code_departement, libelle_departement 
                FROM departements 
                ORDER BY libelle_departement
            """)
        departements = cursor.fetchall()
        conn.close()
        return departements
    
    def get_sites(self, departement_code=None):
        """Récupère les sites, optionnellement filtrés par département"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if departement_code:
            cursor.execute("""
                SELECT DISTINCT s.code_site, s.libelle_site 
                FROM sites s
                JOIN communes c ON s.code_commune = c.code_commune
                WHERE c.code_departement = ?
                ORDER BY s.libelle_site
            """, (departement_code,))
        else:
            cursor.execute("""
                SELECT DISTINCT code_site, libelle_site 
                FROM sites 
                ORDER BY libelle_site
            """)
        sites = cursor.fetchall()
        conn.close()
        return sites
    
    def get_stations(self, page=1, per_page=10, region_filter=None, departement_filter=None, site_filter=None, search_query=None):
        """Récupère les stations avec pagination et filtres"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Construction de la requête avec filtres
        base_query = """
            SELECT st.code_station, st.libelle_station, s.libelle_site, 
                   r.libelle_region, d.libelle_departement, st.en_service,
                   st.date_ouverture_station
            FROM stations st
            JOIN sites s ON st.code_site = s.code_site
            JOIN communes c ON s.code_commune = c.code_commune
            JOIN departements d ON c.code_departement = d.code_departement
            JOIN regions r ON d.code_region = r.code_region
            WHERE 1=1
        """
        
        params = []
        
        if region_filter:
            base_query += " AND r.code_region = ?"
            params.append(region_filter)
        
        if departement_filter:
            base_query += " AND d.code_departement = ?"
            params.append(departement_filter)
        
        if site_filter:
            base_query += " AND s.code_site = ?"
            params.append(site_filter)
        
        if search_query:
            base_query += " AND (st.libelle_station LIKE ? OR st.code_station LIKE ? OR s.libelle_site LIKE ?)"
            search_param = f"%{search_query}%"
            params.extend([search_param, search_param, search_param])
        
        # Compter le total pour la pagination
        count_query = f"SELECT COUNT(*) FROM ({base_query}) as subquery"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Ajouter la pagination
        base_query += " ORDER BY st.libelle_station LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        
        cursor.execute(base_query, params)
        stations = cursor.fetchall()
        conn.close()
        
        return stations, total
    
    def get_station_details(self, code_station):
        """Récupère les détails complets d'une station"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT st.code_station, st.libelle_station, st.libelle_cours_eau,
                   st.latitude_station, st.longitude_station, st.date_ouverture_station,
                   st.en_service, s.libelle_site, s.code_site,
                   c.libelle_commune, c.code_commune,
                   d.libelle_departement, d.code_departement,
                   r.libelle_region, r.code_region
            FROM stations st
            JOIN sites s ON st.code_site = s.code_site
            JOIN communes c ON s.code_commune = c.code_commune
            JOIN departements d ON c.code_departement = d.code_departement
            JOIN regions r ON d.code_region = r.code_region
            WHERE st.code_station = ?
        """
        
        cursor.execute(query, (code_station,))
        station = cursor.fetchone()
        conn.close()
        
        if station:
            return {
                'code_station': station[0],
                'libelle_station': station[1],
                'libelle_cours_eau': station[2],
                'latitude_station': station[3],
                'longitude_station': station[4],
                'date_ouverture_station': station[5],
                'en_service': station[6],
                'libelle_site': station[7],
                'code_site': station[8],
                'libelle_commune': station[9],
                'code_commune': station[10],
                'libelle_departement': station[11],
                'code_departement': station[12],
                'libelle_region': station[13],
                'code_region': station[14]
            }
        return None

    def get_stations_with_coordinates(self):
        """Récupère TOUTES les stations avec leurs coordonnées pour la carte"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        print("DEBUG: Exécution de la requête get_stations_with_coordinates")
        
        base_query = """
            SELECT st.code_station, st.libelle_station, s.libelle_site, 
                   r.libelle_region, d.libelle_departement, st.en_service,
                   st.date_ouverture_station, st.latitude_station, st.longitude_station
            FROM stations st
            JOIN sites s ON st.code_site = s.code_site
            JOIN communes c ON s.code_commune = c.code_commune
            JOIN departements d ON c.code_departement = d.code_departement
            JOIN regions r ON d.code_region = r.code_region
            WHERE st.latitude_station IS NOT NULL 
            AND st.longitude_station IS NOT NULL
            ORDER BY st.libelle_station
        """
        
        print(f"DEBUG: Requête SQL: {base_query}")
        
        try:
            cursor.execute(base_query)
            stations = cursor.fetchall()
            print(f"DEBUG: Requête exécutée, {len(stations)} stations récupérées")
            
            if len(stations) > 0:
                print(f"DEBUG: Première station: {stations[0]}")
            
            conn.close()
            return stations, len(stations)
            
        except Exception as e:
            print(f"DEBUG: Erreur dans la requête: {e}")
            conn.close()
            return [], 0

def clean_date_format(date_str):
    """Nettoie et formate une date pour l'affichage et les inputs HTML"""
    if not date_str:
        return None
    
    try:
        if 'T' in str(date_str):
            return str(date_str).split('T')[0]
        elif len(str(date_str)) == 10 and '-' in str(date_str):
            return str(date_str)
        else:
            return str(date_str)[:10]
    except:
        return None

def convert_value_with_unit(value, grandeur):
    """Convertit une valeur selon sa grandeur pour un affichage cohérent"""
    if value is None:
        return None, "m"
    
    try:
        val = float(value)
        
        if grandeur == "HIXM":  # Hauteur d'eau
            if 100 <= val <= 10000:  # Probablement en centimètres
                return val / 100, "m"
            elif 1000 <= val <= 100000:  # Probablement en millimètres
                return val / 1000, "m"
            else:  # Déjà en mètres ou valeur atypique
                return val, "m"
        
        elif grandeur == "HIXnJ":  # Débit
            if val > 1000:  # Probablement en L/s
                return val / 1000, "m³/s"
            else:  # Déjà en m³/s
                return val, "m³/s"
        
        # Autres grandeurs : retourner tel quel
        return val, "unité inconnue"
        
    except (ValueError, TypeError):
        return None, "m"

def get_available_grandeurs(code_station):
    """Récupère les grandeurs disponibles pour une station avec leurs infos"""
    url = "https://hubeau.eaufrance.fr/api/v2/hydrometrie/obs_elab"
    params = {
        'code_entite': code_station,
        'format': 'json',
        'size': 100
    }
    
    grandeurs_info = {}
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code in [200, 206]:
            data = response.json()
            measurements = data.get('data', [])
            
            for measurement in measurements:
                grandeur = measurement.get('grandeur_hydro_elab')
                valeur = measurement.get('resultat_obs_elab')
                
                if grandeur and valeur is not None:
                    if grandeur not in grandeurs_info:
                        grandeurs_info[grandeur] = {
                            'valeurs_exemple': [],
                            'count': 0
                        }
                    
                    grandeurs_info[grandeur]['valeurs_exemple'].append(float(valeur))
                    grandeurs_info[grandeur]['count'] += 1
                    
                    if len(grandeurs_info[grandeur]['valeurs_exemple']) > 10:
                        grandeurs_info[grandeur]['valeurs_exemple'] = grandeurs_info[grandeur]['valeurs_exemple'][:10]
    
    except Exception as e:
        print(f"Erreur lors de la récupération des grandeurs: {e}")
    
    return grandeurs_info

def get_station_measurements(code_station, date_debut=None, date_fin=None, grandeur_hydro=None):
    """Récupère les mesures d'une station depuis l'API Hub'eau"""
    url = "https://hubeau.eaufrance.fr/api/v2/hydrometrie/obs_elab"
    params = {
        'code_entite': code_station,
        'format': 'json',
        'size': 1000
    }
    
    if date_debut:
        params['date_debut_obs_elab'] = date_debut
    if date_fin:
        params['date_fin_obs_elab'] = date_fin
    if grandeur_hydro:
        params['grandeur_hydro_elab'] = grandeur_hydro
    else:
        params['grandeur_hydro_elab'] = 'H'
    
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code in [200, 206]:
            data = response.json()
            measurements = data.get('data', [])
            
            if len(measurements) == 0 and not grandeur_hydro:
                params.pop('grandeur_hydro_elab', None)
                response = requests.get(url, params=params, timeout=30)
                if response.status_code in [200, 206]:
                    data = response.json()
                    measurements = data.get('data', [])
            
            return measurements
    except Exception as e:
        print(f"Erreur lors de la récupération des mesures: {e}")

    return []

def get_smart_dates_for_station(code_station):
    """Récupère les dates intelligentes pour une station spécifique"""
    try:
        conn = sqlite3.connect('hubleau.db')
        cursor = conn.cursor()
        cursor.execute("SELECT date_ouverture_station FROM stations WHERE code_station = ?", (code_station,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            date_debut = clean_date_format(result[0])
        else:
            date_debut = "2020-01-01"
    except Exception as e:
        date_debut = "2020-01-01"
    
    try:
        url = "https://hubeau.eaufrance.fr/api/v2/hydrometrie/obs_elab"
        params = {
            'code_entite': code_station,
            'format': 'json',
            'size': 1,
            'sort': 'desc'
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code in [200, 206]:
            data = response.json()
            measurements = data.get('data', [])
            
            if measurements:
                last_date_raw = measurements[0].get('date_obs_elab', '')
                date_fin = clean_date_format(last_date_raw)
                
                if not date_fin:
                    date_fin = datetime.now().strftime('%Y-%m-%d')
            else:
                date_fin = datetime.now().strftime('%Y-%m-%d')
        else:
            date_fin = datetime.now().strftime('%Y-%m-%d')
    except Exception as e:
        date_fin = datetime.now().strftime('%Y-%m-%d')
    
    return date_debut, date_fin

