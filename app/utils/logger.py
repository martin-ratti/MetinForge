import logging
import os
import sys
from datetime import datetime


def setup_logger(name="MetinForge"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '[%(asctime)s] | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        try:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
            os.makedirs(log_dir, exist_ok=True)
            fh = logging.FileHandler(os.path.join(log_dir, "app.log"), encoding='utf-8')
            fh.setFormatter(formatter)
            logger.addHandler(fh)
            
            fh.stream.write("\n" + "=" * 80 + "\n")
            fh.stream.write(f"  SESSION STARTED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            fh.stream.write("=" * 80 + "\n\n")
            
        except Exception as e:
            print(f"Failed to setup file logging: {e}")
            
    return logger


logger = setup_logger()


def log_db_operation(operation: str, table: str, count: int = 0, details: str = ""):
    """Registra operaciones de base de datos relevantes."""
    msg = f"DB {operation.upper()} | {table}"
    if count:
        msg += f" | {count} registros"
    if details:
        msg += f" | {details}"
    logger.info(msg)


def log_import(source: str, accounts: int = 0, errors: int = 0):
    """Registra importaciones de datos."""
    msg = f"IMPORT | {source} | {accounts} cuentas procesadas"
    if errors:
        msg += f" | {errors} errores"
        logger.warning(msg)
    else:
        logger.info(msg)


def log_user_action(action: str, context: str = ""):
    """Registra acciones del usuario en la UI."""
    msg = f"USER ACTION | {action}"
    if context:
        msg += f" | {context}"
    logger.info(msg)
