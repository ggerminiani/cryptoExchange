import time

import pandas as pd
from binance import BinanceAPIException
from binance.client import Client

import config
from tools.csv import initialize_csv, log_trade
from tools.logging import setup_logging, log_message

# Inicializar logging e CSV
setup_logging()
initialize_csv()

# Inicializa a API da Binance
client = Client(api_key=config.API, api_secret=config.KEY)

# Configurações do robô
ticker = "BTCBRL"
timeframe = "1m"  # 1 minuto
TRADE_VARIATION = 0.02  # 2% de variação para comprar/vender
MAX_DRAWNDOWN = -0.10  # Stop loss total se cair 10%
MAX_CONSECUTIVE_BUYS = 3  # Número máximo de compras seguidas sem venda

last_buy_price = None
consecutive_buys = 0

SIMULATED_MODE = True


# Função para obter saldo
def get_balance(asset="BRL"):
    try:
        info = client.get_account()
        for balance in info["balances"]:
            if balance["asset"] == asset:
                return float(balance["free"])
    except BinanceAPIException as e:
        log_message("error", f"Erro ao obter saldo: {e.message}")
        return 0.0


# Função para obter dados históricos
def get_historical_data(symbol, interval, limit=50):
    try:
        candles = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume", "close_time",
                                            "quote_asset_volume", "trades", "taker_base_vol", "taker_quote_vol",
                                            "ignore"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit='ms')
        df["close"] = df["close"].astype(float)
        return df[["timestamp", "close"]]
    except BinanceAPIException as e:
        log_message("error", f"Erro ao obter dados históricos: {e.message}")
        return None


# Função principal de verificação de sinais
def check_signals(df):
    global last_buy_price, consecutive_buys
    last_price = df.iloc[-1]["close"]
    variation = (last_price - last_buy_price) / last_buy_price if last_buy_price else 0

    log_message("info", f"Último preço: {last_price}, Variação: {variation:.2%}")

    # Primeira compra
    if last_buy_price is None:
        last_buy_price = last_price
        log_message("info", "Primeira compra feita como referência.")
        return

    # Stop Loss Progressivo
    if variation < MAX_DRAWNDOWN:
        log_message("warning", "🚨 Stop loss ativado! Vendendo para evitar perdas excessivas.")
        execute_trade("SELL", last_price)
        last_buy_price = None
        consecutive_buys = 0
        return

    # Compra se a variação atingir o limiar e limite de compras ainda não foi atingido
    if variation <= -TRADE_VARIATION and consecutive_buys < MAX_CONSECUTIVE_BUYS:
        log_message("info", "📉 Comprando mais para diluir preço de entrada.")
        execute_trade("BUY", last_price)
        last_buy_price = last_price
        consecutive_buys += 1
        return

    # Venda se a variação atingir o limiar positivo
    if variation >= TRADE_VARIATION:
        log_message("info", "📈 Vendendo para realizar lucro.")
        execute_trade("SELL", last_price)
        last_buy_price = None
        consecutive_buys = 0


# Função para executar trade simulado
def execute_trade(order_type, price):
    order_amount = get_balance("BRL") * 0.05  # Compra com 5% do saldo
    if order_amount <= 0:
        log_message("warning", "Saldo insuficiente para executar a ordem.")
        return

    if SIMULATED_MODE:
        log_trade(order_type, price, order_amount)
        log_message("info", f"[SIMULAÇÃO] Ordem {order_type} executada a {price} BRL com {order_amount} BRL")
    else:
        try:
            order = client.order_market(symbol=ticker, side=order_type, quantity=order_amount)
            log_trade(order_type, price, order_amount)
            log_message("info", f"[REAL] Ordem {order_type} enviada com sucesso: {order}")
        except BinanceAPIException as e:
            log_message("error", f"Erro ao executar ordem real: {e.message}")


# Loop principal
if __name__ == "__main__":
    while True:
        df = get_historical_data(ticker, timeframe)
        if df is not None:
            check_signals(df)
        time.sleep(10)  # Atualiza a cada 10 segundos
