from yahoo_fin.stock_info import get_data
from yahoo_fin.stock_info import get_currencies


amazon_weekly= get_data("amzn", start_date="12/04/2009", end_date="12/04/2019", index_as_date = True, interval="1wk")
print(amazon_weekly)


a = get_currencies()
print(a)
