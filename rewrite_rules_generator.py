import pandas as pd
import re
import sys
from urllib.parse import urlparse, parse_qs, urlencode

def is_valid_url(url):
    # Vérifier si l'URL correspond à un format valide
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domaine
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ou adresse IP
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # adresse IPv6
        r'(?::\d+)?'  # port facultatif
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

def generate_htaccess_rules(csv_file_path):
    # Lire le fichier CSV
    df = pd.read_csv(csv_file_path, delimiter=';')

    # Initialiser une liste pour stocker les règles de redirection
    rewrite_rules = []
    rewrite_rules.append('#### Règles de redirection')

    # Parcourir chaque ligne du DataFrame pour créer les règles
    for index, row in df.iterrows():
        old_url = row['Anciennes URLs']
        new_url = row['Nouvelles URLs']

        # Vérifier si les valeurs sont manquantes
        if pd.isna(old_url) or pd.isna(new_url):
            print(f"Avertissement: Valeur manquante détectée à la ligne {index + 2}. Cette ligne sera ignorée.")
            continue

        # Vérifier si les URLs sont valides
        if not is_valid_url(old_url) or not is_valid_url(new_url):
            print(f"Erreur: URL invalide détectée à la ligne {index + 2}.")
            continue

       
        # Extraire le chemin de l'ancienne URL
        old_parsed_url = urlparse(old_url)
        old_path = old_parsed_url.path
        old_query = old_parsed_url.query
        new_parsed_url = urlparse(new_url)
        new_path = new_parsed_url.path

        # Vérifier si la nouvelle URL est différente de l'ancienne pour éviter les boucles
        if old_path != new_path:

            # Vérifier que le chemin n'est pas vide ou égal à '/'
            if old_path and old_path != '/':
                # Convertir le chemin en motif regex
                regex_pattern = "^" +  re.escape(old_path) + "$"

                # Ajouter une condition pour les paramètres si nécessaire
                if old_query:
                    # print(f"Paramètres de requête détectés: {old_query}")
                    query_dict = parse_qs(old_query)
                    encoded_query = urlencode(query_dict, doseq=True)
                    rewrite_cond = f"RewriteCond %{{QUERY_STRING}} ^{encoded_query}$"
                    rewrite_rules.append(rewrite_cond)

                # Créer une règle RedirectMatch
                rule = f"RewriteRule {regex_pattern} {new_url} [R=301,L]"
                rewrite_rules.append(rule)

    rewrite_rules.append('#### Fin règles de redirection')
    
    # Joindre toutes les règles en une seule chaîne avec des sauts de ligne
    htaccess_content = "\n".join(rewrite_rules)

    # Afficher ou sauvegarder le contenu du fichier .htaccess
    print(htaccess_content)

# Exemple d'utilisation
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python rewrite_rules_generator.py <chemin_vers_fichier_csv>")
    else:
        csv_file_path = sys.argv[1]
        generate_htaccess_rules(csv_file_path)
