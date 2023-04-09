# orobnat_dl
orobnat_dl is a tool to download water analysis reports from orobnat.sante.gouv.fr.
# Requirements
## System packages
* python3
* wkhtmltopdf
## Python packages
* requests
* beautifulsoup4
* pdfkit
# Usage
```
usage: orobnat_dl.py [-h] [--debug] [--dry-run] [--format [{PDF,HTML} ...]] [--region ID] [--liste-departements] [--departement ID] [--liste-communes] [--commune ID] [--liste-reseaux] [--reseau ID] [CHEMIN]

Cet outil permet de télécharger les résultats d'analyse d'eau potable depuis le site https://orobnat.sante.gouv.fr

positional arguments:
  CHEMIN                Chemin du répertoire d'export.

optional arguments:
  -h, --help            Afficher ce message d'aide.
  --debug               Afficher les informations de débogage.
  --dry-run             Afficher les actions à réaliser mais ne rien faire.
  --format [{PDF,HTML} ...]
                        Sélectionner le format d'export.
                        Défault : PDF
  --region ID           Sélectionner une région : 
                        84: AUVERGNE-RHONE-ALPES
                        27: BOURGOGNE-FRANCHE-COMTE
                        53: BRETAGNE
                        24: CENTRE-VAL DE LOIRE
                        94: CORSE
                        44: GRAND EST
                        01: GUADELOUPE
                        03: GUYANE
                        32: HAUTS-DE-FRANCE
                        11: ILE DE FRANCE
                        04: LA REUNION
                        02: MARTINIQUE
                        06: MAYOTTE
                        28: NORMANDIE
                        75: NOUVELLE-AQUITAINE
                        76: OCCITANIE
                        52: PAYS DE LA LOIRE
                        93: PROVENCE-ALPES-COTE D’AZUR
  --liste-departements  Afficher la liste des départements disponibles pour la région sélectionnée.
  --departement ID      Sélectionner un département.
  --liste-communes      Afficher la liste des communes disponibles pour le département sélectionné.
  --commune ID          Sélectionner une commune.
  --liste-reseaux       Afficher la liste des réseaux disponibles pour la commune sélectionnée.
  --reseau ID           Sélectionner un réseau.
  ```
