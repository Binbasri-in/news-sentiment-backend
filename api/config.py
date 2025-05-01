import logging

def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        filename='app.log',  # Log file name
        filemode='a'         # Append mode
    )
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)  # Optional: Adjust SQLAlchemy logging level