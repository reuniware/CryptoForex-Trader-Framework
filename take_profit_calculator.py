# Given a high price and a low price, calculates the high price + 1/4 of the difference between high and low

phigh = 21388
plow = 20637

tp_level = ((phigh - plow)/4) + phigh

print("tp level =", str(tp_level))
