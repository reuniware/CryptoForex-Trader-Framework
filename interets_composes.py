
initialbalance = 99.87
finalbalance = initialbalance
for x in range(365):
    balancebefore = finalbalance
    finalbalance = finalbalance + (finalbalance/100) * 2
    balanceafter = finalbalance
    print(x, "finalbalance=", finalbalance, "must win=", balanceafter-balancebefore)

print("finalbalance=", finalbalance)
