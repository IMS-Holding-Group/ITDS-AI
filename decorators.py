# دوال حماية المسارات والجلسات
from functools import wraps

from flask import jsonify, redirect, session, url_for


def login_required(view_fn):
    @wraps(view_fn)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login_page"))
        return view_fn(*args, **kwargs)

    return wrapped


def login_required_api(view_fn):
    @wraps(view_fn)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"success": False, "message": "يجب تسجيل الدخول"}), 401
        return view_fn(*args, **kwargs)

    return wrapped


def admin_required(view_fn):
    @wraps(view_fn)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login_page"))
        if session.get("user_role") != "admin":
            return redirect(url_for("auth.home"))
        return view_fn(*args, **kwargs)

    return wrapped


def employee_required(view_fn):
    @wraps(view_fn)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login_page"))
        if session.get("user_role") != "employee":
            return redirect(url_for("auth.home"))
        return view_fn(*args, **kwargs)

    return wrapped


def admin_required_api(view_fn):
    @wraps(view_fn)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"success": False, "message": "يجب تسجيل الدخول"}), 401
        if session.get("user_role") != "admin":
            return jsonify({"success": False, "message": "غير مصرّح"}), 403
        return view_fn(*args, **kwargs)

    return wrapped


def employee_required_api(view_fn):
    @wraps(view_fn)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"success": False, "message": "يجب تسجيل الدخول"}), 401
        if session.get("user_role") != "employee":
            return jsonify({"success": False, "message": "غير مصرّح"}), 403
        return view_fn(*args, **kwargs)

    return wrapped
