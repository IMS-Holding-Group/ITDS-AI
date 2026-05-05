# كشف مخاطر الإرهاق الوظيفي وتحديث قاعدة البيانات
from datetime import datetime, timedelta


def _last_three_completed_tasks(conn, employee_id):
    rows = conn.execute(
        """
        SELECT actual_hours, estimated_hours FROM tasks
        WHERE assigned_to = ? AND status = 'completed' AND actual_hours IS NOT NULL
        ORDER BY datetime(completed_at) DESC
        LIMIT 3
        """,
        (employee_id,),
    ).fetchall()
    return rows


def _overtime_factor(rows):
    if not rows:
        return 0.0
    bad = 0
    for r in rows:
        est = float(r["estimated_hours"] or 1)
        act = float(r["actual_hours"] or 0)
        if act > est * 1.2:
            bad += 1
    return 1.0 if bad > 0 else 0.0


def _performance_drop_factor(conn, employee_id):
    since = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    logs = conn.execute(
        """
        SELECT score, logged_at FROM performance_logs
        WHERE employee_id = ? AND datetime(logged_at) >= datetime(?)
        ORDER BY datetime(logged_at) ASC
        """,
        (employee_id, since),
    ).fetchall()
    if len(logs) < 2:
        return 0.0
    first = float(logs[0]["score"] or 0)
    last = float(logs[-1]["score"] or 0)
    return 1.0 if (first - last) > 10 else 0.0


def detect_burnout(conn):
    employees = conn.execute(
        """
        SELECT e.id, e.current_workload, e.max_workload, u.name
        FROM employees e
        JOIN users u ON u.id = e.user_id
        """
    ).fetchall()

    results = []
    admins = conn.execute("SELECT id FROM users WHERE role = 'admin'").fetchall()
    admin_ids = [r["id"] for r in admins]

    for emp in employees:
        mx = max(int(emp["max_workload"] or 1), 1)
        ratio = min(1.0, int(emp["current_workload"] or 0) / mx)
        ot = _overtime_factor(_last_three_completed_tasks(conn, emp["id"]))
        pd = _performance_drop_factor(conn, emp["id"])
        risk = ratio * 0.50 + ot * 0.30 + pd * 0.20
        risk = max(0.0, min(1.0, risk))

        conn.execute("UPDATE employees SET burnout_risk = ? WHERE id = ?", (risk, emp["id"]))

        level = "آمن"
        level_key = "safe"
        if risk > 0.6:
            level = "خطر"
            level_key = "danger"
            alert_msg = f"تنبيه إرهاق وظيفي عالٍ للموظف {emp['name']} (المخاطر {risk:.2f})"
            for aid in admin_ids:
                dup = conn.execute(
                    """
                    SELECT 1 FROM notifications
                    WHERE user_id = ? AND message = ? AND datetime(created_at) > datetime('now','-12 hours')
                    LIMIT 1
                    """,
                    (aid, alert_msg),
                ).fetchone()
                if not dup:
                    conn.execute(
                        "INSERT INTO notifications (user_id, message, type) VALUES (?, ?, 'danger')",
                        (aid, alert_msg),
                    )
        elif risk > 0.3:
            level = "تحذير"
            level_key = "warn"

        results.append(
            {
                "employee_id": emp["id"],
                "name": emp["name"],
                "burnout_risk": round(risk, 3),
                "level": level,
                "level_key": level_key,
            }
        )

    conn.commit()
    return results
