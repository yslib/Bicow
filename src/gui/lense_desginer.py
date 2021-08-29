import dearpygui.dearpygui as dpg
from typing import List, Any
from base.imgio import Image, ImageBracket
from gui.list_widget import ImageListWidget
from gui.widget import Widget
import numpy as np

class LenseCanvasWidget(Widget):
    def __init__(self, parent: int):
        super().__init__(parent)
        with dpg.drawlist(label='lenses', width=400,height=400) as self._widget_id:
            draw_x = 4
            draw_y = 4
            draw_size = 36
            draw_spacing = 10
            _draw_t = 1.0
            draw_color = [255, 255, 0]
            a = dpg.draw_circle([draw_x + draw_size*0.5, draw_y + draw_size*0.5], draw_size*0.5, thickness=_draw_t, color=draw_color)
            print(a)

    def draw_lenses(self, lenses:np.ndarray):
        draw_x = 4
        draw_y = 4
        draw_size = 36
        draw_spacing = 10
        _draw_t = 1.0
        draw_color = [255, 255, 0]
        dpg.draw_rectangle([draw_x, draw_y], [draw_size + draw_x, draw_size + draw_y], thickness=_draw_t, color=draw_color, parent=self.widget())
        draw_x = draw_x + draw_spacing + draw_size

    def clear_drawinglist(self):
        dpg.delete_item(self.widget(), children_only=True)
        self.draw_lenses(np.array([]))
        pass

class SceneCanvasWidget(Widget):
    def __init__(self, parent: int):
        super().__init__(parent)
        self._canvas = 0

class LenseDesginerWidget(Widget):
    def __init__(self, parent: int):
        super().__init__(parent)
        with dpg.child() as self._widget_id:
            self._lense_canvas: LenseCanvasWidget = LenseCanvasWidget(self.widget())
            self._clear_button = dpg.add_button(label='Clear Items', callback=lambda a,s,u:self._lense_canvas.clear_drawinglist())