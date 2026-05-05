# مسارات تسجيل الدخول والخروج


from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from database import get_connection, verify_password

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def home():
    uid = session.get("user_id")
    role = session.get("user_role")
    if not uid or not role:
        return redirect(url_for("auth.login_page"))
    if role == "admin":
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("employee.dashboard"))


@auth_bp.route("/login", methods=["GET"])
def login_page():
    if session.get("user_id"):
        return redirect(url_for("auth.home"))
    return render_template("auth/login.html")


@auth_bp.route("/login", methods=["POST"])
def login_post():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify({"success": False, "message": "البريد وكلمة المرور مطلوبان"}), 400

    conn = get_connection()
    try:
        row = conn.execute("SELECT id, password, role FROM users WHERE email = ?", (email,)).fetchone()
    finally:
        conn.close()

    if not row or not verify_password(row["password"], password):
        return jsonify({"success": False, "message": "بيانات الدخول غير صحيحة"}), 401

    conn = get_connection()
    try:
        u = conn.execute("SELECT id, name, role FROM users WHERE id = ?", (row["id"],)).fetchone()
    finally:
        conn.close()

    session["user_id"] = u["id"]
    session["user_role"] = u["role"]
    session["user_name"] = u["name"]

    dest = "/employee/dashboard" if u["role"] == "employee" else "/admin/dashboard"
    return jsonify({"success": True, "redirect": dest})


@auth_bp.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for("auth.login_page"))
