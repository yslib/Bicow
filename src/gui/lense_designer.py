import math
import dearpygui.dearpygui as dpg
from typing import List, Any, Callable, Dict

from networkx.classes.function import selfloop_edges

from gui.widget import Widget, widget_property, AttributeValueType
from demo.realistic import RealisticCamera
import numpy as np
import networkx as nx
class LenseCanvasWidget(Widget):
    def __init__(self, *, parent: int, film_height=24.0, callback:Callable[[None],None]=None):
        super().__init__(parent=parent, callback=callback)
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


class LenseSurface(Widget):
    def __init__(self, parent: int, callback:Callable[[None],None]=None):
        super().__init__(parent=parent,callback=callback)

class LenseSphereSurface(LenseSurface):
    curvature_radius = widget_property('Curvature Radius', AttributeValueType.ATTRI_FLOAT,0.0,100.0,100)
    thickness = widget_property('Thickness', AttributeValueType.ATTRI_FLOAT,0.0,100.0,100)
    eta = widget_property('Eta', AttributeValueType.ATTRI_FLOAT,0.0,100.0,100)
    aperture_radius = widget_property('Aperture Radius', AttributeValueType.ATTRI_FLOAT,0.0,100.0,100)
    def __init__(self, parent: int, callback:Callable[[None],None]):
        super().__init__(parent=parent,callback=callback)
        with dpg.tree_node(label='SphereElement',parent=parent) as self._widget_id:
            self.curvature_radius = 0.0
            self.thickness = 0.0
            self.eta = 0.0
            self.aperture_radius = 0.0

    def dump(self):
        return [ self.curvature_radius,self.thickness,self.eta,self.aperture_radius]

    def property_changed(self, s, a, u):
        self._invoke_update()

    def load(self, data:List[float]= [0.0,0.0,0.0,0.0]):
        self.curvature_radius = data[0]
        self.thickness = data[1]
        self.eta = data[2]
        self.aperture_radius = data[3]

class NodeWidget(Widget):
    def __init__(self,*, name:str, parent:int, callback:Callable[[Any],Any]=None):
        super(NodeWidget, self).__init__(parent=parent, callback=callback)
        self._attri_dict:Dict[str,Any] = {}
        self._callback = callback
        with dpg.node(label=name,parent=parent, user_data=self) as self._widget_id:
            pass

    def add_attribute(self, attri_name:str, attri_type:int):
        if attri_name not in self._attri_dict.keys():
            with dpg.node_attribute(label=attri_name, attribute_type=attri_type, parent=self.widget()) as attri:
                self._attri_dict[attri_name] = (attri, {})
                return attri
        return None

    def get_attribute(self, attri_name:str):
        return self._attri_dict.get(attri_name, (None, {}))[0]

    def remove_attribute(self, attri_name):
        if attri_name in self._attri_dict.keys():
            dpg.delete_item(self._attri_dict[attri_name][0])

    def add_value(self,*,attri_name:str,
                        value_name:str,
                        value_type:int,
                        default_value:Any,
                        size:int=4,
                        callback:Callable[[Any], Any]=None):

        attri_id = self.get_attribute(attri_name)
        attri_id, value_dict = self._attri_dict.get(attri_name, (None, {}))
        if attri_id is None:
            print('No corresponding attribute :', attri_name)
            return

        width = 100

        if value_name in value_dict.keys():
            print(value_name, 'has already existed in attribute ', attri_name)
            return None
        else:
            if value_type == AttributeValueType.ATTRI_FLOAT:
                value_id = dpg.add_input_float(label=value_name, callback=callback,default_value=default_value,parent=attri_id,width=width)
            elif value_type == AttributeValueType.ATTRI_FLOATX:
                value_id = dpg.add_input_floatx(label=value_name, callback=callback,default_value=default_value,size=size, parent=attri_id,width=width)
            elif value_type == AttributeValueType.ATTRI_INT:
                value_id = dpg.add_input_int(label=value_name,callback=callback,default_value=default_value, parent=attri_id,width=width)
            value_dict[value_name] = value_id

        return value_id


    def get_attri_value_item_id(self,attri_name:str, value_name:str):
        return self._attri_dict.get(attri_name, (-1, {}))[1].get(value_name, None)

    def get_value(self, attri_name:str, value_name:str):
        item_id = self.get_attri_value_item_id(attri_name=attri_name,value_name=value_name)
        if item_id is not None:
            return dpg.get_value(item_id)

        print('No such value: ', value_name, ' of ', attri_name)
        return None

    def set_value(self, attri_name:str, value_name:str, value:Any):
        item_id = self.get_attri_value_item_id(attri_name=attri_name,value_name=value_name)
        if item_id is not None:
            dpg.configure_item(item=item_id, value=Any)
            return
        print('No such value: ', value_name, ' of ', attri_name)


class SceneNode(NodeWidget):
    def __init__(self,parent:int, value_update_callback:Callable[[Any], None]=None):
        super(SceneNode, self).__init__(name='Scene',parent=parent,callback=value_update_callback)
        self.add_attribute(attri_name='SceneOutput',attri_type=dpg.mvNode_Attr_Output)
        self.add_value(value_name='Focus depth',attri_name='SceneOutput', value_type=AttributeValueType.ATTRI_FLOAT,default_value=10.0,callback=value_update_callback)

class FilmNode(NodeWidget):
    def __init__(self, parent:int,value_update_callback:Callable[[Any], None]=None):
        super(FilmNode, self).__init__(name='Film',parent=parent,callback=value_update_callback)
        self.add_attribute(attri_name='FilmInput',attri_type=dpg.mvNode_Attr_Input)
        self.add_value(attri_name='FilmInput',
        value_name='Film Size',
        value_type=AttributeValueType.ATTRI_FLOATX,
        default_value=(36,24),
        size=2,
        callback=value_update_callback)

class ApertureStop(NodeWidget):
    def __init__(self, *, parent: int,value_update_callback:Callable[[Any], None]=None):
        super().__init__(name='Aperture Stop', parent=parent, callback=value_update_callback)
        self.add_attribute('Input',dpg.mvNode_Attr_Input)
        self.add_attribute('Output',dpg.mvNode_Attr_Output)
        self.add_value(attri_name='Input',
        value_name='Stop Radius',
        value_type=AttributeValueType.ATTRI_FLOAT,
        default_value=10.00,
        callback=value_update_callback)


class LenseSurfaceGroup(NodeWidget):
    def __init__(self,*,name:str,parent:int, update_callback:Callable[[Any], Any]=None):
        super(LenseSurfaceGroup, self).__init__(name=name, parent=parent,callback=update_callback)
        self._lense_surface_group:List[LenseSurface] = []
        self._surface_data_value_id:List[int] = []
        self._input_attri_name = 'Input'
        self._output_attri_name = 'Output'
        self._surface_count_value_name = 'Surface Count'
        self.input_attri_item_id = self.add_attribute(self._input_attri_name, attri_type=dpg.mvNode_Attr_Input)
        self.add_attribute(self._output_attri_name, attri_type=dpg.mvNode_Attr_Output)

        self.count_attri = self.add_value(attri_name=self._input_attri_name,
        value_name=self._surface_count_value_name,
        value_type=AttributeValueType.ATTRI_INT,
        default_value=0,
        callback=lambda s,a,u:self._update_surface(int(a)))


    def _update_surface(self, count):
        """
        """
        cur_count = len(self._lense_surface_group)
        print('surface count changed: ',count, cur_count)

        delta = count - cur_count
        if delta > 0:
            for _ in range(delta):
                surf = LenseSphereSurface(self.input_attri_item_id, callback=self.callback())
                self._lense_surface_group.append(surf)
        elif delta < 0:
            for item in self._lense_surface_group[count:]:
                item.delete()
            del self._lense_surface_group[count:]

        self._invoke_update()

    def load(self, raw_group_data: List[List[float]]):
        self._clear_surface_data()
        surfs = []
        for s in raw_group_data:
            surf = LenseSphereSurface(self.input_attri_item_id, callback=self.callback())
            surf.load(s)
            surfs.append(surf)

        self._lense_surface_group = surfs
        dpg.set_value(self.count_attri, len(self._lense_surface_group))
        self._invoke_update()

    def get_surface(self, ind:int):
        return self._lense_surface_group[ind]

    def get_surface_count(self):
        return len(self._lense_surface_group)

    def _clear_surface_data(self):
        for surf in self._lense_surface_group:
            surf.delete()
        self._lense_surface_group = []

    def clear_surface_data(self):
        """
        Invode update signal
        """
        self._clear_surface_data()
        self._invoke_update()



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
    [-39.73,5.0,1,20]
]



class EditorEventType:
    EVENT_NODE_ADD= 0x000
    EVENT_NODE_DELETE = 0x001
    EVENT_NODE_UPDATE = 0x002
    EVENT_NODE_DELETE_ALL = 0x003

    EVENT_LINK_ADD = 0x200
    EVENT_LINK_DELETE = 0x201


    EVENT_SURFACE_ADD = 0x300
    EVENT_SURFACE_DELETE = 0x301
    EVENT_SURFACE_ATTRIBUTE_CHANGED = 0x302

    EVENT_UPDATE_ALL = 0xFFF


class Graph:
    def __init__(self):
        self.G = nx.Graph()

    def add_edge(self, n1, n2):
        self.G.add_edge(n1, n2)

    def remove_edge(self, n1, n2):
        self.G.remove_edge(n1, n2)

    def simple_path_of(self, n1, n2):
        return list(nx.all_simple_paths(self.G, n1, n2))

    def edge_exists(self, n1, n2):
        return self.G.has_edge(n1, n2)


class LenseEditorWidget(Widget):
    def __init__(self,*,update_callback:Callable[[Any],None], parent: int):
        super().__init__(parent=parent, callback=update_callback)
        self._lense_group_node_list:List[LenseSurfaceGroup] = []
        self._link_list = []

        self._lense_data:List[Dict[str, List[float]]]= []
        self._valid_lenses = False
        self._editor_id = -1
        with dpg.node_editor(parent=parent,callback=self._add_node_link, delink_callback=self._delete_link) as self._widget_id:
            pass

        dpg.add_button(label='Add Lense', callback=self._add_new_node)

        self._editor_id = self.widget()

        self._add_default_node()
        self._add_lense_group_node(LenseSurfaceGroup(name='Lense1',parent=self._editor_id, update_callback=self.callback()))
        self._add_lense_group_node(LenseSurfaceGroup(name='Gauss Lense1',parent=self._editor_id, update_callback=self.callback()))
        self._add_lense_group_node(LenseSurfaceGroup(name='Gauss Lense2',parent=self._editor_id, update_callback=self.callback()))
        self._add_lense_group_node(LenseSurfaceGroup(name='Lense2',parent=self._editor_id, update_callback=self.callback()))

        self.node_manager = Graph()


    def set_lense_data(self, lense_data_dict:List[Dict[str, List[float]]]):
        """
        Sets lense data

        Note: this function will invoke update_callback
        """
        self._clear_lense()
        self._lense_data = lense_data_dict.copy()

        self._invoke_update(event=EditorEventType.EVENT_NODE_UPDATE)


    def get_lense_data(self):
        """
        Returned data makes sense only
        when is_valid_lenses() returns True
        """
        return self._lense_data.copy()

    def is_valid_lenses(self):
        """
        Returns True if the lenses is valid otherwise returns False
        (e.g. links between lense groups are not closed)
        """
        return self._valid_lenses

    def clear_lenses(self):
        """
        Note: this function will invoke update_callback
        """
        self._clear_lense()
        self._invoke_update(event=EditorEventType.EVENT_NODE_UPDATE)

    def _add_node_link(self, sender:int, app_data:Any, user_data:Any):
        print('add_node_link: ', sender, app_data, user_data)
        link = dpg.add_node_link(app_data[0], app_data[1], parent=sender)
        self._invoke_update(event=EditorEventType.EVENT_LINK_ADD)

    def _delete_link(self, sender:int, app_data:Any, user_data:Any):
        print('delete_link:', sender, app_data, user_data)
        dpg.delete_item(app_data)
        self._invoke_update(event=EditorEventType.EVENT_NODE_DELETE)

    def _clear_lense(self):
        for group in self._lense_group_node_list:
            dpg.delete_item(group.widget())

        self._lense_group_node_list = []


    def _add_new_node(self, s, a, u):
        pass

    def _add_default_node(self):
        self._add_lense_group_node(SceneNode(self._editor_id, self.callback()))
        self._add_lense_group_node(FilmNode(self._editor_id, self.callback()))
        self._add_lense_group_node(ApertureStop(parent=self._editor_id, value_update_callback=self.callback()))

    def _add_lense_group_node(self, lense_group_node:LenseSurfaceGroup):
        self._lense_group_node_list.append(lense_group_node)
        # callable(self._update_callback) and self._update_callback()

class LenseDesignerWidget(Widget):

    def __init__(self, parent: int):
        super().__init__(parent=parent)
        with dpg.child(parent=parent) as self._widget_id:
            self._lense_canvas: LenseCanvasWidget = LenseCanvasWidget(parent=self.widget(),callback=self._canvas_update)
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
        print(args, kwargs)


    def _canvas_update(self, *args, **kwargs):
        pass

    def _lense_update(self):
        self.camera.refocus(0.2)
        lenses = self.camera.get_lenses_data()
        self.camera.gen_draw_rays_from_film()
        ray_points = self.camera.get_ray_points()

        self._lense_canvas.draw_lenses(np.array(lenses))
        self._lense_canvas.draw_rays(ray_points, self.camera.get_element_count() + 2, color=[0, 0, 255])
