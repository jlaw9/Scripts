import logging


# -----------------------------------------------------------
# ----------- FUNCTIONS DEFINED HERE ------------------------
# -----------------------------------------------------------


class Logger:

    def __init__(self, log_file, filemode):
        self.__log_file = log_file
        self.__filemode = filemode


    def getLogger(self):
        logging.basicConfig(filename=self.__log_file,
                            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                            filemode=self.__filemode,
                            level=logging.DEBUG)
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(name)-8s: %(levelname)-8s %(message)s')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)

        logger = logging.getLogger('LOGGER')
        return logger

