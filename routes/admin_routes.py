# مسارات لوحة المدير وإدارة المهام والموظفين


import json
from datetime import datetime

from flask import Blueprint, jsonify, render_template, request, session

from ai_engine.matcher import find_best_match
from database import get_connection, hash_password, sync_employee_workloads
from decorators import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _notify(conn, user_id, message, ntype="info"):
    conn.execute(
        "INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)",
        (user_id, message, ntype),
    )


def _notify_all_admins(conn, message, ntype="info"):
    rows = conn.execute("SELECT id FROM users WHERE role = 'admin'").fetchall()
    for r in rows:
        _notify(conn, r["id"], message, ntype)


def _employee_user_id(conn, employee_id):
    row = conn.execute("SELECT user_id FROM employees WHERE id = ?", (employee_id,)).fetchone()
    return row["user_id"] if row else None


@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    return render_template("admin/dashboard.html", page_title="لوحة المدير")


@admin_bp.route("/tasks")
@admin_required
def tasks_page():
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT t.*, u.name AS assignee_name
            FROM tasks t
            LEFT JOIN employees e ON e.id = t.assigned_to
            LEFT JOIN users u ON u.id = e.user_id
            ORDER BY datetime(t.created_at) DESC
            """
        ).fetchall()
        employees = conn.execute(
            """
            SELECT e.id, u.name, u.email, e.department
            FROM employees e JOIN users u ON u.id = e.user_id
            ORDER BY u.name
            """
        ).fetchall()
    finally:
        conn.close()
    return render_template("admin/tasks.html", tasks=rows, employees=employees, page_title="إدارة المهام")


@admin_bp.route("/tasks/create", methods=["POST"])
@admin_required
def tasks_create():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    priority = data.get("priority") or "medium"
    skills = data.get("required_skills") or []
    deadline = (data.get("deadline") or "").strip()
    est = float(data.get("estimated_hours") or 4.0)

    if priority not in ("low", "medium", "high", "critical"):
        priority = "medium"
    if not title:
        return jsonify({"success": False, "message": "عنوان المهمة مطلوب"}), 400

    skills_json = json.dumps(skills, ensure_ascii=False)
    creator = session["user_id"]

    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO tasks (title, description, priority, status, required_skills, deadline,
                estimated_hours, created_by)
            VALUES (?, ?, ?, 'new', ?, ?, ?, ?)
            """,
            (title, description, priority, skills_json, deadline or None, est, creator),
        )
        tid = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (tid,)).fetchone()
        matches = find_best_match(conn, row)
        notes = json.dumps(matches, ensure_ascii=False)
        conn.execute("UPDATE tasks SET ai_notes = ? WHERE id = ?", (notes, tid))
        conn.commit()
    finally:
        conn.close()

    return jsonify({"success": True, "task_id": tid, "matches": matches})


@admin_bp.route("/tasks/<int:task_id>/assign", methods=["POST"])
@admin_required
def tasks_assign(task_id):
    data = request.get_json(silent=True) or {}
    employee_id = data.get("employee_id")
    if employee_id is None:
        return jsonify({"success": False, "message": "معرّف الموظف مطلوب"}), 400
    employee_id = int(employee_id)

    conn = get_connection()
    try:
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            return jsonify({"success": False, "message": "المهمة غير موجودة"}), 404

        emp = conn.execute(
            """
            SELECT e.*, u.name FROM employees e JOIN users u ON u.id = e.user_id WHERE e.id = ?
            """,
            (employee_id,),
        ).fetchone()
        if not emp:
            return jsonify({"success": False, "message": "الموظف غير موجود"}), 404

        mx = max(int(emp["max_workload"] or 1), 1)
        cur = int(emp["current_workload"] or 0)
        if cur >= mx:
            return jsonify({"success": False, "message": "الموظف بلغ الحد الأقصى للحمل الوظيفي"}), 400

        row_match = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        matches = find_best_match(conn, row_match)
        top_score = matches[0]["score"] if matches else None

        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            """
            UPDATE tasks SET assigned_to = ?, status = 'assigned', assigned_at = ?, ai_match_score = ?
            WHERE id = ?
            """,
            (employee_id, now, top_score, task_id),
        )
        sync_employee_workloads(conn)

        uid = _employee_user_id(conn, employee_id)
        if uid:
            _notify(conn, uid, f"تم تعيين المهمة «{task['title']}» لك", "info")

        conn.commit()
    finally:
        conn.close()

    return jsonify({"success": True})


@admin_bp.route("/tasks/<int:task_id>/status", methods=["POST"])
@admin_required
def tasks_status(task_id):
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    actual_hours = data.get("actual_hours")

    allowed = ("new", "analyzing", "assigned", "in_progress", "in_review", "completed", "on_hold")
    if new_status not in allowed:
        return jsonify({"success": False, "message": "حالة غير صالحة"}), 400

    conn = get_connection()
    try:
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            return jsonify({"success": False, "message": "المهمة غير موجودة"}), 404

        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        extras = []
        params = []

        if new_status == "completed":
            extras.append("completed_at = ?")
            params.append(now)
            if actual_hours is not None:
                extras.append("actual_hours = ?")
                params.append(float(actual_hours))

            ah = float(actual_hours) if actual_hours is not None else float(task["estimated_hours"] or 4)
            est = float(task["estimated_hours"] or 4)
            on_time = 1 if ah <= est * 1.2 else 0
            score = min(100.0, 72.0 + (est / max(ah, 0.1)) * 12.0)

            if task["assigned_to"]:
                conn.execute(
                    """
                    INSERT INTO performance_logs (employee_id, task_id, score, completion_time, on_time, logged_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (task["assigned_to"], task_id, score, ah, on_time, now),
                )
                conn.execute(
                    "UPDATE employees SET total_tasks_done = total_tasks_done + 1 WHERE id = ?",
                    (task["assigned_to"],),
                )
                _notify_all_admins(conn, f"اكتملت المهمة «{task['title']}»", "success")

        frag = ", ".join(extras)
        sql = "UPDATE tasks SET status = ?"
        if frag:
            sql += ", " + frag
        sql += " WHERE id = ?"
        conn.execute(sql, [new_status] + params + [task_id])
        sync_employee_workloads(conn)
        conn.commit()
    finally:
        conn.close()

    return jsonify({"success": True})


@admin_bp.route("/employees")
@admin_required
def employees_page():
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT e.*, u.name, u.email
            FROM employees e JOIN users u ON u.id = e.user_id
            ORDER BY u.name
            """
        ).fetchall()
    finally:
        conn.close()
    return render_template("admin/employees.html", employees=rows, page_title="الموظفون")


@admin_bp.route("/employees/create", methods=["POST"])
@admin_required
def employees_create():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    department = (data.get("department") or "").strip()
    skills = data.get("skills") or []
    perf = float(data.get("performance_score") or 80.0)
    spd = float(data.get("speed_score") or 75.0)

    if not name or not email or not department:
        return jsonify({"success": False, "message": "الحقول الأساسية مطلوبة"}), 400

    conn = get_connection()
    try:
        exists = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if exists:
            return jsonify({"success": False, "message": "البريد مستخدم مسبقاً"}), 400

        conn.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, 'employee')",
            (name, email, hash_password("")),
        )
        uid = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
        skills_json = json.dumps(skills, ensure_ascii=False)
        conn.execute(
            """
            INSERT INTO employees (user_id, department, skills, performance_score, speed_score)
            VALUES (?, ?, ?, ?, ?)
            """,
            (uid, department, skills_json, perf, spd),
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"success": True})


@admin_bp.route("/reports")
@admin_required
def reports_page():
    return render_template("admin/reports.html", page_title="التقارير والتحليلات")
