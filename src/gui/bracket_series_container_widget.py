import dearpygui.dearpygui as dpg
from typing import List, Any
from .widget import Widget
from base.imgio import Image, ImageBracket
from gui.list_widget import ImageListWidget

class ImageContainerWidget(Widget):
    def __init__(self,parent):
        super(ImageContainerWidget, self).__init__(parent=parent)
        # self._widget_id = dpg.child(autosize_y=True, width=200)
        with dpg.child(autosize_x=True, height=250) as cid:
            self._image_list_widget:ImageListWidget = ImageListWidget(label='', parent=cid)
        with dpg.child(autosize_x=True) as cid:
            self._bracket_list_widget:ImageListWidget = ImageListWidget(label='', parent=cid)
        self._image_list:List[Image] = None
        self._bracket_list:List[ImageBracket] = None

    def set_data(self, image_brackets:List[ImageBracket])->None:
        self._bracket_list = image_brackets
        bracket_list_item = [b.name for b in image_brackets]
        image_list_item = [i.filename for b in image_brackets for i in b.images]
        self._image_list_widget.set_list_items(image_list_item)
        self._bracket_list_widget.set_list_items(bracket_list_item)

    def get_images(self)->List[Image]:
        return self._image_list

    def get_brackets(self)->List[ImageBracket]:
        return self._bracket_list
