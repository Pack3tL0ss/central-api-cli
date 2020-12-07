#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Any
from .utils import Utils
utils = Utils()

# from .central import CentralApi  # NoQA
# from .central import BuildCLI  # NoQA

# import logging  # NoQA

# LOGFILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logs", 'centralcli.log'))
# DEBUG = os.getenv('DEBUG', False)


class Response:
    '''Decorator class for requests.response object

    Assigns commonly evaluated attributes regardless of success
    Otherwise resp.ok will always be assigned and will be True or False
    '''
    # def __init__(self, function) -> Any:
    #     self.function = function

    def __init__(self, function, *args: Any, **kwargs: Any) -> Any:
        try:
            resp = function(*args, **kwargs)
            self.ok = resp.ok
            try:
                self.output = resp.json()
            except Exception:
                self.output = resp.text
            self.error = resp.reason
            self.status_code = resp.status_code
            # self.json = resp.json
            # self.response = resp
        except Exception as e:
            self.ok = False
            self.output = {}
            self.error = f"Exception occured {e.__class__}\n\t{e}"
            self.status_code = 418
            # self.json = None
            # self.response = None

# class Response():
#     def __init__(self, ok: bool, output=None, error=None, status_code=None, state=None, do_json=False,  **kwargs):
#         self.ok = ok
#         self.text = output
#         self.error = error
#         self.state = state
#         self.status_code = status_code
#         if 'json' in kwargs:
#             self.json = kwargs['json']
#         else:
#             self.json = None


# class MyLogger:
#     def __init__(self, log_file, debug=False):
#         self.log_msgs = []
#         self.DEBUG = debug
#         self.verbose = False
#         self.log_file = log_file
#         self._log = self.get_logger()
#         self.name = self._log.name

#     def get_logger(self):
#         '''Return custom log object.'''
#         fmtStr = "%(asctime)s [%(process)d][%(levelname)s]: %(message)s"
#         dateStr = "%m/%d/%Y %I:%M:%S %p"
#         logging.basicConfig(filename=self.log_file,
#                             level=logging.DEBUG if self.DEBUG else logging.INFO,
#                             format=fmtStr,
#                             datefmt=dateStr)
#         return logging.getLogger(__name__)

#     def log_print(self, msgs, log=False, show=True, level='info', *args, **kwargs):
#         msgs = [msgs] if not isinstance(msgs, list) else msgs
#         _msgs = []
#         _logged = []
#         for i in msgs:
#             if log and i not in _logged:
#                 getattr(self._log, level)(i)
#                 _logged.append(i)
#             if '\n' in i:
#                 _msgs += i.replace('\t', '').replace('\r', '').split('\n')
#             elif i.startswith('[') and ']' in i:
#                 _msgs.append(i.split(']', 1)[1].replace('\t', '').replace('\r', ''))
#             else:
#                 _msgs.append(i.replace('\t', '').replace('\r', '').strip())

#         msgs = []
#         [msgs.append(i) for i in _msgs
#             if i and i not in msgs and i not in self.log_msgs]

#         if show:
#             self.log_msgs += msgs
#             for m in self.log_msgs:
#                 print(m)
#             self.log_msgs = []

#     def show(self, msgs, log=False, show=True, *args, **kwargs):
#         self.log_print(msgs, show=show, log=log, *args, **kwargs)

#     def debug(self, msgs, log=True, show=False, *args, **kwargs):
#         self.log_print(msgs, log=log, show=show, level='debug', *args, **kwargs)

#     # -- more verbose debugging - primarily to get json dumps
#     def debugv(self, msgs, log=True, show=False, *args, **kwargs):
#         if self.DEBUG and self.verbose:
#             self.log_print(msgs, log=log, show=show, level='debug', *args, **kwargs)

#     def info(self, msgs, log=True, show=False, *args, **kwargs):
#         self.log_print(msgs, log=log, show=show, *args, **kwargs)

#     def warning(self, msgs, log=True, show=False, *args, **kwargs):
#         self.log_print(msgs, log=log, show=show, level='warning', *args, **kwargs)

#     def error(self, msgs, log=True, show=False, *args, **kwargs):
#         self.log_print(msgs, log=log, show=show, level='error', *args, **kwargs)

#     def exception(self, msgs, log=True, show=False, *args, **kwargs):
#         self.log_print(msgs, log=log, show=show, level='exception', *args, **kwargs)

#     def critical(self, msgs, log=True, show=False, *args, **kwargs):
#         self.log_print(msgs, log=log, show=show, level='critical', *args, **kwargs)

#     def fatal(self, msgs, log=True, show=False, *args, **kwargs):
#         self.log_print(msgs, log=log, show=show, level='fatal', *args, **kwargs)

#     def setLevel(self, level):
#         getattr(self._log, 'setLevel')(level)


# log = MyLogger(LOGFILE, debug=DEBUG)
