import dearpygui.dearpygui as dpg
from typing import Callable, List, Any
from .widget import Widget, get_logger

class ImageListWidget(Widget):
    def __init__(self,label:str, parent: int):
        super().__init__(parent=parent)
        self._widget_id = dpg.add_listbox(label=label,
        items=[],
        num_items=10,
        callback=self._callback)

        self._items = []
        self._update_list_layout()

    def _update_list_layout(self)->None:
        """
        Updates the list size and layout after the content changed
        """

        num_items = min(len(self._items), 20)
        rect = dpg.get_item_rect_size(self.parent())
        dpg.configure_item(self.widget(), num_items=num_items, width=rect[0])

    def _callback(self, sender, app_data, user_data)->None:
        print('ImageListWidget::_callback', sender, app_data, user_data)

    def set_list_items(self, items: List[Any], display_func:Callable[[Any],str]=None)->None:
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

    def get_items(self)->List[Any]:
        return self._items
