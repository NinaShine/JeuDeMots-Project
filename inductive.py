import requests
import concurrent.futures
from functools import lru_cache

# 🔗 Définition de l'URL de base et de la session HTTP persistante
API_ENDPOINT = "https://jdm-api.demo.lirmm.fr/v0"
http_client = requests.Session()

@lru_cache(maxsize=32)
def retrieve_relation_types():
    """
    Récupère les types de relations disponibles et les stocke sous plusieurs index.
    """
    try:
        response = http_client.get(f"{API_ENDPOINT}/relations_types")
        response.raise_for_status()
        data = response.json()

        relation_map = {entry["id"]: entry for entry in data}
        relation_map.update({entry["name"]: entry for entry in data})
        relation_map.update({entry["gpname"]: entry for entry in data})

        return relation_map
    except requests.RequestException as e:
        print(f"⚠️ Erreur de récupération des relations: {e}")
        return {}

@lru_cache(maxsize=128)
def fetch_relation_weight(middle_node, target_node, relation_id):
    """
    Vérifie et récupère le poids d'une relation entre un nœud intermédiaire et le nœud cible.
    """
    try:
        response = http_client.get(f"{API_ENDPOINT}/relations/from/{middle_node}/to/{target_node}?types_ids={relation_id}")
        response.raise_for_status()
        relations = response.json().get("relations", [])
        return relations[0].get("w", 0) if relations else None
    except requests.RequestException:
        return None

def scale_weights(data_list, weight_key, normalized_key):
    """
    Normalise les poids entre 0 et 1 en évitant les divisions par zéro.
    """
    if not data_list:
        return
    weights = [item[weight_key] for item in data_list]
    min_w, max_w = min(weights), max(weights)
    range_w = max_w - min_w

    for item in data_list:
        item[normalized_key] = 1.0 if range_w == 0 else (item[weight_key] - min_w) / range_w

def infer_inductive_relation(start_node, intermediate_relation, target_node):
    """
    Effectue une inférence inductive en passant par un nœud intermédiaire pour relier start_node à target_node.
    """
    threshold_weight = 1
    try:
        response = http_client.get(f"{API_ENDPOINT}/relations/from/{start_node}?types_ids=8&min_weight={threshold_weight}")
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"⚠️ Erreur: Impossible d'obtenir les relations pour {start_node} ({e})")
        return []

    node_mapping = {node["id"]: node["name"] for node in data.get("nodes", [])}
    
    # Construction de la première liste des nœuds intermédiaires
    intermediate_nodes = [
        {"middle_node": node_mapping.get(rel.get("node2"), "Inconnu"), "weight": rel.get("w", 0), "initial_relation": "r_hypo"}
        for rel in data.get("relations", [])
    ]
    scale_weights(intermediate_nodes, "weight", "normalized_weight")

    # Récupération de l'ID de la relation intermédiaire
    relation_types = retrieve_relation_types()
    relation_info = relation_types.get(intermediate_relation)
    if not relation_info:
        print(f"⚠️ Erreur: Relation '{intermediate_relation}' introuvable.")
        return []
    relation_id = relation_info.get("id")

    # Récupération des poids pour la relation intermédiaire en parallèle
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_results = {
            executor.submit(fetch_relation_weight, item["middle_node"], target_node, relation_id): item
            for item in intermediate_nodes
        }
        for future in concurrent.futures.as_completed(future_results):
            item = future_results[future]
            try:
                item["final_relation_weight"] = future.result()
            except Exception:
                item["final_relation_weight"] = None

    # Filtrer les entrées valides
    filtered_nodes = [item for item in intermediate_nodes if item.get("final_relation_weight") is not None]
    scale_weights(filtered_nodes, "final_relation_weight", "normalized_final_weight")

    # Calcul du score avec la moyenne harmonique
    results = [
        {
            "start_node": start_node,
            "initial_relation": "r_hypo",
            "middle_node": item["middle_node"],
            "final_relation": intermediate_relation,
            "target_node": target_node,
            "score": (
                2 * (item["normalized_weight"] * item["normalized_final_weight"])
                / (item["normalized_weight"] + item["normalized_final_weight"])
                if (item["normalized_weight"] + item["normalized_final_weight"]) > 0
                else 0
            )
        }
        for item in filtered_nodes
    ]

    return results
