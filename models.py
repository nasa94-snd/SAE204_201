import requests
import sqlite3
import datetime

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
    
    def get_stations(self, page=1, per_page=10, region_filter=None, departement_filter=None, site_filter=None):
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
    def get_nbr_stations(self):
        """Récupère le nombre total de stations"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM stations")
        total = cursor.fetchone()[0]
        conn.close()
        return total
db_manager = DatabaseManager()