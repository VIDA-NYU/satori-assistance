import logging

def setup_logger(name, log_file, level=logging.INFO):
    """Function to set up a logger for a specified name and log file."""
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create a handler for writing to a file
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    # Create a logger and add the handler
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)

    # Adding a stream handler to output to console
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.ERROR)  # Set higher level for console
    logger.addHandler(stream_handler)

    return logger
