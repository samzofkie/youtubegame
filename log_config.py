logging_level = "INFO"

std_format = {
    "formatters": {
        "default": { "format": "[%(asctime)s.%(msecs)03d] %(levelname)s %(name)s:%(module)s:%(funcName)s: %(message)s",
                     "datefmt": "%d/%b/%Y:%H:%M:%S"},
        "access": { "format": "[%(asctime)s.%(msecs)03d] %(message)s", "datefmt": "%d/%b/%Y:%H:%M:%S"}
    }
}
std_logger = {
    "loggers": {
        "": {"level": logging_level, "handlers": ["default"], "propagate": True},
        "app.access": { "level": logging_level,
                        "handlers": ["access_logs"],
                        "propagate": False, },
        "root": {"level": logging_level, "handlers": ["default"]},
    }
}
logging_handler = {
    "handlers": {
        "default": {
            #"level": logging_level,
            #"class": "logging.FileHandler",
            #"filename": "app.log",
            #"formatter": "default",
            #"delay": True, 
            "level": logging_level,
            "class": "logging.StreamHandler",
            "formatter": "default"
        },
        "access_logs": {
            #"level": logging_level,
            #"class": "logging.FileHandler",
            #"filename": "access.log",
            #"formatter": "access",
            #"delay": True,
            "level" : logging_level,
            "class" : "logging.StreamHandler",
            "formatter" : "access"
        },
    }
}

log_config = {
            "version": 1,
            "formatters": std_format["formatters"],
            "loggers": std_logger["loggers"],
            "handlers": logging_handler["handlers"],
}
