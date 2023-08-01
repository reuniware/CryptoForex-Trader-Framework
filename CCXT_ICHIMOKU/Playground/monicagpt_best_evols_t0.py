import requests
import time

url = "https://api.binance.com/api/v3/ticker/price"
first_prices = {}
previous_prices = {}
start_time = time.time()

while True:
    response = requests.get(url)

    if response.status_code == 200:
        prices = response.json()
        changes = {}
        if not first_prices:
            for price in prices:
                symbol = price['symbol']
                if symbol.endswith("USDT"):
                    current_price = float(price['price'])
                    first_prices[symbol] = current_price
        else:
            current_time = time.time() - start_time
            for price in prices:
                symbol = price['symbol']
                if symbol.endswith("USDT"):
                    current_price = float(price['price'])
                    if symbol in previous_prices:
                        previous_price = previous_prices[symbol]
                        price_diff = current_price - previous_price
                        percent_change = (price_diff / first_prices[symbol]) * 100
                        if percent_change > 0:
                            changes[symbol] = percent_change
                    previous_prices[symbol] = current_price

            sorted_changes = sorted(changes.items(), key=lambda x: x[1], reverse=True)
            output = ""
            for symbol, change in sorted_changes[:10]:
                output += f"{current_time:.2f}s - {symbol}: {change:.2f}%\n"
            with open("result.txt", "w") as f:
                f.write(output)
            
            print(output)

    else:
        print("Error retrieving prices")

    time.sleep(10)
