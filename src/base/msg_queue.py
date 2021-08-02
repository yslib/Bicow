import queue
import functools

_msg_queue = queue.Queue(50)

def msg(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        global _msg_queue
        _msg_queue.put(lambda:func(*args,**kwargs))
    return wrapper

def get_msg_queue():
    return _msg_queue