from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import math
from models import *

app = Flask(__name__)

#@app.route('/')
#def acceuil():
 #   nbr_stations = db_manager.get_nbr_stations()
  #  return render_template('accueil.html', nbr_stations=nbr_stations)

@app.route('/')
def index():
    # Paramètres de pagination
    page = int(request.args.get('page', 1))
    per_page = 11
    
    # Filtres
    region_filter = request.args.get('region')
    departement_filter = request.args.get('departement')
    site_filter = request.args.get('site')
    
    # Si on change de région, on reset le département et le site
    if region_filter and not departement_filter:
        site_filter = None
    
    # Si on change de département, on reset le site
    if departement_filter and not site_filter:
        pass  # On garde le site si il est compatible
    
    # Récupération des données
    stations, total = db_manager.get_stations(
        page=page, 
        per_page=per_page,
        region_filter=region_filter,
        departement_filter=departement_filter,
        site_filter=site_filter
    )
    
    # Calcul de la pagination
    total_pages = math.ceil(total / per_page)
    
    # Données pour les filtres
    regions = db_manager.get_regions()
    departements = db_manager.get_departements(region_filter)
    sites = db_manager.get_sites(departement_filter)
    
    return render_template('index.html', 
                         stations=stations,
                         regions=regions,
                         departements=departements,
                         sites=sites,
                         current_page=page,
                         total_pages=total_pages,
                         total_stations=total,
                         region_filter=region_filter,
                         departement_filter=departement_filter,
                         site_filter=site_filter)

@app.route('/filter', methods=['POST'])
def apply_filter():
    """Route pour appliquer les filtres via formulaire POST"""
    region = request.form.get('region')
    departement = request.form.get('departement')
    site = request.form.get('site')
    
    # Construction des paramètres pour la redirection
    params = {}
    if region:
        params['region'] = region
    if departement:
        params['departement'] = departement
    if site:
        params['site'] = site
    
    return redirect(url_for('index', **params))

@app.route('/reset')
def reset_filters():
    """Route pour réinitialiser tous les filtres"""
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)