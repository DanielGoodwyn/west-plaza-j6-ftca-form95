import logging
import sys
import os

logger = logging.getLogger(__name__)

def setup_logging(log_level_str='INFO', log_file=None):
    """
    Configures basic logging for the application.

    Args:
        log_level_str (str): The minimum log level to capture (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR').
        log_file (str, optional): Path to a file for logging. If None, logs only to console.
    """
    # Ensure log level is valid
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)

    # Basic configuration
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    handlers = []

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    handlers.append(console_handler)

    # File Handler (Optional)
    if log_file:
        try:
            # Ensure log directory exists if log_file includes a path
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
            handlers.append(file_handler)
        except Exception as e:
            # Log error about file handler setup to console
            # Use basicConfig temporarily to ensure this message gets out
            logging.basicConfig(level=logging.ERROR)
            logging.error(f"Failed to set up file logging handler for {log_file}: {e}", exc_info=True)
            # We might want to remove the partially configured basicConfig logger after this
            # For simplicity here, we just log the error and proceed without file logging

    # Apply basic config with handlers
    logging.basicConfig(level=log_level, format=log_format, datefmt=date_format, handlers=handlers, force=True)

    # Example: You can get a specific logger for your app module
    # logger = logging.getLogger('src.app') # Or just __name__ in the module using it
    # logger.info("Logging configured.")

# Example usage (usually called from your main app script)
# if __name__ == '__main__':
#     setup_logging(log_level_str='DEBUG', log_file='app.log')
#     logging.info("This is an info message.")
#     logging.warning("This is a warning.")
#     logging.debug("This is a debug message.")
