# -*- coding: utf-8 -*-

import logging
import sys


class StdoutFilter(logging.Filter):
    """
    Filter levels which should not be logged on stdout.
    """

    def __init__(self, level, name=''):
        """
        :param level: lowest filtered level.
        :param name: the name of the filter.
        """
        super(StdoutFilter, self).__init__(name)
        self.__level = level

    def filter(self, record):
        return {True: 1, False: 0}[(record.levelno < self.__level)]


class Logger(logging.Logger):

    def __init__(self, name, level=logging.INFO):
        """
        :param name: Name of the logger
        :param level: Log level of the logger
        """
        super(Logger, self).__init__(name, level)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        err_handler = logging.StreamHandler(sys.stderr)
        err_handler.setLevel(logging.ERROR)
        err_handler.setFormatter(formatter)
        self.addHandler(err_handler)

        def_handler = logging.StreamHandler(sys.stdout)
        def_handler.setLevel(logging.DEBUG)
        def_handler.addFilter(StdoutFilter(logging.ERROR))
        def_handler.setFormatter(formatter)
        self.addHandler(def_handler)


# the global logger
logger = Logger('orobnat')
