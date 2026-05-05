# تحليل أداء الفريق والمهام لاستخدام التقارير وواجهات API
from datetime import datetime, timedelta


def _daterange_days(days):
    end = datetime.utcnow().date()
    start = end - timedelta(days=days)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def analyze_data(conn, period_days=30):
    start_d, end_d = _daterange_days(period_days)

    per_employee = conn.execute(
        """
        SELECT u.name AS name,
               AVG(pl.score) AS avg_score,
               SUM(CASE WHEN pl.on_time = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(pl.id) AS on_time_rate
        FROM performance_logs pl
        JOIN employees e ON e.id = pl.employee_id
        JOIN users u ON u.id = e.user_id
        WHERE date(pl.logged_at) BETWEEN date(?) AND date(?)
        GROUP BY e.id
        """,
        (start_d, end_d),
    ).fetchall()

    team_on_time = conn.execute(
        """
        SELECT SUM(CASE WHEN on_time = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(id) AS r
        FROM performance_logs
        WHERE date(logged_at) BETWEEN date(?) AND date(?)
        """,
        (start_d, end_d),
    ).fetchone()
    on_time_rate = float(team_on_time["r"] or 0) if team_on_time and team_on_time["r"] is not None else 0.0

    priority_dist = conn.execute(
        """
        SELECT priority, COUNT(*) AS c FROM tasks
        WHERE date(created_at) BETWEEN date(?) AND date(?)
        GROUP BY priority
        """,
        (start_d, end_d),
    ).fetchall()

    status_dist = conn.execute(
        """
        SELECT status, COUNT(*) AS c FROM tasks
        WHERE date(created_at) BETWEEN date(?) AND date(?)
        GROUP BY status
        """,
        (start_d, end_d),
    ).fetchall()

    burnout_rows = conn.execute(
        """
        SELECT e.id AS employee_id, u.name AS name, e.burnout_risk AS burnout_risk
        FROM employees e
        JOIN users u ON u.id = e.user_id
        """
    ).fetchall()
    burnout_report = []
    for r in burnout_rows:
        risk = float(r["burnout_risk"] or 0)
        if risk > 0.6:
            lk, lv = "danger", "خطر"
        elif risk > 0.3:
            lk, lv = "warn", "تحذير"
        else:
            lk, lv = "safe", "آمن"
        burnout_report.append(
            {"employee_id": r["employee_id"], "name": r["name"], "burnout_risk": round(risk, 3), "level": lv, "level_key": lk}
        )

    completed_series = conn.execute(
        """
        SELECT date(completed_at) AS d, COUNT(*) AS c
        FROM tasks
        WHERE status = 'completed' AND completed_at IS NOT NULL
          AND date(completed_at) BETWEEN date(?) AND date(?)
        GROUP BY date(completed_at)
        ORDER BY d
        """,
        (start_d, end_d),
    ).fetchall()

    return {
        "period_days": period_days,
        "employee_performance": [
            {"name": r["name"], "avg_score": round(float(r["avg_score"] or 0), 2), "on_time_rate": round(float(r["on_time_rate"] or 0), 3)}
            for r in per_employee
        ],
        "team_on_time_rate": round(on_time_rate, 3),
        "tasks_by_priority": {r["priority"]: r["c"] for r in priority_dist},
        "tasks_by_status": {r["status"]: r["c"] for r in status_dist},
        "burnout_report": burnout_report,
        "completed_per_day": [{"date": r["d"], "count": r["c"]} for r in completed_series],
    }
