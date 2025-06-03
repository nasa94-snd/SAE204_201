import unittest
from Script_Automatique import (
    extraire_communes,
    extraire_regions,
    extraire_departements,
    extraire_stations
)

class TestImportStatic(unittest.TestCase):

    def setUp(self):
        self.sample_data = [
            {
                'code_commune': '123',
                'libelle_commune': 'Paris',
                'code_departement': '75',
                'code_region': '11',
                'libelle_region': 'Île-de-France',
                'libelle_departement': 'Paris',
                'code_station': 'S1',
                'code_site': 'SITE1',
                'libelle_station': 'Station Paris',
                'libelle_cours_eau': 'Seine',
                'geometry': {'coordinates': [2.35, 48.85]},
                'date_ouverture_station': '2000-01-01',
                'en_service': True
            },
            {
                'code_commune': '456',
                'libelle_commune': 'Lyon',
                'code_departement': '69',
                'code_region': '84',
                'libelle_region': 'Auvergne-Rhône-Alpes',
                'libelle_departement': 'Rhône',
                'code_station': 'S2',
                'code_site': 'SITE2',
                'libelle_station': 'Station Lyon',
                'libelle_cours_eau': 'Rhône',
                'geometry': {'coordinates': [4.83, 45.75]},
                'date_ouverture_station': '2005-01-01',
                'en_service': False
            },
            {
                'code_commune': '123',  # doublon
                'libelle_commune': 'Paris',
                'code_departement': '75',
                'code_region': '11',
                'libelle_region': 'Île-de-France',
                'libelle_departement': 'Paris',
                'code_station': 'S3',
                'code_site': 'SITE3',
                'libelle_station': 'Station Paris 2',
                'libelle_cours_eau': 'Seine',
                'geometry': {'coordinates': [2.36, 48.86]},
                'date_ouverture_station': '2010-01-01',
                'en_service': True
            }
        ]

    def test_extraire_communes(self):
        communes = extraire_communes(self.sample_data)
        self.assertEqual(len(communes), 2)
        self.assertIn({'_id': '123', 'code_departement': '75', 'libelle_commune': 'Paris'}, communes)

    def test_extraire_regions(self):
        regions = extraire_regions(self.sample_data)
        self.assertEqual(len(regions), 2)
        self.assertIn({'_id': '11', 'libelle_region': 'Île-de-France'}, regions)

    def test_extraire_departements(self):
        departements = extraire_departements(self.sample_data)
        self.assertEqual(len(departements), 2)
        self.assertIn({'_id': '75', 'code_region': '11', 'libelle_departement': 'Paris'}, departements)

    def test_extraire_stations(self):
        stations = extraire_stations(self.sample_data)
        self.assertEqual(len(stations), 3)
        self.assertEqual(stations[0]['code_station'], 'S1')
        self.assertEqual(stations[1]['longitude_station'], 45.75)

if __name__ == '__main__':
    unittest.main()