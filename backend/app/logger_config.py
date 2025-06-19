import logging

def setup_logging():
    """
    Configures the logging settings for the application.
    Logs will be written to both console and a file named 'app.log'.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s %(levelname)s %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log', mode='w', encoding='utf-8')
        ]
    )
    logger_config = {
        "watchfiles.main": logging.WARNING,
        "uvicorn.error": logging.INFO,
        "uvicorn.access": logging.INFO,
    }
    for logger_name, level in logger_config.items():
        logging.getLogger(logger_name).setLevel(level)

def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger with the specified name.
    
    Args:
        name (str): The name of the logger.
    
    Returns:
        logging.Logger: The configured logger instance.
    """
    return logging.getLogger("mailmind." + name)

