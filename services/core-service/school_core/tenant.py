import threading

_thread_locals = threading.local()


def set_current_school_id(school_id):
    _thread_locals.school_id = school_id


def get_current_school_id():
    return getattr(_thread_locals, "school_id", None)


def clear_current_school_id():
    _thread_locals.school_id = None


def has_current_school_id():
    return hasattr(_thread_locals, "school_id") and _thread_locals.school_id is not None