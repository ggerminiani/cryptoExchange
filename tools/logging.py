import os
import time

import logging

# Diretório para logs
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "logs")
LOG_FILE = os.path.join("..", LOG_DIR, f"trading_bot_{time.strftime('%y%m%d%H%M%S')}.log")

# Criar diretório se não existir
os.makedirs(LOG_DIR, exist_ok=True)


# Configuração de logging
def setup_logging():
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )


# Função para registrar logs
def log_message(level, message):
    if level == "info":
        logging.info(message)
    elif level == "warning":
        logging.warning(message)
    elif level == "error":
        logging.error(message)
    elif level == "critical":
        logging.critical(message)
    elif level == "debug":
        logging.debug(message)
    print(message)  # Exibe a mensagem no console também
