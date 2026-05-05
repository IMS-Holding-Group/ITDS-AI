# واجهات JSON للبيانات والتحليلات
from flask import Blueprint, jsonify, request, session

from ai_engine.analyzer import analyze_data
from ai_engine.burnout_detector import detect_burnout
from ai_engine.matcher import find_best_match
from database import get_connection
from decorators import admin_required_api, login_required_api

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/tasks/stats")
@login_required_api
def tasks_stats():
    conn = get_connection()
    try:
        role = session.get("user_role")
        emp_params = []
        prefix = ""
        if role == "employee":
            erow = conn.execute(
                "SELECT id FROM employees WHERE user_id = ?", (session["user_id"],)
            ).fetchone()
            if not erow:
                return jsonify(
                    {
                        "success": True,
                        "data": {"total_tasks": 0, "active_tasks": 0, "completion_week_pct": 0.0},
                    }
                )
            prefix = "WHERE assigned_to = ?"
            emp_params.append(erow["id"])

        total = conn.execute(f"SELECT COUNT(*) AS c FROM tasks {prefix}", emp_params).fetchone()["c"]
        active_where = (
            f"{prefix} {'AND' if prefix else 'WHERE'} status IN ('assigned','in_progress','in_review','analyzing')"
        )
        active = conn.execute(f"SELECT COUNT(*) AS c FROM tasks {active_where}", emp_params).fetchone()["c"]

        week_where = (
            f"{prefix} {'AND' if prefix else 'WHERE'} status = 'completed' "
            "AND datetime(completed_at) >= datetime('now','-7 days')"
        )
        completion_week = conn.execute(f"SELECT COUNT(*) AS c FROM tasks {week_where}", emp_params).fetchone()["c"]

        denom_sql = f"SELECT COUNT(*) AS c FROM tasks {prefix}"
        denom = conn.execute(denom_sql, emp_params).fetchone()["c"]
        pct_week = round((completion_week / denom * 100.0), 1) if denom else 0.0

        stats_body = {"total_tasks": total, "active_tasks": active, "completion_week_pct": pct_week}

        if role == "admin":
            available = conn.execute(
                """
                SELECT COUNT(*) AS c FROM employees e
                WHERE e.is_available = 1 AND e.current_workload < e.max_workload
                """
            ).fetchone()["c"]
            stats_body["available_employees"] = available
    finally:
        conn.close()

    return jsonify({"success": True, "data": stats_body})


@api_bp.route("/employees/stats")
@admin_required_api
def employees_stats():
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT u.name, e.performance_score, e.speed_score, e.current_workload, e.max_workload,
                   e.burnout_risk, e.department
            FROM employees e JOIN users u ON u.id = e.user_id
            ORDER BY u.name
            """
        ).fetchall()
        items = [
            {
                "name": r["name"],
                "performance_score": r["performance_score"],
                "speed_score": r["speed_score"],
                "current_workload": r["current_workload"],
                "max_workload": r["max_workload"],
                "burnout_risk": r["burnout_risk"],
                "department": r["department"],
            }
            for r in rows
        ]
    finally:
        conn.close()

    return jsonify({"success": True, "data": {"employees": items}})


@api_bp.route("/ai/match/<int:task_id>")
@admin_required_api
def ai_match(task_id):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            return jsonify({"success": False, "message": "المهمة غير موجودة"}), 404
        matches = find_best_match(conn, row)
    finally:
        conn.close()

    return jsonify({"success": True, "data": {"matches": matches}})


@api_bp.route("/ai/burnout")
@admin_required_api
def ai_burnout():
    conn = get_connection()
    try:
        rows = detect_burnout(conn)
    finally:
        conn.close()

    return jsonify({"success": True, "data": {"employees": rows}})


@api_bp.route("/reports/summary")
@admin_required_api
def reports_summary():
    days_map = {"week": 7, "month": 30, "quarter": 90}
    rng = (request.args.get("range") or "month").lower()
    period_days = days_map.get(rng, 30)

    conn = get_connection()
    try:
        data = analyze_data(conn, period_days=period_days)
    finally:
        conn.close()

    return jsonify({"success": True, "data": data})


@api_bp.route("/notifications")
@login_required_api
def notifications_list():
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, message, type, is_read, created_at FROM notifications
            WHERE user_id = ?
            ORDER BY datetime(created_at) DESC
            LIMIT 50
            """,
            (session["user_id"],),
        ).fetchall()
        unread = conn.execute(
            "SELECT COUNT(*) AS c FROM notifications WHERE user_id = ? AND is_read = 0",
            (session["user_id"],),
        ).fetchone()["c"]
        items = [
            {"id": r["id"], "message": r["message"], "type": r["type"], "is_read": r["is_read"], "created_at": r["created_at"]}
            for r in rows
        ]
    finally:
        conn.close()

    return jsonify({"success": True, "data": {"items": items, "unread_count": unread}})


@api_bp.route("/notifications/read/<int:notif_id>", methods=["POST"])
@login_required_api
def notifications_read(notif_id):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?",
            (notif_id, session["user_id"]),
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"success": True})


@api_bp.route("/dashboard/recent-tasks")
@admin_required_api
def dashboard_recent_tasks():
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT t.id, t.title, t.priority, t.status, t.created_at, u.name AS assignee_name
            FROM tasks t
            LEFT JOIN employees e ON e.id = t.assigned_to
            LEFT JOIN users u ON u.id = e.user_id
            ORDER BY datetime(t.created_at) DESC
            LIMIT 5
            """
        ).fetchall()
        items = [{k: r[k] for k in r.keys()} for r in rows]
    finally:
        conn.close()

    return jsonify({"success": True, "data": {"tasks": items}})


@api_bp.route("/dashboard/burnout-alerts")
@admin_required_api
def dashboard_burnout_alerts():
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT e.id, u.name, e.burnout_risk, e.current_workload, e.max_workload
            FROM employees e JOIN users u ON u.id = e.user_id
            WHERE e.burnout_risk > 0.6
            ORDER BY e.burnout_risk DESC
            """
        ).fetchall()
        items = [{k: r[k] for k in r.keys()} for r in rows]
    finally:
        conn.close()

    return jsonify({"success": True, "data": {"employees": items}})


@api_bp.route("/employee/summary")
@login_required_api
def employee_summary():
    if session.get("user_role") != "employee":
        return jsonify({"success": False, "message": "غير مصرّح"}), 403

    conn = get_connection()
    try:
        emp = conn.execute(
            """
            SELECT e.*, u.name AS emp_name FROM employees e
            JOIN users u ON u.id = e.user_id WHERE e.user_id = ?
            """,
            (session["user_id"],),
        ).fetchone()
        if not emp:
            return jsonify({"success": True, "data": {}})

        eid = emp["id"]
        active = conn.execute(
            """
            SELECT COUNT(*) AS c FROM tasks
            WHERE assigned_to = ? AND status IN ('assigned','in_progress','in_review','analyzing')
            """,
            (eid,),
        ).fetchone()["c"]

        week_done = conn.execute(
            """
            SELECT COUNT(*) AS c FROM tasks
            WHERE assigned_to = ? AND status = 'completed'
              AND datetime(completed_at) >= datetime('now','-7 days')
            """,
            (eid,),
        ).fetchone()["c"]

        urgent = conn.execute(
            """
            SELECT id, title, priority, status, deadline FROM tasks
            WHERE assigned_to = ? AND status NOT IN ('completed','on_hold')
              AND (priority IN ('high','critical') OR date(deadline) <= date('now','+3 days'))
            ORDER BY CASE priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 ELSE 3 END, deadline
            LIMIT 8
            """,
            (eid,),
        ).fetchall()

        activity_rows = conn.execute(
            """
            SELECT title, status, created_at AS ts FROM tasks WHERE assigned_to = ?
            ORDER BY datetime(created_at) DESC LIMIT 5
            """,
            (eid,),
        ).fetchall()

        acts = [{"title": r["title"], "status": r["status"], "ts": r["ts"]} for r in activity_rows]
    finally:
        conn.close()

    return jsonify(
        {
            "success": True,
            "data": {
                "emp_name": emp["emp_name"],
                "performance_score": emp["performance_score"],
                "burnout_risk": emp["burnout_risk"],
                "active_tasks": active,
                "week_completed": week_done,
                "urgent": [{k: row[k] for k in row.keys()} for row in urgent],
                "activity": acts,
            },
        }
    )
