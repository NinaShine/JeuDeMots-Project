from direct import infer_direct_relation
from inductive import infer_inductive_relation
from deductive import infer_deductive_relation

# Test 1 : Vérifier si "chat" est un agent du verbe "manger"
result1 = infer_direct_relation("chat", "r_agent-1", "manger", verbose=True)
print(result1)

# Test 2 : Vérifier si "soleil" a une caractéristique "chaud"
result2 = infer_direct_relation("soleil", "r_carac", "chaud", verbose=True)
print(result2)

# Test 3 : Vérifier si "fromage" est lié à "lait" par une relation de matière
result3 = infer_direct_relation("fromage", "r_matière", "lait", verbose=True)
print(result3)
print("-----------------------------------------------------------")
# test inductive 
# Test avec des mots différents
result4 = infer_inductive_relation("chien", "r_carac", "fidèle")
print(result4)

result5 = infer_inductive_relation("soleil", "r_matière", "énergie")
print(result5)

result6 = infer_inductive_relation("oiseau", "r_agent-1", "voler")
print(result6)

print("-----------------------------------------------------------")
# test deductive 
# 🔍 Test avec des mots différents
result7 = infer_deductive_relation("oiseau", "r_agent-1", "voler")
print(result7)

result8 = infer_deductive_relation("chien", "r_carac", "fidèle")
print(result8)

