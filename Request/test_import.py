import requests
import pandas as pd

# URL de l'API Hub'Eau
url = "https://hubeau.eaufrance.fr/api/v2/hydrometrie/observations_tr"

# Paramètres de la requête
params = {
    "code_entite": "Y251002001",
    "grandeur_hydro": "H",
    "fields": "code_station,date_obs,resultat_obs",
    "size": 10
}

# Envoi de la requête
response = requests.get(url, params=params)

# Vérification du statut HTTP
if response.status_code in [200, 206]:
    data = response.json().get("data", [])

    # Création d'un DataFrame Pandas
    df = pd.DataFrame(data)

    # Affichage du tableau
    print(df)

else:
    print(f"Erreur {response.status_code} : Impossible de récupérer les données.")
