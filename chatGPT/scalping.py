import os
import sys
import time

import numpy as np
import pandas as pd
from binance import BinanceAPIException
from binance.client import Client

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config
from tools.csv import initialize_csv, log_trade
from tools.logging import setup_logging, log_message

# Inicializar logging e CSV
setup_logging()
initialize_csv()

# Inicializa a API da Binance
client = Client(api_key=config.API, api_secret=config.KEY)

# Configurações do par de trading e período
ticker = "BTCBRL"
timeframe = "1m"  # 1 minuto

# Modo de simulação (True = apenas logs, False = execução real)
SIMULATED_MODE = True

# Percentual do saldo disponível a ser investido em cada operação
TRADE_PERCENTAGE = 0.05  # 5%


# Função para obter saldo disponível
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
        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["volume"] = df["volume"].astype(float)
        return df[["timestamp", "open", "close", "high", "low", "volume"]]
    except BinanceAPIException as e:
        log_message("error", f"Erro ao obter dados históricos: {e.message}")
        return None


# Função para calcular indicadores
def calculate_indicators(df):
    try:
        df["EMA_5"] = df["close"].ewm(span=5, adjust=False).mean()
        df["EMA_13"] = df["close"].ewm(span=13, adjust=False).mean()
        delta = df["close"].diff(1)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, abs(delta), 0)
        avg_gain = pd.Series(gain).rolling(window=14).mean()
        avg_loss = pd.Series(loss).rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df["RSI"] = 100 - (100 / (1 + rs))
        return df
    except BinanceAPIException as e:
        log_message("error", f"Erro ao calcular indicadores: {e.message}")
        return None


# Função para verificar sinais de trade
def check_signals(df):
    try:
        last_row = df.iloc[-1]
        previous_row = df.iloc[-2]
        prev_prev_row = df.iloc[-3]

        log_message("info",
                    f"Última vela: Preço {last_row['close']}, EMA5: {last_row['EMA_5']}, EMA13: {last_row['EMA_13']}, RSI: {last_row['RSI']}")

        if (prev_prev_row["EMA_5"] < prev_prev_row["EMA_13"] and previous_row["EMA_5"] < previous_row["EMA_13"] and
            last_row["EMA_5"] > last_row["EMA_13"]) and last_row["RSI"] < 40:
            log_message("info", "📈 Sinal de COMPRA detectado!")
            execute_trade("BUY", last_row["close"])
        elif (prev_prev_row["EMA_5"] > prev_prev_row["EMA_13"] and previous_row["EMA_5"] > previous_row["EMA_13"] and
              last_row["EMA_5"] < last_row["EMA_13"]) and last_row["RSI"] > 60:
            log_message("info", "📉 Sinal de VENDA detectado!")
            execute_trade("SELL", last_row["close"])
    except BinanceAPIException as e:
        log_message("error", f"Erro ao verificar sinais de trade: {e.message}")


# Função para executar trade simulado
def execute_trade(order_type, price):
    order_amount = get_balance("BRL") * TRADE_PERCENTAGE
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
            df = calculate_indicators(df)
            if df is not None:
                check_signals(df)
        time.sleep(10)  # Atualiza a cada 10 segundos
