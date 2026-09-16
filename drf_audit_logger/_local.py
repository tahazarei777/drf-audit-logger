"""
Thread-local storage for the current request context.

This allows signal handlers to access the current user, IP address,
and user agent without passing them explicitly through the call stack.
"""
import threading

_local = threading.local()


# --------------------------------------------------------
# User
# --------------------------------------------------------
def get_current_user():
    """Return the current authenticated user, or None."""
    user = getattr(_local, 'user', None)
    if user and user.is_authenticated:
        return user
    return None


def set_current_user(user):
    """Set the current user for this thread."""
    _local.user = user


# --------------------------------------------------------
# IP Address
# --------------------------------------------------------
def get_current_ip():
    """Return the current client IP, or None."""
    return getattr(_local, 'ip_address', None)


def set_current_ip(ip_address):
    """Set the current IP for this thread."""
    _local.ip_address = ip_address


# --------------------------------------------------------
# User Agent
# --------------------------------------------------------
def get_current_user_agent():
    """Return the current user agent, or ''."""
    return getattr(_local, 'user_agent', '')


def set_current_user_agent(user_agent):
    """Set the current user agent for this thread."""
    _local.user_agent = user_agent


# --------------------------------------------------------
# Request
# --------------------------------------------------------
def get_current_request():
    """Return the current request, or None."""
    return getattr(_local, 'request', None)


def set_current_request(request):
    """Set the current request for this thread."""
    _local.request = request


# --------------------------------------------------------
# Cleanup
# --------------------------------------------------------
def clear():
    """Clear all thread-local data. Called at the end of each request."""
    for attr in ('user', 'ip_address', 'user_agent', 'request'):
        if hasattr(_local, attr):
            delattr(_local, attr)