
initialbalance = 97.15
finalbalance = initialbalance
for x in range(365):
    balancebefore = finalbalance
    finalbalance = finalbalance + (finalbalance/100) * 0.5
    balanceafter = finalbalance
    print("j+", (x+1), "finalbalance=", finalbalance, "must win was=", balanceafter-balancebefore)

print("finalbalance=", finalbalance)

