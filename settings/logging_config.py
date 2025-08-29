import logging.config

def setup_logging():
    log_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
        },
        'handlers': {
            'file_handler': {
                'class': 'logging.FileHandler',
                'level': 'INFO',
                'formatter': 'standard',
                'filename': 'logs/eds_app.log',
            },
            'console_handler': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'standard',
            },
        },
        'loggers': {
            '': {  
                'handlers': ['file_handler', 'console_handler'],
                'level': 'INFO',
                'propagate': True,
            },
        }
    }
    logging.config.dictConfig(log_config)