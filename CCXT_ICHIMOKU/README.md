Ichimoku Scanner - INELIDAScanner

For now the file is named "Ichimoku2022_Multithreaded.py"

Examples of use :

python Ichimoku2022_Multithreaded.py -e binance -f *usdt -t
- Condition of scan by default (C1) : Price above all its Ichimoku levels and Chikou above all its Ichimoku levels and above its price
- This will scan all assets ending with USDT on the BINANCE exchange.
- This will scan for assets that might be trending (C1 on at least 1m or 3m or 5m or 15m).
- Scan results will be written to results.txt file (as -t option is specified then only trending assets).
- the -f option can be used with the asterisk wildcard that can only be at the beginning or at the end of the filter string.

python Ichimoku2022_Multithreaded.py -e binance
- Condition of scan by default (C1) : Price above all its Ichimoku levels and Chikou above all its Ichimoku levels and above its price
- This will scan all assets on the BINANCE exchange.
- Scan results will be written to results.txt file.

python Ichimoku2022_Multithreaded.py -g
- Will list all available exchanges (for use with -e option).

python Ichimoku2022_Multithreaded.py -e binance -a
- Will list all available assets from BINANCE exchange.

python Ichimoku2022_Multithreaded.py -e binance -gotc
- "gotc" means "getting over the cloud". 
- Condition of scan (C2) : if SSA>SSB then OpenPrice<SSA and ClosePrice>SSA else if SSB>SSA then OpenPrice<SSB and ClosePrice>SSB
- Scan results will be written to results.txt file.

python Ichimoku2022_Multithreaded.py -e binance -f *usdt -t
- Condition of scan (C2) : if SSA>SSB then OpenPrice<SSA and ClosePrice>SSA else if SSB>SSA then OpenPrice<SSB and ClosePrice>SSB
- This will scan for assets that might be trending (C2 on at least 1m or 3m or 5m or 15m).
- This will scan all assets ending with USDT on the BINANCE exchange.
- Scan results will be written to results.txt file.

python Ichimoku2022_Multithreaded.py -e binance -gutc
- "gutc" means "getting under the cloud".
- Condition of scan (C3) : if SSB>SSA then OpenPrice>SSA and ClosePrice<SSA else if SSA>SSB then OpenPrice>SSB and ClosePrice<SSB
- Scan results will be written to results.txt file.
                                                                                                                                  
The -t option is to be used if you are searching for an asset to trade (very short term trading).

When using the -f option (to filter scanned assets), think of using an underscore for gateio, eg: ALAYA_USDT, BTC_USDT etc...

To monitor one asset in a shell environment :
                                                                                                                                  
while true; do python Ichimoku2022_Multithreaded.py -e binance -f santosusdt; done;

