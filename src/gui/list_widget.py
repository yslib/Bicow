import dearpygui.dearpygui as dpg
from widget import Widget
from typing import Callable, List, Any

class ImageListWidget(Widget):
    def __init__(self,label:str, parent: int):
        super().__init__(parent)
        self._widget_id = dpg.add_listbox(label=label,
        items=[],
        num_items=10,
        width=0,
        callback=self._callback)
        self._items = []
        self._update_list_layout()

    def _update_list_layout(self):
        num_items = len(self._items) / 20
        dpg.configure_item(self.widget(), num_items=num_items)

    def _callback(self, sender, app_data, user_data):
        print(sender, app_data, user_data)
        pass

    def set_list_items(self, items: List[Any], display_func:Callable[[Any],str]):
        """
        Set display items
        """
        self._items = items
        if callable(display_func):
            strs = [display_func(it) for it in self._items]
        else:
            strs = [str(i) for i in range(len(self._items))]

        dpg.configure_item(item=self.widget(), items=strs)
        self._update_list_layout()