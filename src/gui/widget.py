import dearpygui.dearpygui as dpg
from typing import Callable, Any
from base.msg_queue import msg

class Widget:
    def __init__(self, parent):
        self._widget_id = None
        self._parent_id = parent

    def widget(self):
        return self._widget_id

    def parent(self):
        return self._parent_id
