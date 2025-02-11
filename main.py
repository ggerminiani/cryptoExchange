from binance import BinanceAPIException
from binance.client import Client

import config

client = Client(
    api_key=config.API,
    api_secret=config.KEY,
)

try:
    info = client.get_account()
    for item in info['balances']:
        if float(item['free']) > 0:
            print(item)
except BinanceAPIException as e:
    print(e.status_code)
    print(e.message)
