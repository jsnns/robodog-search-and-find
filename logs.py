import logging
import sys


class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    blue = "\x1b[34;20m"
    purple = "\x1b[35;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "[%(levelname)s] %(asctime)s: %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: blue + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


formatter = CustomFormatter()
std_out = logging.StreamHandler(sys.stdout)
std_out.setLevel(logging.INFO)
std_out.setFormatter(formatter)

logging.basicConfig(level=logging.DEBUG, handlers=[std_out])

logging.getLogger("datadog.dogstatsd").setLevel(logging.ERROR)
