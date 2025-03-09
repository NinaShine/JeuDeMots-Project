import requests
from functools import lru_cache


API_BASE = "https://jdm-api.demo.lirmm.fr/v0"
http_session = requests.Session()  # Session HTTP réutilisable pour optimiser les requêtes

@lru_cache(maxsize=32)
def fetch_relation_types(verbose=False):
    """
    Récupère les types de relations existants dans la base JDM et les met en cache.
    Retourne un dictionnaire indexé par ID, nom et gpname pour un accès rapide.
    """
    endpoint = f"{API_BASE}/relations_types"
    try:
        response = http_session.get(endpoint)
        response.raise_for_status()  # Lève une exception en cas d'erreur HTTP

        data = response.json()
        relations_index = {entry["id"]: entry for entry in data}
        relations_index.update({entry["name"]: entry for entry in data})
        relations_index.update({entry["gpname"]: entry for entry in data})

        if verbose:
            print(f"Relations récupérées ({len(relations_index)} entrées)")
        
        return relations_index

    except requests.RequestException as err:
        if verbose:
            print(f"Erreur lors de la récupération des relations : {err}")
        return {}

def infer_direct_relation(start_node, relation_type, target_node, verbose=False):
    """
    Vérifie l'existence d'une relation spécifique entre deux nœuds et retourne une liste de résultats.
    - `start_node` : Terme source
    - `relation_type` : Nom ou gpname de la relation
    - `target_node` : Terme cible
    """
    relations_dict = fetch_relation_types()

    relation_info = relations_dict.get(relation_type)
    if not relation_info:
        if verbose:
            print(f"Relation '{relation_type}' introuvable.")
        return []

    relation_id = relation_info.get("id")
    if relation_id is None:
        if verbose:
            print(f"L'ID de la relation '{relation_type}' est introuvable.")
        return []

    endpoint = f"{API_BASE}/relations/from/{start_node}/to/{target_node}?types_ids={relation_id}"
    
    try:
        response = http_session.get(endpoint)
        response.raise_for_status()  # Lève une erreur si la requête échoue
        data = response.json()

        extracted_relations = [(start_node, rel.get("w", 0)) for rel in data.get("relations", [])]

        if verbose:
            print(f"Relations trouvées : {extracted_relations}")

        return extracted_relations

    except requests.RequestException as err:
        if verbose:
            print(f"Erreur lors de la récupération des relations : {err}")
        return []

# Test 1 : Vérifier si "chat" est un agent du verbe "manger"
# infer_direct_relation("chat", "r_agent-1", "manger", verbose=True)
