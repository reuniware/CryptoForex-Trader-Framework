Ichimoku Scanner

For now the file is named "Ichimoku2022_Multithreaded.py"

Example of use :

python Ichimoku2022_Multithreaded.py -e binance -f *usdt -t
- Condition of scan by default (C1) : Price above all its Ichimoku levels and Chikou above all its Ichimoku levels and above its price
- This will scan all assets ending with USDT on the BINANCE exchange.
- This will scan for assets that might be trending (C1 on at least 1m or 3m or 5m or 15m).
- Scan results will be written to results.txt file (if -t then only trending assets)

python Ichimoku2022_Multithreaded.py -e binance -f *usdt -t

