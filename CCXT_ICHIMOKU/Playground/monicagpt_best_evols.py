import requests
import time

url = "https://api.binance.com/api/v3/ticker/price"
previous_prices = {}

while True:
    response = requests.get(url)

    if response.status_code == 200:
        prices = response.json()
        changes = {}
        for price in prices:
            symbol = price['symbol']
            current_price = float(price['price'])
            if symbol in previous_prices:
                previous_price = previous_prices[symbol]
                price_diff = current_price - previous_price
                percent_change = (price_diff / previous_price) * 100
                if percent_change > 0:
                    changes[symbol] = percent_change
            previous_prices[symbol] = current_price

        sorted_changes = sorted(changes.items(), key=lambda x: x[1], reverse=True)
        output = ""
        for symbol, change in sorted_changes[:10]:
            output += f"{symbol}: {change:.2f}%\n"
        print(output)
    else:
        print("Error retrieving prices")

    time.sleep(10)
