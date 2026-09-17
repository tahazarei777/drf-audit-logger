"""
Thread-local storage for the current request context.
"""
import threading

_local = threading.local()


def get_current_user():
    """Return the current authenticated user, or None."""
    user = getattr(_local, 'user', None)
    if user and user.is_authenticated:
        return user
    return None


def set_current_user(user):
    _local.user = user


def get_current_ip():
    return getattr(_local, 'ip_address', None)


def set_current_ip(ip_address):
    _local.ip_address = ip_address


def get_current_user_agent():
    return getattr(_local, 'user_agent', '')


def set_current_user_agent(user_agent):
    _local.user_agent = user_agent


def get_current_request():
    return getattr(_local, 'request', None)


def set_current_request(request):
    _local.request = request


def clear():
    """Clear all thread-local data."""
    for attr in ('user', 'ip_address', 'user_agent', 'request'):
        if hasattr(_local, attr):
            delattr(_local, attr)