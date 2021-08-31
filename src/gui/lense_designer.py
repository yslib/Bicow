import math
import dearpygui.dearpygui as dpg
from typing import List, Any, Callable, Dict
from gui.widget import Widget
from demo.realistic import RealisticCamera
import numpy as np
class LenseCanvasWidget(Widget):
    def __init__(self, *, parent: int, film_height=24.0):
        super().__init__(parent)
        with dpg.drawlist(label='lenses',parent=parent, width=800, height=400) as self._widget_id:
            self.film_height = film_height
            self.axis_y = 200
            self.origin_z = 500

            self.scale = 5.0
            self.lense_length = 0.0
            self.lense_radius = 0.0
            self.world_matrix = np.array([[1.0,0.0,0.0], [0.0,1.0 ,0.0],[0.0,0.0,1.0]])
            self.screen_matrix = np.array([[1.0,0.0,0.0], [0.0,1.0 ,0.0],[0.0,0.0,1.0]])


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
        return (self.world_to_screen @ np.array([point[0], point[1], 1.0]))[0:2]

    def _draw_frame(self):
        pass

    def _update_canvas(self, length:float, max_radius:float):
        """
        Update size of this widget by the given lenses size
        """
        width = (600 + length * self.scale)
        height = ( 2 * max_radius ) * self.scale + 100

        self.lense_length = length
        self.lense_radius = max_radius

        self.axis_y = height / 2.0
        self.origin_z = 0.618 * width
        self._setup_transform(self.scale, self.origin_z, self.axis_y)
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
        # draw lense groups
        for i in range(len(lenses)):
            is_stop = lenses[i][0] == 0.0
            r = lenses[i][3]/2.0
            if is_stop:
                self._draw_aperture_stop(z, r, color=[255.0, 255.0, 0.0], thickness=4.0)
            else:
                a, b = self._draw_arch(z, lenses[i][0], 6.0)
                if i > 0 and lenses[i - 1][2] != 1 and lenses[i-1][2] != 0:
                    self._draw_line(a, first)
                    self._draw_line(b, last)  # draw connection between element surface
                first, last = a, b

            z -= lenses[i][1]

        self._draw_axis()
        self._draw_film()

    def draw_rays(self, rays:np.array, count:int, color=[255.0,255.0,255.0,255.0], thickness=1.0):
        points = []
        point1 = []
        for i in range(count):
            p = rays[0][i]
            p0 = self._world_to_screen([-p[2],p[0]])
            p1 = self._world_to_screen([-p[2],-p[0]])
            points.append(p0)
            point1.append(p1)

        dpg.draw_polyline(points, parent=self.widget(), color=color, thickness=thickness)
        dpg.draw_polyline(point1, parent=self.widget(), color=color, thickness=thickness)

    def _draw_line(self, p0:List[float], p1:List[float], color=[255.0,255.0,255.0], thickness=1.0):
        dpg.draw_line(self._world_to_screen(p0), self._world_to_screen(p1), color=color, thickness=thickness,parent=self.widget())

    def _draw_axis(self):
        p0 = self._world_to_screen([self.lense_length + 10,0])
        p1 = self._world_to_screen([-10,0])
        dpg.draw_line(p0, p1, parent=self.widget())

    def _draw_film(self, color=[255.0,255.0,255.0], thickness = 4.0):
        p0 = self._world_to_screen([0, self.film_height / 2])
        p1 = self._world_to_screen([0, -self.film_height/2])
        dpg.draw_line(p0, p1, color=color, thickness=thickness, parent=self.widget())

    def _draw_aperture_stop(self, z:float, aperture_radius:float, color=[255.0,255.0,255.0], thickness=2.0):
        p0 = self._world_to_screen([z, aperture_radius + 10])
        p1 = self._world_to_screen([z, aperture_radius])
        p2 = self._world_to_screen([z, -aperture_radius])
        p3 = self._world_to_screen([z, -aperture_radius - 10])
        dpg.draw_line(p0, p1, color=color, thickness=thickness, parent=self.widget())
        dpg.draw_line(p2, p3, color=color, thickness=thickness, parent=self.widget())

    def _draw_arch(self, z: float, curvature_radius:float, aperture_radius:float, color=[255.0,255.0,255.0], thickness=1.0):
        """
        There is no built-in arch drawing API in DearPyGui. So arch is done with
        segmented by polylines.

        Returns the two end points of the arch
        """
        center = z - curvature_radius
        half = math.asin(aperture_radius/curvature_radius)
        min_theta = -2 * half
        max_theta = 2 * half
        seg_count = 30
        points = []
        first = []
        last = []
        for i in range(seg_count):
            t = i * 1.0 / seg_count
            theta = min_theta * (1.0 - t) + t * max_theta
            p0 = (center + curvature_radius * math.cos(theta))
            p1 = curvature_radius * math.sin(theta)
            if i == 0:
                first = [p0, p1]
            elif i == seg_count - 1:
                last = [p0, p1]
            points.append(self._world_to_screen([p0, p1]))
        dpg.draw_polyline(points=points,parent=self.widget(),color=color,thickness=thickness)
        return first, last

    def clear_drawinglist(self):
        dpg.delete_item(self.widget(), children_only=True)


class SceneCanvasWidget(Widget):
    def __init__(self, parent: int):
        super().__init__(parent)
        self._canvas = 0


class NodeWidget(Widget):
    def __init__(self,*, name:str, parent:int):
        super(NodeWidget, self).__init__(parent)
        self._attri_list = []
        with dpg.node(label=name,parent=parent) as self._widget_id:
            pass

    def _register_attri(self, attri_name:str):
        pass

    def get_attri_value(self, attri_name:str):
        pass

class SceneNode(NodeWidget):
    def __init__(self,parent:int):
        super(SceneNode, self).__init__(name='Scene',parent=parent)
        with dpg.node_attribute(label='Scene', attribute_type=dpg.mvNode_Attr_Output, parent=self.widget()) as self._attri:
            pass


class FilmNode(NodeWidget):
    def __init__(self, parent:int):
        super(FilmNode, self).__init__(name='Film',parent=parent)
        with dpg.node_attribute(label='Film', attribute_type=dpg.mvNode_Attr_Input, parent=self.widget()) as self._attri:
            dpg.add_input_floatx(label='Film size',width=200, size=2, default_value=(36.00,24.00))


class LenseGroup(NodeWidget):
    def __init__(self,*,name:str,parent:int):
        super(LenseGroup, self).__init__(name=name, parent=parent)

class SphereLenseGroup(LenseGroup):
    def __init__(self,*,name:str, parent:int):
        super(SphereLenseGroup, self).__init__(name=name, parent=parent)


class LenseEditorWidget(Widget):
    def __init__(self,*,update_callback:Callable[[Any],None], parent: int):
        super().__init__(parent)
        self._node_list = []
        self._update_callback = update_callback
        with dpg.node_editor(parent=parent,callback=self._add_node_link, delink_callback=self._delete_link) as self._widget_id:
            pass

        self._add_default_node()

    def _add_node_link(self, sender:int, app_data:Any, user_data:Any):
        print('add_node_link: ', sender, app_data, user_data)
        link = dpg.add_node_link(app_data[0], app_data[1], parent=sender)
        callable(self._update_callback) and self._update_callback()

    def _delete_link(self, sender:int, app_data:Any, user_data:Any):
        print('delete_link:', sender, app_data, user_data)
        dpg.delete_item(app_data)
        callable(self._update_callback) and self._update_callback()

    def _add_default_node(self):
        self._add_node(SceneNode(self.widget()))
        self._add_node(FilmNode(self.widget()))

    def _add_node(self, node_widget:NodeWidget):
        self._node_list.append(node_widget)
        callable(self._update_callback) and self._update_callback()

    def open(self, filename:str):
        raise NotImplementedError

    def save(self, filename:str):
        """
        """
        raise NotImplementedError

    def get_lense_data_dict(self):
        return

    def clear_lenses(self):
        self._add_default_node()
        callable(self._update_callback) and self._update_callback()

class LenseDesignerWidget(Widget):
    def __init__(self, parent: int):
        super().__init__(parent)
        with dpg.child(parent=parent) as self._widget_id:
            self._lense_canvas: LenseCanvasWidget = LenseCanvasWidget(parent=self.widget())
            self._node_editor: LenseEditorWidget = LenseEditorWidget(update_callback=self._editor_update, parent=self.widget())

            pos = [0.0, 3.0, 24.0]
            center = [0.0, 0.0, 0.0]
            world_up = [0.0, 1.0, 0.0]
            self.camera = RealisticCamera(pos, center, world_up)

        self._lense_update()

    def _editor_update(self, *args, **kwargs):
        """
        Update Realistic camera here
        """
        print('_editor_update')

    def _convert_raw_lense_data(self, lense_data_dict:Dict[str,List[float]]):
        """
        """
        return [[]]

    def _lense_update(self):
        self.camera.refocus(0.2)
        lenses = self.camera.get_lenses_data()
        self.camera.gen_draw_rays_from_film()
        ray_points = self.camera.get_ray_points()

        self._lense_canvas.draw_lenses(np.array(lenses))
        self._lense_canvas.draw_rays(ray_points, self.camera.get_element_count() + 2, color=[0, 0, 255])
