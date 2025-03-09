import requests
import urllib3
import json

# Désactiver les warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_BASE = "https://jdm-api.demo.lirmm.fr/v0"

# Dictionnaire des types de relations
relation = {
    "r_isa": 6  # Relation "est un" (hyperonyme)
}

def getJson(node1, node2, rel):
    """ Effectue une requête pour récupérer la relation entre deux mots """
    urlR = f"{API_BASE}/relations/from/{node1}/to/{node2}?types_ids={rel}"
    
    try:
        r = requests.get(urlR, verify=False)
        r.raise_for_status()  # Vérifie si la requête a réussi
        return r.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la requête : {e}")
        return None

def save_to_file(data, filename):
    """ Sauvegarde les résultats dans un fichier JSON """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"📂 Résultat enregistré dans {filename}")
    except IOError as e:
        print(f"❌ Erreur d'écriture du fichier : {e}")

def main():
    """ Fonction principale """
    print("Entrez votre requête (format: mot1 relation mot2)")
    requete = input().strip()  # Supprime les espaces inutiles
    array = requete.split()

    if len(array) != 3:
        print("❌ Format incorrect. Utilisez : mot1 relation mot2")
        return 0

    node1, rel, node2 = array[0], array[1], array[2]

    # Vérifie si la relation est connue
    if rel in relation:
        rel_id = relation[rel]
    else:
        print(f"❌ Relation inconnue : {rel}. Utilisez : {list(relation.keys())}")
        return 0

    # Récupération des données JSON
    res = getJson(node1, node2, rel_id)

    if res and "relations" in res:
        if res["relations"]:
            poids = res["relations"][0].get("w", "N/A")
            print(f"✅ '{node1}' est relié à '{node2}' via '{rel}' (ID {rel_id}) avec un poids de {poids}.")
            
            # Enregistrer dans un fichier JSON
            filename = f"result_{node1}_{node2}.json"
            save_to_file(res, filename)

        else:
            print(f"❌ '{node1}' n'est PAS relié à '{node2}' via '{rel}'.")
    else:
        print("❌ Aucune donnée trouvée ou erreur API.")

if __name__ == "__main__":
    main()
