import requests
import concurrent.futures
from functools import lru_cache

API_ENDPOINT = "https://jdm-api.demo.lirmm.fr/v0"
http_client = requests.Session()

@lru_cache(maxsize=32)
def fetch_relation_types():
    try:
        res = http_client.get(f"{API_ENDPOINT}/relations_types")
        res.raise_for_status()
        data = res.json()
        rels = {r["id"]: r for r in data}
        rels.update({r["name"]: r for r in data})
        rels.update({r["gpname"]: r for r in data})
        return rels
    except:
        return {}

@lru_cache(maxsize=128)
def fetch_direct_relation(source, target, relation_id):
    url = f"{API_ENDPOINT}/relations/from/{source}/to/{target}?types_ids={relation_id}"
    try:
        response = http_client.get(url)
        response.raise_for_status()
        relations = response.json().get("relations", [])
        return relations[0].get("w", 0) if relations else None
    except:
        return None

def normalize_scores(data, weight_key, norm_key):
    if not data:
        return
    weights = [item[weight_key] for item in data]
    min_w, max_w = min(weights), max(weights)
    for item in data:
        item[norm_key] = (item[weight_key] - min_w) / (max_w - min_w) if max_w != min_w else 1.0

def transitive_inference(node_a, relation_name, node_b):
    """
    Vérifie s'il existe un lien transitif entre A → C → B pour une relation donnée.
    Ex : piston r_holo moteur, moteur r_holo voiture ⇒ piston r_holo voiture
    """
    relation_types = fetch_relation_types()
    relation_obj = relation_types.get(relation_name)
    if not relation_obj:
        print(f"⚠️ Relation '{relation_name}' inconnue.")
        return []

    relation_id = relation_obj.get("id")
    if relation_id is None:
        print(f"⚠️ ID manquant pour la relation '{relation_name}'.")
        return []

    # Étape 1 : trouver tous les C tels que A → C via relation_name
    try:
        url = f"{API_ENDPOINT}/relations/from/{node_a}?types_ids={relation_id}&min_weight=1"
        response = http_client.get(url)
        response.raise_for_status()
        data = response.json()
    except:
        print(f"⚠️ Échec de récupération des relations depuis {node_a}.")
        return []

    node_map = {n["id"]: n["name"] for n in data.get("nodes", [])}
    candidates = [
        {"middle_node": node_map.get(rel["node2"], "Inconnu"), "weight": rel["w"], "step1": True}
        for rel in data.get("relations", [])
    ]
    normalize_scores(candidates, "weight", "normalized_first")

    # Étape 2 : pour chaque C, chercher si C → B existe
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(fetch_direct_relation, item["middle_node"], node_b, relation_id): item
            for item in candidates
        }
        for future in concurrent.futures.as_completed(futures):
            item = futures[future]
            try:
                result = future.result()
                item["final_weight"] = result
            except:
                item["final_weight"] = None

    # Filtrer ceux qui ont un lien C → B
    valid_paths = [item for item in candidates if item.get("final_weight") is not None]
    normalize_scores(valid_paths, "final_weight", "normalized_second")

    # Calculer le score combiné (moyenne harmonique)
    results = []
    for item in valid_paths:
        nw1 = item["normalized_first"]
        nw2 = item["normalized_second"]
        score = 2 * nw1 * nw2 / (nw1 + nw2) if (nw1 + nw2) > 0 else 0
        results.append({
            "start_node": node_a,
            "middle_node": item["middle_node"],
            "end_node": node_b,
            "relation": relation_name,
            "score": score
        })

    return results

result = transitive_inference("piston", "r_holo", "voiture")
for r in result:
    print(f"{r['start_node']} → {r['middle_node']} → {r['end_node']} via {r['relation']} | score: {r['score']:.2f}")
