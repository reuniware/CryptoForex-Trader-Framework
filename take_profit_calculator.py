# Given a high price and a low price, calculates the high price + 1/4 of the difference between high and low

tp_type = "up"

phigh = 21388
plow = 20637

if tp_type == "up":
    tp_level = phigh + ((phigh - plow)/4)
elif tp_type == "down":
    tp_level = plow - ((phigh - plow)/4)

print("tp level =", str(tp_level))
