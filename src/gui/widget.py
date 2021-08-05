from math import log
import dearpygui.dearpygui as dpg
from dearpygui.logger import mvLogger
from typing import Callable, Any

from numpy.lib.function_base import select
from base.msg_queue import msg

_logger = None

def init_global_logger(parent:int):
    global _logger
    if _logger is None:
        _logger = mvLogger(parent)

def get_logger()->mvLogger:
    return _logger

class Widget:
    def __init__(self, parent:int):
        self._widget_id:int = None
        self._parent_id:int = parent

    def widget(self)->int:
        return self._widget_id

    def parent(self)->int:
        return self._parent_id