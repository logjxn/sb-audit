import ctypes


def is_admin() -> bool:
    """True if the current process has Windows administrator rights.

    Returns False on any failure, including non-Windows platforms where
    ctypes.windll does not exist.
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False