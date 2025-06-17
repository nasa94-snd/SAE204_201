from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import math
import requests
import json
from datetime import datetime, timedelta
from models import *

app = Flask(__name__)

# Initialize database manager
db_manager = DatabaseManager()

@app.route('/')
def index():
    """Page d'accueil avec carte interactive des stations"""
    try:
        print("DEBUG: Début de la fonction index()")
        
        # Récupérer TOUTES les stations avec coordonnées pour la carte
        stations, total = db_manager.get_stations_with_coordinates()
        print(f"DEBUG: Récupéré {total} stations pour la carte")
        
        # Convertir en format dictionnaire pour faciliter l'usage dans le template
        stations_data = []
        for station in stations:
            station_data = {
                'code_station': station[0],
                'libelle_station': station[1],
                'libelle_site': station[2],
                'libelle_region': station[3],
                'libelle_departement': station[4],
                'en_service': station[5],
                'date_ouverture_station': station[6],
                'latitude_station': station[7],
                'longitude_station': station[8]
            }
            stations_data.append(station_data)
        
        print(f"DEBUG: {len(stations_data)} stations préparées pour affichage")
        
        return render_template('index.html', 
                             stations=stations_data,
                             total_stations=total)
                             
    except Exception as e:
        print(f"ERREUR dans index(): {e}")
        import traceback
        traceback.print_exc()
        return render_template('index.html', 
                             stations=[],
                             total_stations=0,
                             error_message=f"Erreur: {str(e)}")

@app.route('/recherche_filtre')
def recherche_filtre():
    """Page de recherche avec liste des stations et filtres"""
    # Paramètres de pagination
    page = int(request.args.get('page', 1))
    per_page = 12
    
    # Filtres
    region_filter = request.args.get('region')
    departement_filter = request.args.get('departement')
    site_filter = request.args.get('site')
    search_query = request.args.get('search', '').strip()
    
    # Récupération des données
    stations, total = db_manager.get_stations(
        page=page, 
        per_page=per_page,
        region_filter=region_filter,
        departement_filter=departement_filter,
        site_filter=site_filter,
        search_query=search_query
    )
    
    # Calcul de la pagination
    total_pages = math.ceil(total / per_page)
    
    # Données pour les filtres
    regions = db_manager.get_regions()
    departements = db_manager.get_departements(region_filter)
    sites = db_manager.get_sites(departement_filter)
    
    return render_template('recherche_filtre.html', 
                         stations=stations,
                         regions=regions,
                         departements=departements,
                         sites=sites,
                         current_page=page,
                         total_pages=total_pages,
                         total_stations=total,
                         region_filter=region_filter,
                         departement_filter=departement_filter,
                         site_filter=site_filter,
                         search_query=search_query)

@app.route('/station/<code_station>')
def station_detail(code_station):
    """Page de détail d'une station avec graphiques"""
    # Récupérer les détails de la station
    station = db_manager.get_station_details(code_station)
    
    if not station:
        return redirect(url_for('recherche_filtre'))
    
    # Paramètres de dates et grandeur depuis l'URL
    date_debut_url = request.args.get('date_debut')
    date_fin_url = request.args.get('date_fin')
    grandeur_hydro = request.args.get('grandeur_hydro')
    
    # Récupérer les dates intelligentes pour cette station
    smart_debut, smart_fin = get_smart_dates_for_station(code_station)
    
    # Utiliser les dates de l'URL si spécifiées, sinon les dates intelligentes
    date_debut = date_debut_url if date_debut_url else smart_debut
    date_fin = date_fin_url if date_fin_url else smart_fin
    
    # Récupérer les grandeurs disponibles pour cette station
    available_grandeurs = get_available_grandeurs(code_station)
    
    # Récupérer les mesures avec les filtres
    measurements = get_station_measurements(code_station, date_debut, date_fin, grandeur_hydro)
    
    # Préparer les données pour le graphique
    chart_data = prepare_chart_data(measurements)
    
    # Calculer les statistiques
    stats = calculate_stats(chart_data, measurements)
    
    return render_template('station_detail.html',
                         station=station,
                         chart_data=chart_data,
                         chart_data_json=json.dumps(chart_data),
                         stats=stats,
                         date_debut=date_debut,
                         date_fin=date_fin,
                         grandeur_hydro=grandeur_hydro,
                         available_grandeurs=list(available_grandeurs.keys()),
                         dates_automatiques=not (date_debut_url or date_fin_url))

@app.route('/api/stations-geojson')
def api_stations_geojson():
    """API endpoint pour récupérer les stations au format GeoJSON pour la carte"""
    stations, total = db_manager.get_stations_with_coordinates()
    
    features = []
    for station in stations:
        if station[7] and station[8]:  # latitude et longitude
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [station[8], station[7]]  # [longitude, latitude]
                },
                "properties": {
                    "code_station": station[0],
                    "libelle_station": station[1],
                    "libelle_site": station[2],
                    "libelle_region": station[3],
                    "libelle_departement": station[4],
                    "en_service": station[5],
                    "date_ouverture_station": station[6]
                }
            }
            features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    return jsonify(geojson)

@app.route('/api/station-latest-measurement/<code_station>')
def api_station_latest_measurement(code_station):
    """API pour récupérer la dernière mesure d'une station"""
    grandeur = request.args.get('grandeur', 'H')
    
    # Récupérer les détails de la station
    station = db_manager.get_station_details(code_station)
    if not station:
        return jsonify({'error': 'Station non trouvée'}), 404
    
    # Récupérer la dernière mesure
    try:
        url = "https://hubeau.eaufrance.fr/api/v2/hydrometrie/obs_elab"
        params = {
            'code_entite': code_station,
            'grandeur_hydro_elab': grandeur,
            'format': 'json',
            'size': 1,
            'sort': 'desc'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code in [200, 206]:
            data = response.json()
            measurements = data.get('data', [])
            
            if measurements:
                measurement = measurements[0]
                valeur_brute = measurement.get('resultat_obs_elab')
                valeur_convertie, unite = convert_value_with_unit(valeur_brute, grandeur)
                
                return jsonify({
                    'station': station,
                    'measurement': {
                        'valeur': valeur_convertie,
                        'unite': unite,
                        'grandeur': grandeur,
                        'date': measurement.get('date_obs_elab'),
                        'valeur_brute': valeur_brute
                    }
                })
            else:
                # Essayer sans filtre de grandeur
                params.pop('grandeur_hydro_elab', None)
                response = requests.get(url, params=params, timeout=10)
                if response.status_code in [200, 206]:
                    data = response.json()
                    measurements = data.get('data', [])
                    if measurements:
                        measurement = measurements[0]
                        valeur_brute = measurement.get('resultat_obs_elab')
                        grandeur_detectee = measurement.get('grandeur_hydro_elab', 'INCONNUE')
                        valeur_convertie, unite = convert_value_with_unit(valeur_brute, grandeur_detectee)
                        
                        return jsonify({
                            'station': station,
                            'measurement': {
                                'valeur': valeur_convertie,
                                'unite': unite,
                                'grandeur': grandeur_detectee,
                                'date': measurement.get('date_obs_elab'),
                                'valeur_brute': valeur_brute
                            }
                        })
                
                return jsonify({
                    'station': station,
                    'measurement': None,
                    'message': 'Aucune mesure disponible'
                })
        else:
            return jsonify({
                'station': station,
                'measurement': None,
                'error': f'Erreur API: {response.status_code}'
            })
            
    except Exception as e:
        print(f"Erreur API: {e}")
        return jsonify({
            'station': station,
            'measurement': None,
            'error': str(e)
        })


@app.route('/api/stations')
def api_stations():
    """API endpoint pour récupérer les stations en JSON"""
    region_filter = request.args.get('region')
    departement_filter = request.args.get('departement')
    site_filter = request.args.get('site')
    
    stations, total = db_manager.get_stations(
        page=1,
        per_page=1000,  # Récupérer toutes les stations pour l'API
        region_filter=region_filter,
        departement_filter=departement_filter,
        site_filter=site_filter
    )
    
    return jsonify({
        'stations': [
            {
                'code_station': station[0],
                'libelle_station': station[1],
                'libelle_site': station[2],
                'libelle_region': station[3],
                'libelle_departement': station[4],
                'en_service': station[5],
                'date_ouverture_station': station[6]
            }
            for station in stations
        ],
        'total': total
    })

@app.route('/filter', methods=['POST'])
def apply_filter():
    """Route pour appliquer les filtres via formulaire POST"""
    region = request.form.get('region')
    departement = request.form.get('departement')
    site = request.form.get('site')
    search = request.form.get('search')
    
    # Construction des paramètres pour la redirection
    params = {}
    if region:
        params['region'] = region
    if departement:
        params['departement'] = departement
    if site:
        params['site'] = site
    if search:
        params['search'] = search
    
    return redirect(url_for('recherche_filtre', **params))

@app.route('/reset')
def reset_filters():
    """Route pour réinitialiser tous les filtres"""
    return redirect(url_for('recherche_filtre'))

def prepare_chart_data(measurements):
    """Prépare les données pour le graphique"""
    chart_data = {
        'labels': [],
        'values': []
    }
    
    for measurement in measurements:
        if measurement.get('resultat_obs_elab') is not None:
            grandeur = measurement.get('grandeur_hydro_elab', 'INCONNUE')
            valeur_brute = measurement.get('resultat_obs_elab')
            
            valeur_convertie, unite = convert_value_with_unit(valeur_brute, grandeur)
            
            if valeur_convertie is not None:
                date_str = measurement.get('date_obs_elab', '')
                if date_str:
                    try:
                        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
                    except:
                        formatted_date = date_str[:16]
                else:
                    formatted_date = 'Date inconnue'
                    
                chart_data['labels'].append(formatted_date)
                chart_data['values'].append(valeur_convertie)
    
    return chart_data

def calculate_stats(chart_data, measurements):
    """Calcule les statistiques des mesures"""
    detected_unit = "m"
    detected_grandeur = None
    
    if measurements:
        first_measurement = measurements[0]
        grandeur = first_measurement.get('grandeur_hydro_elab', 'INCONNUE')
        valeur_brute = first_measurement.get('resultat_obs_elab')
        if valeur_brute is not None:
            _, detected_unit = convert_value_with_unit(valeur_brute, grandeur)
            detected_grandeur = grandeur
    
    stats = {
        'total_mesures': len(measurements),
        'valeur_min': min(chart_data['values']) if chart_data['values'] else 0,
        'valeur_max': max(chart_data['values']) if chart_data['values'] else 0,
        'valeur_moyenne': sum(chart_data['values']) / len(chart_data['values']) if chart_data['values'] else 0,
        'unite': detected_unit,
        'grandeur': detected_grandeur
    }
    
    return stats

if __name__ == '__main__':
    app.run(debug=True)

