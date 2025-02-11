import os
import time

import csv
import logging

# Diretório para CSVs
CSV_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "csv")
CSV_FILE = os.path.join(CSV_DIR, f"trade_log_{time.strftime('%y%m%d%H%M%S')}.csv")

# Criar diretório se não existir
os.makedirs(CSV_DIR, exist_ok=True)


# Inicializar CSV se não existir
def initialize_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["timestamp", "type", "price", "amount"])


# Registrar uma operação no CSV
def log_trade(order_type, price, amount):
    try:
        with open(CSV_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                time.strftime("%Y-%m-%d %H:%M:%S"),
                order_type,
                price,
                amount
            ])
        logging.info(f"[CSV] Ordem registrada: {order_type} a {price} USDT com {amount} USDT")
    except Exception as e:
        logging.error(f"Erro ao registrar trade no CSV: {str(e)}")
