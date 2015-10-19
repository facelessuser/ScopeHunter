"""
Scope Hunter.

Licensed under MIT
Copyright (c) 2012 - 2015 Isaac Muse <isaacmuse@gmail.com>
"""
import sublime
try:
    from SubNotify.sub_notify import SubNotifyIsReadyCommand as Notify
except Exception:
    class Notify(object):
        """Fallback Notify class if SubNotify is not found."""

        @classmethod
        def is_ready(cls):
            """Return False to disable SubNotify."""

            return False


def notify(msg):
    """Notify message."""

    settings = sublime.load_settings("scope_hunter.sublime-settings")
    if settings.get("use_sub_notify", False) and Notify.is_ready():
        sublime.run_command("sub_notify", {"title": "ScopeHunter", "msg": msg})
    else:
        sublime.status_message(msg)


def error(msg):
    """Error message."""

    settings = sublime.load_settings("scope_hunter.sublime-settings")
    if settings.get("use_sub_notify", False) and Notify.is_ready():
        sublime.run_command("sub_notify", {"title": "ScopeHunter", "msg": msg, "level": "error"})
    else:
        sublime.error_message("ScopeHunter:\n%s" % msg)
