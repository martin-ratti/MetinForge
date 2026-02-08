import logging
import sys
import os

def setup_logger(name="MetinForge"):
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        # Aesthetic format: [Time] | LEVEL    | Message
        formatter = logging.Formatter('[%(asctime)s] | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S')
        
        # Console Handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # Optional: File Handler
        try:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
            os.makedirs(log_dir, exist_ok=True)
            fh = logging.FileHandler(os.path.join(log_dir, "app.log"))
            fh.setFormatter(formatter)
            logger.addHandler(fh)
            
            # Add session separator
            fh.stream.write("\n" + "="*80 + "\n")
            fh.stream.write(f" SESSION STARTED: {logging.Formatter('%(asctime)s').format(logging.LogRecord(None, None, None, None, None, None, None))}\n")
            fh.stream.write("="*80 + "\n")
            
        except Exception as e:
            print(f"Failed to setup file logging: {e}")
        
    return logger

logger = setup_logger()
