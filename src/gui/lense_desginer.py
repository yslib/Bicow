import math
import dearpygui.dearpygui as dpg
from typing import List, Any
from base.imgio import Image, ImageBracket
from gui.list_widget import ImageListWidget
from gui.widget import Widget
import numpy as np

class LenseCanvasWidget(Widget):
    def __init__(self, parent: int):
        super().__init__(parent)
        with dpg.drawlist(label='lenses', width=800, height=400) as self._widget_id:
            dgauss50 = [
                [29.475,3.76,1.67,25.2],
                [84.83,0.12,1,25.2],
                [19.275,4.025,1.67,23],
                [40.77,3.275,1.699,23],
                [12.75,5.705,1,18],
                [0,4.5,0,17.1],
                [-14.495,1.18,1.603,17],
                [40.77,6.065,1.658,20],
                [-20.385,0.19,1,20],
                [437.065,3.22,1.717,20],
                [-39.73,0,1,20]
            ]

            self.film_height = 24
            self.scale = 5

            self.axis_y = 200
            self.origin_z = 500

            self.top = 50
            self.bottom = 400
            self.left = 50
            self.right = 800

            self.max_lenses_aperture_radius = 50
            self.draw_lenses(np.array(dgauss50))

    def _update_layout(self, length:float, max_radius:float):
        """
        Update size of this widget by the given lenses size
        """
        dpg.configure_item(self.widget(), width= (length+100) * self.scale, height=(2 * max_radius + 50) * self.scale)
        self.axis_y = max_radius + self.top
        self.origin_z = length + 50
        self.max_lenses_aperture_radius = min(max_radius, 100)

    def draw_lenses(self, lenses:np.ndarray):
        self.clear_drawinglist()
        length = 0.0
        max_radius = 0.0
        for i in range(len(lenses)):
            length += lenses[i][1]
            max_radius = max(max_radius, lenses[i][3] / 2.0)

        self._update_layout(length, max_radius)

        z = length

        for i in range(len(lenses)):
            is_stop = lenses[i][0] == 0.0
            print('i-th z: ', z)
            r = lenses[i][3]/2.0
            if is_stop:
                print('aperture stop z: ', z)
                self._draw_aperture_stop(z, r, color=[255.0,255.0,0.0], thickness=4.0)
            else:
                self._draw_arch(z, lenses[i][0], r)
                pass

            z -= lenses[i][1]

        self._draw_axis()
        self._draw_film()


    def _draw_axis(self):
        margin_from_left = 50
        dpg.draw_line([margin_from_left * self.scale, self.axis_y * self.scale],[self.origin_z * self.scale, self.axis_y * self.scale])

    def _draw_film(self, color=[255.0,255.0,255.0], thickness = 4.0):
        dpg.draw_line([self.origin_z * self.scale, (self.axis_y + self.film_height) * self.scale],[self.origin_z * self.scale, self.bottom * self.scale], color=color, thickness=thickness)
        pass

    def _draw_aperture_stop(self, z:float, aperture_radius:float, color=[255.0,255.0,255.0], thickness=2.0):
        half_range = min(80, aperture_radius) + 20
        up_y1 = (self.axis_y - aperture_radius) * self.scale
        up_y0 = (self.axis_y - aperture_radius - (half_range - aperture_radius)) * self.scale
        down_y0 = (self.axis_y + aperture_radius) * self.scale
        down_y1 = (self.axis_y + aperture_radius + (half_range - aperture_radius)) * self.scale
        dpg.draw_line([z * self.scale, up_y0], [z * self.scale, up_y1],color=color,thickness=thickness)
        dpg.draw_line([z * self.scale, down_y0], [z * self.scale, down_y1],color=color,thickness=thickness)

    def _draw_arch(self, z: float, radius:float, aperture_radius:float, color=[255.0,255.0,255.0]):
        """
        There is no built-in arch drawing API in DearPyGui. So arch is done with
        segmented by polylines.
        """
        center = z - radius
        half = math.asin(aperture_radius/radius)
        min_theta = -2 * half
        max_theta = 2 * half
        seg_count = 30
        points = []
        for i in range(seg_count):
            t = i * 1.0 / seg_count
            theta = min_theta * (1.0 - t) + t * max_theta
            z = (center + radius * math.cos(theta))
            y = radius * math.sin(theta)
            points.append([(self.origin_z - z) * self.scale, (y + self.axis_y) * self.scale])
        dpg.draw_polyline(points=points,parent=self.widget(),color=color)

    def clear_drawinglist(self):
        dpg.delete_item(self.widget(), children_only=True)

class SceneCanvasWidget(Widget):
    def __init__(self, parent: int):
        super().__init__(parent)
        self._canvas = 0

class LenseDesginerWidget(Widget):
    def __init__(self, parent: int):
        super().__init__(parent)
        with dpg.child() as self._widget_id:
            self._lense_canvas: LenseCanvasWidget = LenseCanvasWidget(self.widget())