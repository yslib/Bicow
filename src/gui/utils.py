import dearpygui.dearpygui as dpg
from typing import Callable, Any
from base.msg_queue import msg

def bind_param(item:int, param:Any, name:str):
    prop = param.__class__.__dict__[name]

    @msg
    def value(val):
        setattr(param, name, val)

    dpg.configure_item(item,
            default_value=getattr(param, name, 0),
            min_value=prop.min_value,
            max_value=prop.max_value,
            format="%.02f",
            speed=0.01,
            callback=lambda s,a,u:value(a))


def bind_event(item:int, event_callback:Callable[[Any,Any,Any],None], type:str):
    """
    Binds an event handler for a give widget
    event type listed as:
    clicked,
    hover,
    activated,
    active,
    deactivated,
    deactivated_after_edit,
    edited,
    focus,
    toggled,
    visible
    """

    if type == 'clicked':
        dpg.add_clicked_handler(item, 0, callback=event_callback)
    elif type == 'hover':
        dpg.add_hover_handler(item, callback=event_callback)
    elif type == 'activated':
        dpg.add_activated_handler(item, callback=event_callback)
    elif type == 'active':
        dpg.add_active_handler(item, callback=event_callback)
    elif type == 'deactivated_after_edit':
        dpg.add_deactivated_after_edit_handler(item, callback=event_callback)
    elif type == 'deactivated':
        dpg.add_deactivated_handler(item, callback=event_callback)
    elif type == 'edited':
        dpg.add_edited_handler(item, callback=event_callback)
    elif type == 'focus':
        dpg.add_focus_handler(item, callback=event_callback)
    elif type == 'toggled':
        dpg.add_toggled_open_handler(item, callback=event_callback)
    elif type == 'visible':
        dpg.add_visible_handler(item, callback=event_callback)