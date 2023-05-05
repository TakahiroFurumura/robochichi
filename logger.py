import os
import sys
import logging


def get_logger(name: str,
               logfile_path: str = None,
               log_level: str = 'DEBUG'):
    """

    :param name:
    :param logfile_path:
    :param log_level:
    :return:
    """
    assert isinstance(name, str)
    assert logfile_path is None or isinstance(logfile_path, str)

    # Log config
    logfile_path = logfile_path or os.path.dirname(__file__) + '/%s.log' % name

    # creat dir if not exists
    if not os.path.exists(os.path.dirname(logfile_path)):
        os.mkdir(logfile_path)

    # Initialize a logger instance
    lgr = logging.getLogger(name)

    commandline_args_dict = {arg.split('=')[0].lower(): arg.split('=')[1].upper()
                             for arg in sys.argv if len(arg.split('=')) == 2}
    _log_level = commandline_args_dict.get('log_level') or log_level
    log_format_text = '%(asctime)s [%(levelname)s]: %(message)s (%(filename)s)'

    # Console Handler
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(_log_level)
    # create and add formatter
    formatter = logging.Formatter(log_format_text)
    ch.setFormatter(formatter)
    # add ch to logger
    lgr.addHandler(ch)

    # File Handler
    fh = logging.FileHandler(logfile_path)
    fh.setLevel(_log_level)
    fh_formatter = logging.Formatter(log_format_text)
    fh.setFormatter(fh_formatter)
    lgr.addHandler(fh)

    lgr.setLevel(_log_level)
    lgr.info('logger starts: ' + name)
    lgr.info('log level: ' + log_level)

    return lgr

