Ichimoku Scanner - INELIDAScanner (Part of Ichimoku Analyst Framework)

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
                                                                                                                                  

Latest options added :

-gott for assets that are getting over the tenkan

-gutt for assets that are getting below the tenkan

-iotc for assets that are over the cloud

-iutc for assets that are under the cloud

-hgotk for assets that have got over the kijun (close n-2 < kijun and close n-1 > kijun and close n > kijun) ; close n = current (close) price 
                                                                                                                                  
-l or --loop for scanning in loop (no need to use the "while true" trick anymore described some lines above)
  
  
  
 The IchimokuAnalystFramework: The Game-Changer for Cryptocurrency Analysis

As the cryptocurrency industry continues to evolve and grow, so does the need for sophisticated and comprehensive analytical tools to help investors navigate this complex and ever-changing landscape. The IchimokuAnalystFramework is the answer to this need, providing users with the most advanced analysis system available for cryptocurrencies.

Developed over eight years of experimental research, the IchimokuAnalystFramework is the most efficient and pertinent software in the world for analyzing all cryptocurrencies using the Ichimoku system and all criteria available in this type of analysis. The framework stands out from its competitors as it allows traders and investors to easily analyze and understand market trends and behavior, identify potential buying and selling opportunities, and make informed trading decisions.

Additionally, the IchimokuAnalystFramework is user-friendly, making it accessible even to those without extensive knowledge in technical analysis. Its clear and intuitive interface allows all users, regardless of their skill level, to easily assess trends, monitor indicators and alerts, and compare performance across various cryptocurrencies.

Overall, the IchimokuAnalystFramework is a game-changer in cryptocurrency analysis, revolutionizing the way investors approach trading in this fast-paced and dynamic market. With its advanced features and user-friendly interface, every trader can gain confidence and security in their cryptocurrency trading decisions.


