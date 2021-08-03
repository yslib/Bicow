import sys
sys.path.append('..')
from os import waitpid
import sys
sys.path.append('..')
import configparser
import dearpygui.dearpygui as dpg
from core.cameray import CamerayHDR,HDRParamSet, cc_init, cc_shutdown
from base.imgio import ImageBracket, open_image_as_bracket, open_path_as_brackets
from typing import Callable, Dict, Any, List, Tuple
from base.msg_queue import get_msg_queue, msg

CMR_CONFIG_FILE_PATH = r'D:\Code\Cameray\src'
CMR_FONT_FILE_PATH = r'C:\Windows\Fonts\msyh.ttc'

def bind_param(item:int, param:HDRParamSet, name:str):
    pass

msgqueue = get_msg_queue()
class App:
    def __init__(self) -> None:
        self._setup_init()
        self._setup_uuid()
        self._setup_fonts()
        self._setup_window()
        self._setup_viewport()
        self._setup_cameray()

    def _on_app_close(self, s,a,u):
        dpg.delete_item(s)
        self._app_config.write(open(CMR_CONFIG_FILE_PATH,'a'))
        print('_on_app_close')

    def _setup_fonts(self):
        with dpg.font_registry():
            dpg.add_font(CMR_FONT_FILE_PATH, 18, default_font=True)

    def _setup_init(self):
        self._app_config = configparser.ConfigParser()
        self._app_config.read(CMR_CONFIG_FILE_PATH)

    def _setup_uuid(self):
        self._gui_id_app:int = dpg.generate_uuid()
        self._gui_id_img_preview:int = None
        self._gui_id_image_list_box:int = None
        self._gui_id_image_bracket_list_box:int = None
        self._gui_id_parameter_panel_parent:int = None
        self._timelapse_result_image_id:int = None
        self._timelapse_image_image_series_id:List[int] = []

    def _setup_cameray(self):
        cc_init()
        self._cc:CamerayHDR = None

    def _init_timelaplse_image(self,count:int, size:Tuple[int,int]):
        """
        delete old image init new image
        """
        dpg.delete_item(self._timelapse_result_image_id)
        for e in self._timelapse_image_image_series_id:
            dpg.delete_item(e)
        self._timelapse_image_image_series_id = []
        self._timelapse_result_image_id = dpg.generate_uuid()
        for i in range(count):
            self._timelapse_image_image_series_id.append(dpg.generate_uuid())

    def _set_result_image(self, image_id, data:List[float], size:Tuple[int,int]):
        """
        data must be arranged as a 4-channel list and each channel is range [0, 1]
        """
        dpg.add_dynamic_texture(size[0], size[1], data,id=image_id)


    def _gui_add_image_preview(self, parent)->int:
        """
        Image Preview Widget
        Returns the container's id
        """
        with dpg.child(autosize_x=True, height=200,horizontal_scrollbar=True, parent=parent): # image series preview
            with dpg.group(horizontal=True) as image_container_id:
                pass
        return image_container_id

    def _on_image_listbox_callback(self,sender,app_data,user_data):
        print(sender, app_data, user_data)
        pass

    def _on_bracket_listbox_callback(self, sender, app_data, user_data):
        print(sender, app_data, user_data)
        pass

    def _gui_add_popup(self, text:str, title='Window'):
        x = dpg.get_viewport_client_width()
        y = dpg.get_viewport_client_height()
        with dpg.window(label=title, modal=True, pos=[x/2,y/2]) as modal_id:
            dpg.add_text(text)
            dpg.add_separator()
            dpg.add_button(parent=modal_id,label="OK", width=75, callback=lambda: dpg.delete_item(modal_id))

    def _gui_add_parameter_panel(self, parent)->int:
        with dpg.child(autosize_x=True, parent=parent) as w:

            @msg
            def B(val):
                self._cc.param.b = val
            dpg.add_drag_float(label="B", 
                    default_value=self._cc.param.b,
                    min_value=self._cc.param.__class__.b.min_value,
                    max_value=self._cc.param.__class__.b.max_value,
                    format="%.02f", 
                    speed=0.01,
                    callback=lambda s,a,u:B(a))

            @msg
            def K(val):
                self._cc.param.k = val

            dpg.add_drag_float(label="K", 
                    default_value=self._cc.param.k,
                    min_value=self._cc.param.__class__.k.min_value,
                    max_value=self._cc.param.__class__.k.max_value,
                    format="%.02f", 
                    speed=0.01,
                    callback=lambda s,a,u:K(a))

            @msg
            def Zmin(val):
                self._cc.param.zmin = val

            dpg.add_drag_float(label="Zmin", 
                    default_value=self._cc.param.zmin,
                    min_value=self._cc.param.__class__.zmin.min_value,
                    max_value=self._cc.param.__class__.zmax.max_value,
                    format="%.02f", 
                    speed=0.01,
                    callback=lambda s,a,u:Zmin(a))

            @msg
            def Zmax(val):
                self._cc.param.zmax = val

            dpg.add_drag_float(label="Zmax", 
                    default_value=self._cc.param.zmax,
                    min_value=self._cc.param.__class__.zmax.min_value,
                    max_value=self._cc.param.__class__.zmax.max_value,
                    format="%.02f", 
                    speed=0.01,
                    callback=lambda s,a,u:Zmax(a))

            #  dpg.add_combo(("AAAA", "BBBB", "CCCC", "DDDD", "EEEE", "FFFF", "GGGG", "HHHH", "IIII", "JJJJ", "KKKK"), label="combo", default_value="AAAA")
            #  dpg.add_input_int(label="input int")
            #  dpg.add_input_float(label="input float")
            #  dpg.add_input_float(label="input scientific", format="%e")
            #  dpg.add_input_floatx(label="input floatx", default_value=[1,2,3,4])
            #  dpg.add_drag_int(label="drag int")
            #  dpg.add_drag_int(label="drag int 0..100", format="%d%%")
            #  dpg.add_slider_int(label="slider int", max_value=3)
            #  dpg.add_slider_float(label="slider float", max_value=1.0, format="ratio = %.3f", callback=lambda a,u,s:print(a,u,s))
            #  dpg.add_slider_int(label="slider angle", min_value=-360, max_value=360, format="%d deg")
            #  dpg.add_color_edit((102, 179, 0, 128), label="color edit 4")
            #  dpg.add_color_edit(default_value=(.5, 1, .25, .1), label="color edit 4")
            #  dpg.add_listbox(("Apple", "Banana", "Cherry", "Kiwi", "Mango", "Orange", "Pineapple", "Strawberry", "Watermelon"), label="listbox", num_items=4)
            #  dpg.add_color_button()
        return w

    def _log(self, sender, app_data, user_data):
        pass

    def _on_open_image(self, sender:int, app_data:Dict[str,str], user_data:Any):
        print(app_data)
        if user_data == 'open_path':
            path = app_data.get('current_path', None)
            if not path:
                self._gui_add_popup('Invalid path', 'Error')
                return
            image_brackets = open_path_as_brackets(path, 10)
        elif user_data == 'open_bracket':
            fullname = app_data.get('selections',{}).values()
            image_brackets = open_image_as_bracket(fullname)
        self._open_from_brackets(image_brackets)

    def _open_from_brackets(self, image_brackets: List[ImageBracket]):
        bracket_list_item = [b.name for b in image_brackets]
        image_list_item = [i.filename for b in image_brackets for i in b.images]
        # print(bracket_list_item, image_list_item)
        dpg.configure_item(item=self._gui_id_image_list_box, items=image_list_item, num_items=20)
        dpg.configure_item(item=self._gui_id_image_bracket_list_box, items=bracket_list_item, num_items=20)
        self._open_hdr_pipeline(image_brackets)

    def _open_hdr_pipeline(self, braket_list:List[ImageBracket]):
        @msg
        def e():
            self._cc = CamerayHDR(braket_list)
            self._gui_add_parameter_panel(self._gui_id_parameter_panel_parent)
        e()

    def _gui_add_bracket_preview(self):
        pass

    def _gui_add_result_image(self):
        pass

    def _setup_timelapse_tab(self):
        with dpg.group(horizontal=True):
            with dpg.child(autosize_y=True, width=200):
                s = dpg.add_button(label='Export Settings...')
                with dpg.popup(s,modal=True,mousebutton=dpg.mvMouseButton_Left) as modal_id:
                    dpg.add_text('test')
                dpg.add_same_line()
                dpg.add_button(label='Export')
                with dpg.child(height=250):
                    dpg.add_text('Brackets')
                    self._gui_id_image_bracket_list_box = dpg.add_listbox(label='',items=[],num_items=10,width=200,callback=self._on_bracket_listbox_callback)
                with dpg.child():
                    dpg.add_text('Image')
                    self._gui_id_image_list_box = dpg.add_listbox(label='',items=[],num_items=10,width=200, callback=self._on_bracket_listbox_callback)
            with dpg.child() as a:
                self._gui_id_img_preview = self._gui_add_image_preview(a)
                with dpg.group(horizontal=True):
                    with dpg.child(width=800):
                        # result image
                        pass
                    with dpg.child(width=200,autosize_x=True) as b:
                        self._gui_id_parameter_panel_parent = b


    def _gui_viewport_resize_event(self, sender, a, u):
        """
        Keep the root widget fill up the viewport
        """
        dpg.set_item_height(self._gui_id_app, a[3])
        dpg.set_item_width(self._gui_id_app, a[2])

    def _setup_viewport(self):
        dpg.set_viewport_resize_callback(lambda a, b:self._gui_viewport_resize_event(a, b, self._gui_id_app))
        dpg.setup_viewport()
        dpg.set_viewport_title(title='The Best Image Compositor for Old Wizard in Binjiang District')

    def _setup_window(self):

        with dpg.window(label="Cameray",id=self._gui_id_app,
                        width=400,
                        height=400,
                        on_close=self._on_app_close,
                        pos=(0, 0),
                        no_title_bar=True,
                        no_move=True,
                        no_resize=True):
            with dpg.menu_bar():
                with dpg.menu(label="File"):
                    def open_folder_callback(s,a,u):
                        with dpg.file_dialog(label="Open Folder",callback=self._on_open_image,user_data='open_path',default_path=r'data'):
                            dpg.add_file_extension(".*", color=(255, 255, 255, 255))

                    def open_brackets_callback(s,a,u):
                        with dpg.file_dialog(label='Open Bracket',callback=self._on_open_image,user_data='open_bracket'):
                            dpg.add_file_extension(".*", color=(255, 255, 255, 255))

                    dpg.add_menu_item(label="Open Folder...", callback=open_folder_callback)
                    dpg.add_menu_item(label="Open Bracket...", callback=open_brackets_callback)

            with dpg.tab_bar():
                with dpg.tab(label="HDR Timelapse"):
                    self._setup_timelapse_tab()

                with dpg.tab(label="Image Inspector"):
                    pass

    def show(self):
        if not dpg.is_viewport_created():
            vp = dpg.create_viewport()
            dpg.setup_dearpygui(viewport=vp)
            dpg.show_viewport(vp)
        while(dpg.is_dearpygui_running()):
            while not msgqueue.empty():
                event = msgqueue.get()
                callable(event) and event()
            dpg.render_dearpygui_frame()
        dpg.cleanup_dearpygui()