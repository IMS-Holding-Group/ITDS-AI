# مطابقة المهام بالموظفين (منطق توزيع ذكي مبسّط)
import json


def _parse_skills(skills_val):
    if not skills_val:
        return []
    try:
        data = json.loads(skills_val)
        if isinstance(data, list):
            return [str(x).strip() for x in data if str(x).strip()]
    except json.JSONDecodeError:
        pass
    return [s.strip() for s in str(skills_val).split(",") if s.strip()]


def _skill_match_percent(required, emp_skills):
    req = [s.strip() for s in required if s.strip()]
    if not req:
        return 60.0
    emp_set = {s.lower() for s in emp_skills}
    hits = sum(1 for r in req if r.lower() in emp_set)
    return (hits / len(req)) * 100.0


def find_best_match(conn, task_row):
    required = _parse_skills(task_row["required_skills"])
    rows = conn.execute(
        """
        SELECT e.*, u.name AS emp_name
        FROM employees e
        JOIN users u ON u.id = e.user_id
        WHERE e.is_available = 1
        """
    ).fetchall()

    scored = []
    for row in rows:
        emp_skills = _parse_skills(row["skills"])
        sm = _skill_match_percent(required, emp_skills)
        perf = float(row["performance_score"] or 0)
        mx = max(int(row["max_workload"] or 1), 1)
        cur = int(row["current_workload"] or 0)
        availability = (1 - min(1.0, cur / mx)) * 100.0
        spd = float(row["speed_score"] or 0)
        total = sm * 0.40 + perf * 0.30 + availability * 0.20 + spd * 0.10

        reasons = []
        reasons.append(f"تطابق المهارات {sm:.1f}%")
        reasons.append(f"أداء {perf:.1f}")
        reasons.append(f"توفر حمل {availability:.1f}%")
        reasons.append(f"سرعة {spd:.1f}")

        scored.append(
            {
                "employee_id": row["id"],
                "name": row["emp_name"],
                "department": row["department"],
                "score": round(total, 2),
                "skill_match": round(sm, 2),
                "reason": " — ".join(reasons),
            }
        )

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:3]
