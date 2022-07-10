
initialbalance = 100
finalbalance = initialbalance
for x in range(365):
    finalbalance = finalbalance + (finalbalance/100) * 2

print("finalbalance=", finalbalance)
