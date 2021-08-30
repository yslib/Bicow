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

            self.axis_y = 200
            self.origin_z = 500

            self.top = 50
            self.bottom = 400
            self.left = 50
            self.right = 800

            self.scale = 5.0
            self.lense_length = 0.0
            self.lense_radius = 0.0
            self.world_matrix = np.array([[1.0,0.0,0.0], [0.0,1.0 ,0.0],[0.0,0.0,1.0]])
            self.screen_matrix = np.array([[1.0,0.0,0.0], [0.0,1.0 ,0.0],[0.0,0.0,1.0]])

            self.draw_lenses(np.array(dgauss50))

    def _setup_transform(self,scale: float, origin_z:float, axis_y:float):
        self.world_matrix = np.array([
            [scale,0.0,0.0],
            [0.0,scale,0.0],
            [0.0,0.0,1.0]
            ])

        self.screen_matrix = np.array([
            [-1, -0, origin_z],
            [0, -1, axis_y],
            [0,0,1]
        ])

        self.world_to_screen = self.screen_matrix @ self.world_matrix

    def _world_to_screen(self, point: List[float]):
        point.append(1.0)
        return (self.world_to_screen @ np.array(point))[0:2]

    def _draw_frame(self):
        pass

    def _update_canvas(self, length:float, max_radius:float):
        """
        Update size of this widget by the given lenses size
        """
        width = (length + 50) * self.scale
        height = ( 2 * max_radius + 50) * self.scale

        self.lense_length = length
        self.lense_radius = max_radius

        self.axis_y = height / 2.0
        self.origin_z = 0.618 * width
        self._setup_transform(self.scale, self.origin_z, self.axis_y)
        print(width, height)
        dpg.configure_item(self.widget(),width=int(width), height=int(height))

    def draw_lenses(self, lenses:np.ndarray):
        self.clear_drawinglist()
        length = 0.0
        max_radius = 0.0
        for i in range(len(lenses)):
            length += lenses[i][1]
            max_radius = max(max_radius, lenses[i][3] / 2.0)

        self._update_canvas(length, max_radius)

        z = length

        for i in range(len(lenses)):
            is_stop = lenses[i][0] == 0.0
            print('i-th z: ', z)
            r = lenses[i][3]/2.0
            if is_stop:
                print('aperture stop z: ', z)
                self._draw_aperture_stop(z, r, color=[255.0,255.0,0.0], thickness=4.0)
            else:
                self._draw_arch(z, lenses[i][0], 5.0)

            z -= lenses[i][1]

        self._draw_axis()
        self._draw_film()


    def _draw_axis(self):
        p0 = self._world_to_screen([self.lense_length+10,0])
        p1 = self._world_to_screen([-10,0])
        dpg.draw_line(p0, p1)

    def _draw_film(self, color=[255.0,255.0,255.0], thickness = 4.0):
        p0 = self._world_to_screen([0, self.film_height / 2])
        p1 = self._world_to_screen([0, -self.film_height/2])
        dpg.draw_line(p0, p1, color=color, thickness=thickness)

    def _draw_aperture_stop(self, z:float, aperture_radius:float, color=[255.0,255.0,255.0], thickness=2.0):
        p0 = self._world_to_screen([z, aperture_radius + 10])
        p1 = self._world_to_screen([z, aperture_radius])
        p2 = self._world_to_screen([z, -aperture_radius])
        p3 = self._world_to_screen([z, -aperture_radius - 10])
        dpg.draw_line(p0, p1, color=color, thickness=thickness)
        dpg.draw_line(p2, p3, color=color, thickness=thickness)

    def _draw_arch(self, z: float, curvature_radius:float, aperture_radius:float, color=[255.0,255.0,255.0], thickness=1.0):
        """
        There is no built-in arch drawing API in DearPyGui. So arch is done with
        segmented by polylines.
        """
        center = z - curvature_radius
        half = math.asin(aperture_radius/curvature_radius)
        min_theta = -2 * half
        max_theta = 2 * half
        seg_count = 30
        points = []
        for i in range(seg_count):
            t = i * 1.0 / seg_count
            theta = min_theta * (1.0 - t) + t * max_theta
            p0 = (center + curvature_radius * math.cos(theta))
            p1 = curvature_radius * math.sin(theta)
            points.append(self._world_to_screen([p0, p1]))
        dpg.draw_polyline(points=points,parent=self.widget(),color=color,thickness=thickness)

    def clear_drawinglist(self):
        dpg.delete_item(self.widget(), children_only=True)

class SceneCanvasWidget(Widget):
    def __init__(self, parent: int):
        super().__init__(parent)
        self._canvas = 0

class LenseDesignerWidget(Widget):
    def __init__(self, parent: int):
        super().__init__(parent)
        with dpg.child() as self._widget_id:
            self._lense_canvas: LenseCanvasWidget = LenseCanvasWidget(self.widget())