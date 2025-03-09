from direct import infer_direct_relation

# Test 1 : Vérifier si "chat" est un agent du verbe "manger"
result1 = infer_direct_relation("chat", "r_agent-1", "manger", verbose=True)
print(result1)

# Test 2 : Vérifier si "soleil" a une caractéristique "chaud"
result2 = infer_direct_relation("soleil", "r_carac", "chaud", verbose=True)
print(result2)

# Test 3 : Vérifier si "fromage" est lié à "lait" par une relation de matière
result3 = infer_direct_relation("fromage", "r_matière", "lait", verbose=True)
print(result3)
