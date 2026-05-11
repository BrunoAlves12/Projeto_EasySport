from functools import wraps

from flask import flash, redirect, session, url_for


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Tem de fazer login primeiro.", "danger")
            return redirect(url_for("auth.login_page"))

        return view(*args, **kwargs)

    return wrapper


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Acesso restrito ao administrador.", "danger")
            return redirect(url_for("main.index"))

        return view(*args, **kwargs)

    return wrapper
