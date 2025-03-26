import requests
from functools import lru_cache
import sys

BASE_URL = "https://jdm-api.demo.lirmm.fr"
session = requests.Session()

@lru_cache(maxsize=32)
def fetch_relation_types():
    try:
        response = session.get(f"{BASE_URL}/v0/relations_types")
        response.raise_for_status()
        data = response.json()
        rels = {r["id"]: r for r in data}
        rels.update({r["name"]: r for r in data})
        rels.update({r["gpname"]: r for r in data})
        return rels
    except:
        return {}

def apply_annotation_boost(weight, annotations):
    if "impossible" in annotations:
        return 0
    if "pertinent" in annotations:
        return weight * 1.2
    if "probable" in annotations:
        return weight * 1.1
    return weight

def get_relation_from_graph(source, relation_id, inverse=False):
    url = f"{BASE_URL}/graph/{source}"
    params = {"inverse": str(inverse).lower()}
    try:
        response = session.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        results = []
        for rel in data.get("relations", []):
            if rel["type"] == relation_id:
                target = rel.get("node2", rel.get("node1"))
                weight = rel.get("w", 0)
                annotations = rel.get("annotations", [])
                boosted = apply_annotation_boost(weight, annotations)
                results.append({
                    "source": source if not inverse else target,
                    "target": target if not inverse else source,
                    "relation_id": relation_id,
                    "weight": weight,
                    "boosted_weight": boosted,
                    "annotations": annotations
                })
        return results
    except Exception as e:
        print(f"⚠️ Erreur lors de l'accès à {source} : {e}")
        return []

def semantic_schema_inference(start_term, schema_path, end_term, min_score=0.25):
    relation_types = fetch_relation_types()
    steps = []

    current_term = start_term
    total_score = 1.0

    for rel_name in schema_path:
        rel_info = relation_types.get(rel_name)
        if not rel_info:
            print(f"❌ Relation '{rel_name}' non trouvée.")
            return []

        rel_id = rel_info["id"]
        candidates = get_relation_from_graph(current_term, rel_id)
        if not candidates:
            candidates = get_relation_from_graph(current_term, rel_id, inverse=True)

        if not candidates:
            print(f"❌ Aucune relation trouvée pour {current_term} via {rel_name}")
            return []

        best = max(candidates, key=lambda x: x["boosted_weight"])
        total_score *= best["boosted_weight"]
        steps.append(best)
        current_term = best["target"]

    if current_term.lower() != end_term.lower():
        syn_id = relation_types.get("r_syn", {}).get("id")
        if syn_id:
            syn_links = get_relation_from_graph(current_term, syn_id)
            synonymes = [link["target"].lower() for link in syn_links]
            if end_term.lower() not in synonymes:
                print(f"❌ Le chemin aboutit à '{current_term}' mais ce n’est pas '{end_term}', même via r_syn.")
                return []
            else:
                print(f"ℹ️ Fin de chaîne reliée à '{end_term}' via r_syn.")
                total_score *= 0.9

    if total_score < min_score:
        print(f"❌ Score trop faible : {total_score:.2f} < {min_score}")
        return []

    print(f"\nTest '{start_term} → {' → '.join(schema_path)} → {end_term}' :")
    for i, step in enumerate(steps, 1):
        print(f"√ Étape {i} : {step['source']} → {step['target']} via {schema_path[i-1]} "
              f"(poids {step['weight']:.2f}, boosté {step['boosted_weight']:.2f}, annotations: {step['annotations']})")
    print(f"✅ Score total : {total_score:.2f} [OK]\n")

    return {
        "start": start_term,
        "end": end_term,
        "path": schema_path,
        "intermediate": [step["target"] for step in steps[:-1]],
        "score": total_score,
        "steps": steps
    }

# === MAIN CLI EXECUTION ===
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("❗ Utilisation : python3 reffinement.py <terme1> <relation1,relation2,...> <terme2>")
        print("Exemple : python3 reffinement.py soudeur r_processus>agent-1,r_verbe-action-1 souder")
        sys.exit(1)

    term_start = sys.argv[1]
    relations = sys.argv[2].split(",")
    term_end = sys.argv[3]

    semantic_schema_inference(term_start, relations, term_end)
