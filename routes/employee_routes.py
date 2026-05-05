# مسارات لوحة الموظف


from flask import Blueprint, jsonify, render_template, session

from database import get_connection, sync_employee_workloads
from decorators import employee_required

employee_bp = Blueprint("employee", __name__, url_prefix="/employee")


def _row(conn):
    uid = session["user_id"]
    return conn.execute(
        """
        SELECT e.*, u.name AS emp_name, u.email
        FROM employees e JOIN users u ON u.id = e.user_id
        WHERE e.user_id = ?
        """,
        (uid,),
    ).fetchone()


@employee_bp.route("/dashboard")
@employee_required
def dashboard():
    conn = get_connection()
    try:
        emp = _row(conn)
    finally:
        conn.close()
    return render_template("employee/dashboard.html", emp=emp, page_title="لوحة الموظف")


@employee_bp.route("/my-tasks")
@employee_required
def my_tasks():
    conn = get_connection()
    try:
        emp = _row(conn)
        tasks = []
        if emp:
            tasks = conn.execute(
                """
                SELECT * FROM tasks WHERE assigned_to = ? ORDER BY datetime(created_at) DESC
                """,
                (emp["id"],),
            ).fetchall()
    finally:
        conn.close()
    return render_template("employee/my_tasks.html", emp=emp, tasks=tasks, page_title="مهامي")


@employee_bp.route("/performance")
@employee_required
def performance_page():
    conn = get_connection()
    try:
        emp = _row(conn)
        logs = []
        perf_chart = []
        if emp:
            logs = conn.execute(
                """
                SELECT pl.*, t.title
                FROM performance_logs pl
                JOIN tasks t ON t.id = pl.task_id
                WHERE pl.employee_id = ?
                ORDER BY datetime(pl.logged_at) DESC
                LIMIT 25
                """,
                (emp["id"],),
            ).fetchall()
            chunk = list(logs[:10])
            chunk.reverse()
            perf_chart = [{"label": str(i + 1), "score": float(r["score"] or 0)} for i, r in enumerate(chunk)]
    finally:
        conn.close()
    return render_template(
        "employee/performance.html",
        emp=emp,
        logs=logs,
        perf_chart=perf_chart,
        page_title="أدائي",
    )


@employee_bp.route("/tasks/<int:task_id>/start", methods=["POST"])
@employee_required
def task_start(task_id):
    conn = get_connection()
    try:
        emp = _row(conn)
        if not emp:
            return jsonify({"success": False, "message": "لم يتم العثور على ملف الموظف"}), 404

        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task or task["assigned_to"] != emp["id"]:
            return jsonify({"success": False, "message": "المهمة غير متاحة"}), 404

        if task["status"] != "assigned":
            return jsonify({"success": False, "message": "لا يمكن بدء هذه المهمة من حالتها الحالية"}), 400

        conn.execute("UPDATE tasks SET status = 'in_progress' WHERE id = ?", (task_id,))
        sync_employee_workloads(conn)
        conn.commit()
    finally:
        conn.close()

    return jsonify({"success": True})


@employee_bp.route("/tasks/<int:task_id>/finish", methods=["POST"])
@employee_required
def task_finish(task_id):
    conn = get_connection()
    try:
        emp = _row(conn)
        if not emp:
            return jsonify({"success": False, "message": "لم يتم العثور على ملف الموظف"}), 404

        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task or task["assigned_to"] != emp["id"]:
            return jsonify({"success": False, "message": "المهمة غير متاحة"}), 404

        if task["status"] != "in_progress":
            return jsonify({"success": False, "message": "أرسل للمراجعة من حالة التنفيذ فقط"}), 400

        conn.execute("UPDATE tasks SET status = 'in_review' WHERE id = ?", (task_id,))
        sync_employee_workloads(conn)

        admins = conn.execute("SELECT id FROM users WHERE role = 'admin'").fetchall()
        for a in admins:
            conn.execute(
                "INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)",
                (a["id"], f"المهمة «{task['title']}» أُرسلت للمراجعة من {session.get('user_name')}", "info"),
            )

        conn.commit()
    finally:
        conn.close()

    return jsonify({"success": True})
