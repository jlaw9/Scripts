import logging


# -----------------------------------------------------------
# ----------- FUNCTIONS DEFINED HERE ------------------------
# -----------------------------------------------------------


logger = None

def create_logger(log_file, filemode):
    global logger
    logging.basicConfig(filename=log_file,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        filemode=filemode,
                        level=logging.INFO)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-8s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    logger = logging.getLogger('LOGGER')

def get_logger():
    global logger
    return logger



