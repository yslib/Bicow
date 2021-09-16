import sys
import os
from typing import Callable, Dict, Any, List, Tuple
import configparser

sys.path.append('..')
import dearpygui.dearpygui as dpg
import bicow.bicow as bc
from base.imgio import ImageBracket, open_image_as_bracket, open_path_as_brackets
from base.msg_queue import get_msg_queue, msg
from gui.utils import bind_event, bind_param
from gui.image_widget import ImageWidget
from gui.list_widget import ImageListWidget
from gui.bracket_series_container_widget import ImageContainerWidget
from gui.lense_designer import LenseDesignerWidget

CMR_CONFIG_FILE_PATH = r'D:\Code\Cameray\src'
CMR_FONT_FILE_PATH = r'C:\Windows\Fonts\msyh.ttc'
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

def bind_param_and_event(item:int, param, name, update_callback, type):
    bind_param(item, param,name)
    bind_event(item,update_callback, type)


msgqueue = get_msg_queue()

window_resize_callback = []

class App:
    def __init__(self) -> None:
        self._setup_init()
        self._setup_bicow()
        self._setup_uuid()
        self._setup_style()
        self._setup_window()
        self._setup_viewport()

    def _on_app_close(self, s,a,u):
        dpg.delete_item(s)
        self._app_config.write(open(CMR_CONFIG_FILE_PATH,'a'))
        print('_on_app_close')

    def _setup_style(self):
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
        self._gui_id_parameter_panel:int = None
        self._result_image_widget:ImageWidget = None
        self._image_container_widget:ImageContainerWidget = None
        self._lense_designer_widget:LenseDesignerWidget = None

    def _setup_bicow(self):
        bc.bicow_init()
        self._bicow_hdr:bc.BicowHDR = None


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
                dpg.add_text(label='test',parent=image_container_id)
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
            item = dpg.add_drag_float(label="K")
            bind_param_and_event(item, self._bicow_hdr.param, 'k', self._update_process, 'deactivated')
            item = dpg.add_drag_float(label="B")
            bind_param_and_event(item, self._bicow_hdr.param, 'b', self._update_process, 'deactivated')
            item = dpg.add_drag_float(label="Zmin")
            bind_param_and_event(item, self._bicow_hdr.param, 'zmin', self._update_process, 'deactivated')
            item = dpg.add_drag_float(label="Zmax")
            bind_param_and_event(item, self._bicow_hdr.param, 'zmax', self._update_process, 'deactivated')

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
        self._image_container_widget.set_data(image_brackets)
        if len(image_brackets) > 0:
            self._init_hdr_pipeline(image_brackets[0])
        else:
            print('Empty bracket!!!')

    def _update_current_bracket(self, bracket:ImageBracket)->None:
        """
        Init bracket to process while recreate parameter panel gui
        """
        rect = dpg.get_item_rect_size(self._result_image_widget.parent())
        self._bicow_hdr = bc.BicowHDR(rect)
        self._bicow_hdr.set_data(bracket)
        if self._gui_id_parameter_panel is not None:
            dpg.delete_item(self._gui_id_parameter_panel)
            self._gui_id_parameter_panel = None
        self._gui_id_parameter_panel = self._gui_add_parameter_panel(self._gui_id_parameter_panel_parent)

    def _init_hdr_pipeline(self, braket:ImageBracket):
        @msg
        def e():
            self._update_current_bracket(braket)
        e()

    def _update_process(self, s,a,u):
        @msg
        def proc():
            self._bicow_hdr.refine()
            output = self._bicow_hdr.get_processed_data().to_numpy()
            self._result_image_widget.from_numpy(output)
        proc()

    def _gui_add_bracket_preview(self):
        pass

    def _gui_add_result_image(self):
        image_view_id = dpg.add_image(self)
        pass

    def _update_result_image(self, item_id, rgba, width, height):
        dpg.add_dynamic_texture(width, height, rgba, id=self._timelapse_result_image_id)

    def _setup_timelapse_tab(self):
        with dpg.group(horizontal=True):
            with dpg.child(autosize_y=True, width=200, height=200) as cid:
                s = dpg.add_button(label='Export Settings...')
                with dpg.popup(s,modal=True,mousebutton=dpg.mvMouseButton_Left) as modal_id:
                    dpg.add_text('test')
                dpg.add_same_line()
                dpg.add_button(label='Export')
                self._image_container_widget = ImageContainerWidget(cid)
            with dpg.child() as a:
                self._gui_id_img_preview = self._gui_add_image_preview(a)
                with dpg.group(horizontal=True):
                    with dpg.child(width=800) as res_id:
                        # result image
                        self._result_image_widget = ImageWidget(res_id)
                    with dpg.child(width=200, autosize_x=True) as b:
                        self._gui_id_parameter_panel_parent = b


    def _gui_viewport_resize_event(self, sender, a, u):
        """
        Keep the root widget fill up the viewport
        """
        dpg.set_item_height(self._gui_id_app, a[3])
        dpg.set_item_width(self._gui_id_app, a[2])

    def _setup_viewport(self):
        if not dpg.is_viewport_created():
            icon = PROJECT_DIR+'/icon.png'
            vp = dpg.create_viewport(small_icon=icon,title='Bicow', large_icon=icon,width=1920,height=1080)
            dpg.set_viewport_resize_callback(lambda a, b:self._gui_viewport_resize_event(a, b, self._gui_id_app))
            dpg.setup_dearpygui(viewport=vp)
            dpg.show_viewport(vp)
            dpg.set_viewport_title(title='Bicow')
            # dpg.set_viewport_decorated(False)
            dpg.set_viewport_resizable(False)

    def _setup_window(self):

        with dpg.window(label="Cameray",id=self._gui_id_app,
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
                    dpg.add_menu_item(label='Exit', callback=self._on_app_close)

            with dpg.tab_bar():
                with dpg.tab(label="HDR Timelapse"):
                    self._setup_timelapse_tab()

                with dpg.tab(label="Lense Designer") as id:
                    self._lense_designer_widget:LenseDesignerWidget = LenseDesignerWidget(id)

    def _window_resize_callback(self, s,a,u):
        print('window resized: ',s,a,u)
        pass

    def show(self):
        while(dpg.is_dearpygui_running()):
            while not msgqueue.empty():
                event = msgqueue.get()
                callable(event) and event()
            dpg.render_dearpygui_frame()
        dpg.cleanup_dearpygui()
