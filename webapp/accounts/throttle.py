"""Brute-force protection for the login form.

Failed logins are counted per username and per client IP in the cache.
Once either counter reaches LOGIN_MAX_ATTEMPTS, further attempts are refused
(without even checking the password) until LOGIN_LOCKOUT_SECONDS have passed
since the last failure. A successful login clears the username counter.

Note: the default local-memory cache is per process. When running several
worker processes, configure a shared cache (database or Redis) in settings.
"""
import hashlib
import logging

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger("accounts")


def _max_attempts():
    return getattr(settings, "LOGIN_MAX_ATTEMPTS", 5)


def _lockout_seconds():
    return getattr(settings, "LOGIN_LOCKOUT_SECONDS", 15 * 60)


def client_ip(request):
    # REMOTE_ADDR only: X-Forwarded-For can be spoofed by the client unless a
    # trusted proxy rewrites it.
    return request.META.get("REMOTE_ADDR", "") if request else ""


def _keys(username, ip):
    uname = hashlib.sha256((username or "").strip().lower().encode()).hexdigest()
    keys = [f"login-fail:user:{uname}"]
    if ip:
        # The IP limit is looser so that one shared office IP isn't locked out by one user.
        keys.append(f"login-fail:ip:{ip}")
    return keys


def _limit_for(key):
    return _max_attempts() * (4 if ":ip:" in key else 1)


def is_locked(username, ip):
    return any(cache.get(key, 0) >= _limit_for(key) for key in _keys(username, ip))


def register_failure(username, ip):
    timeout = _lockout_seconds()
    for key in _keys(username, ip):
        try:
            count = cache.incr(key)
            cache.touch(key, timeout)
        except ValueError:
            count = 1
            cache.set(key, count, timeout)
        if count == _limit_for(key):
            logger.warning("Login locked out (%s) after %s failures, ip=%s", key.split(":")[1], count, ip)


def reset(username):
    cache.delete(_keys(username, None)[0])
