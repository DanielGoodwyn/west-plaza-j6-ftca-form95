import logging
import sys
import os

logger = logging.getLogger(__name__)

def setup_logging(log_level_str='INFO', log_file='app.log'):
    """
    Configures unified logging for the application.
    All logs from all modules go to a single rotating app.log file (max 0.5MB, 1 backup).
    Only app.log (latest) and app.log.1 (previous) will exist at any time.
    Console logging is also enabled for development.
    """
    import logging.handlers
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Remove all existing handlers from root logger
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Rotating file handler: maxBytes=0.5MB, backupCount=1
    file_handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=524288, backupCount=1, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    file_handler.setLevel(log_level)

    # Console handler (for dev)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    console_handler.setLevel(log_level)

    logging.basicConfig(level=log_level, handlers=[file_handler, console_handler], force=True)

    # Ensure all loggers propagate to root
    logging.captureWarnings(True)
    logging.getLogger().propagate = True
    # Startup confirmation
    logging.info(f"Unified logging initialized: log_file={os.path.abspath(log_file)}, maxBytes=524288, backupCount=1")

    # Example: You can get a specific logger for your app module
    # logger = logging.getLogger('src.app') # Or just __name__ in the module using it
    # logger.info("Logging configured.")

# Example usage (usually called from your main app script)
# if __name__ == '__main__':
#     setup_logging(log_level_str='DEBUG', log_file='app.log')
#     logging.info("This is an info message.")
#     logging.warning("This is a warning.")
#     logging.debug("This is a debug message.")
