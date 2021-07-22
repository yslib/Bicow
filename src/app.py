import dearpygui.dearpygui as dpg

class App:
    def __init__(self) -> None:
        self._setup_uuid()
        self._setup_window()
        self._setup_viewport()

    def _setup_uuid(self):
        self._gui_id_app = dpg.generate_uuid()
        self._gui_id_img_preview = None
        self._gui_id_image_list_box = None

    def _gui_add_image_preview(self, parent)->int:
        """
        Image Preview Widget
        Returns the container's id
        """
        with dpg.child(autosize_x=True, height=200,horizontal_scrollbar=True, parent=parent): # image series preview
            with dpg.group(horizontal=True) as image_container_id:
                pass
        return image_container_id

    def _gui_add_parameter_panel(self, parent)->int:
        with dpg.child(autosize_x=True) as w:
            dpg.add_text("Value", label="Label", show_label=True)
            dpg.add_combo(("AAAA", "BBBB", "CCCC", "DDDD", "EEEE", "FFFF", "GGGG", "HHHH", "IIII", "JJJJ", "KKKK"), label="combo", default_value="AAAA")
            dpg.add_input_text(label="input text", default_value="Hello, world!")
            dpg.add_input_text(label="input text (w/ hint)", hint="enter text here")
            dpg.add_input_int(label="input int")
            dpg.add_input_float(label="input float")
            dpg.add_input_float(label="input scientific", format="%e")
            dpg.add_input_floatx(label="input floatx", default_value=[1,2,3,4])
            dpg.add_drag_int(label="drag int")
            dpg.add_drag_int(label="drag int 0..100", format="%d%%")
            dpg.add_drag_float(label="drag float")
            dpg.add_drag_float(label="drag small float", default_value=0.0067, format="%.06f ns")
            dpg.add_slider_int(label="slider int", max_value=3)
            dpg.add_slider_float(label="slider float", max_value=1.0, format="ratio = %.3f")
            dpg.add_slider_int(label="slider angle", min_value=-360, max_value=360, format="%d deg")
            dpg.add_color_edit((102, 179, 0, 128), label="color edit 4")
            dpg.add_color_edit(default_value=(.5, 1, .25, .1), label="color edit 4")
            dpg.add_listbox(("Apple", "Banana", "Cherry", "Kiwi", "Mango", "Orange", "Pineapple", "Strawberry", "Watermelon"), label="listbox", num_items=4)
            dpg.add_color_button()
        return w

    def _on_app_close(self, s,a,u):
        dpg.delete_item(s)

    def _log(self, sender, app_data, user_data):
        pass

    def _on_open_folder(self, s,a,u):
        print('_on_open_folder',s,a,u)

    def _setup_timelapse_tab(self):
        with dpg.group(horizontal=True):
            with dpg.child(autosize_y=True, width=200):
                s = dpg.add_button(label='Export Settings...')
                with dpg.popup(s,modal=True,mousebutton=dpg.mvMouseButton_Left) as modal_id:
                    dpg.add_text('test')
                dpg.add_same_line()
                dpg.add_button(label='Export')
                with dpg.child(height=250):
                    pass
                with dpg.child():
                    self._gui_id_image_list_box = dpg.add_listbox(label='Image',items=[])
            with dpg.child() as a:
                self._gui_id_img_preview = self._gui_add_image_preview(a)
                with dpg.group(horizontal=True):
                    with dpg.child(width=800):
                        # result image
                        pass
                    with dpg.child(width=100,autosize_x=True) as b:
                        self._gui_add_parameter_panel = self._gui_add_parameter_panel(b)
                        pass


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
                        with dpg.file_dialog(label="Open Folder",callback=self._on_open_folder):
                            dpg.add_file_extension(".*", color=(255, 255, 255, 255))

                    dpg.add_menu_item(label="Open Folder", callback=open_folder_callback)

            with dpg.tab_bar():
                with dpg.tab(label="HDR Timelapse"):
                    self._setup_timelapse_tab()

                with dpg.tab(label="Image Inspector"):
                    pass

    def show(self):
        dpg.start_dearpygui()

if __name__ == '__main__':
    App().show()