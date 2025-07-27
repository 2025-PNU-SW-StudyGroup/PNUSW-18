import logging


class _logger:
    _logger = None

    def __init__(self, name=None, level=logging.DEBUG):
        self.level = level
        self.name = name

    def __call__(self, msg: str, level=None):
        if _logger._logger is None:
            _logger._logger = logging.getLogger(self.name)
            _logger._logger.setLevel(self.level)
            _logger._logger.propagate = False

            handler = logging.StreamHandler()
            formatter = logging.Formatter(f"[{self.name}] %(message)s")
            handler.setFormatter(formatter)
            _logger._logger.addHandler(handler)

        level = self.level if not level else level
        _logger._logger.log(msg=msg, level=level)
        return self
