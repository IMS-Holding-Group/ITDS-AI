# إنشاء قاعدة البيانات وتهيئتها مع البيانات الافتراضية
import hashlib
import json
import secrets
import sqlite3
from datetime import datetime, timedelta

from config import DATABASE_PATH


def hash_password(plain: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.sha256((salt + plain).encode("utf-8")).hexdigest()
    return f"{salt}:{digest}"


def verify_password(stored: str, plain: str) -> bool:
    if ":" not in stored:
        return False
    salt, digest = stored.split(":", 1)
    return hashlib.sha256((salt + plain).encode("utf-8")).hexdigest() == digest


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            email      TEXT UNIQUE NOT NULL,
            password   TEXT NOT NULL,
            role       TEXT NOT NULL CHECK(role IN ('admin', 'employee')),
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS employees (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id           INTEGER UNIQUE REFERENCES users(id),
            department        TEXT NOT NULL,
            skills            TEXT NOT NULL,
            performance_score REAL DEFAULT 75.0,
            speed_score       REAL DEFAULT 70.0,
            current_workload  INTEGER DEFAULT 0,
            max_workload      INTEGER DEFAULT 5,
            total_tasks_done  INTEGER DEFAULT 0,
            burnout_risk      REAL DEFAULT 0.0,
            is_available      INTEGER DEFAULT 1,
            joined_at         TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            title           TEXT NOT NULL,
            description     TEXT,
            priority        TEXT DEFAULT 'medium' CHECK(priority IN ('low','medium','high','critical')),
            status          TEXT DEFAULT 'new' CHECK(status IN ('new','analyzing','assigned','in_progress','in_review','completed','on_hold')),
            required_skills TEXT,
            deadline        TEXT,
            estimated_hours REAL DEFAULT 4.0,
            actual_hours    REAL,
            assigned_to     INTEGER REFERENCES employees(id),
            created_by      INTEGER REFERENCES users(id),
            ai_match_score  REAL,
            ai_notes        TEXT,
            created_at      TEXT DEFAULT (datetime('now')),
            assigned_at     TEXT,
            completed_at    TEXT
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER REFERENCES users(id),
            message    TEXT NOT NULL,
            type       TEXT DEFAULT 'info' CHECK(type IN ('info','success','warning','danger')),
            is_read    INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS performance_logs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id     INTEGER REFERENCES employees(id),
            task_id         INTEGER REFERENCES tasks(id),
            score           REAL,
            completion_time REAL,
            on_time         INTEGER DEFAULT 1,
            logged_at       TEXT DEFAULT (datetime('now'))
        );
        """
    )
    conn.commit()


def seed_if_empty(conn: sqlite3.Connection) -> None:
    cur = conn.execute("SELECT COUNT(*) AS c FROM users")
    if cur.fetchone()["c"] > 0:
        return

    admins = [
        {"name": "أحمد العمري", "email": "ahmed@itds.com", "password": ""},
        {"name": "سارة الزهراني", "email": "sara@itds.com", "password": ""},
        {"name": "خالد المالكي", "email": "khaled@itds.com", "password": ""},
    ]

    employees_seed = [
        {"name": "محمد السالم", "email": "m.salem@itds.com", "department": "تطوير البرمجيات", "skills": ["Python", "Flask", "SQL", "REST API"], "performance_score": 88.5, "speed_score": 82.0},
        {"name": "نورة القحطاني", "email": "n.qahtani@itds.com", "department": "تطوير البرمجيات", "skills": ["JavaScript", "HTML", "CSS", "Vue"], "performance_score": 91.0, "speed_score": 88.0},
        {"name": "فيصل الدوسري", "email": "f.dosari@itds.com", "department": "تحليل البيانات", "skills": ["Python", "Data Analysis", "Excel", "Power BI"], "performance_score": 79.0, "speed_score": 75.0},
        {"name": "رنا العتيبي", "email": "r.otaibi@itds.com", "department": "تصميم", "skills": ["UI/UX", "Figma", "CSS", "Adobe XD"], "performance_score": 93.0, "speed_score": 90.0},
        {"name": "عبدالله الشهري", "email": "a.shahri@itds.com", "department": "تطوير البرمجيات", "skills": ["Java", "Spring Boot", "SQL", "Docker"], "performance_score": 85.0, "speed_score": 80.0},
        {"name": "هند الغامدي", "email": "h.ghamdi@itds.com", "department": "إدارة المشاريع", "skills": ["Project Management", "Jira", "Agile", "Scrum"], "performance_score": 87.5, "speed_score": 85.0},
        {"name": "سلطان الحربي", "email": "s.harbi@itds.com", "department": "تحليل البيانات", "skills": ["SQL", "Python", "Machine Learning", "التقارير"], "performance_score": 76.0, "speed_score": 70.0},
        {"name": "مريم النهدي", "email": "m.nahdi@itds.com", "department": "تطوير البرمجيات", "skills": ["Python", "Django", "PostgreSQL", "Redis"], "performance_score": 89.0, "speed_score": 86.0},
        {"name": "يوسف الزبيدي", "email": "y.zubaidi@itds.com", "department": "تصميم", "skills": ["Graphic Design", "Illustrator", "Photoshop", "Branding"], "performance_score": 82.0, "speed_score": 78.0},
        {"name": "لمياء السبيعي", "email": "l.subai@itds.com", "department": "تطوير البرمجيات", "skills": ["React", "Node.js", "MongoDB", "TypeScript"], "performance_score": 94.0, "speed_score": 91.0},
        {"name": "ماجد الثقفي", "email": "maj.thaqafi@itds.com", "department": "إدارة المشاريع", "skills": ["Risk Management", "Budget", "Agile", "PMP"], "performance_score": 71.0, "speed_score": 68.0, "burnout_risk": 0.72, "current_workload": 5},
        {"name": "دانا الرشيدي", "email": "d.rashidi@itds.com", "department": "تحليل البيانات", "skills": ["Tableau", "Power BI", "Excel", "SQL"], "performance_score": 86.0, "speed_score": 83.0},
    ]

    tasks_seed = [
        {"title": "تطوير واجهة تسجيل الدخول", "priority": "high", "status": "completed", "required_skills": ["HTML", "CSS", "JavaScript"], "estimated_hours": 8, "actual_hours": 7.5, "assigned_to_email": "n.qahtani@itds.com"},
        {"title": "تصميم قاعدة بيانات العملاء", "priority": "critical", "status": "completed", "required_skills": ["SQL", "Data Analysis"], "estimated_hours": 12, "actual_hours": 11.0, "assigned_to_email": "f.dosari@itds.com"},
        {"title": "بناء API مصادقة المستخدمين", "priority": "high", "status": "in_progress", "required_skills": ["Python", "Flask", "SQL"], "estimated_hours": 16, "assigned_to_email": "m.salem@itds.com"},
        {"title": "لوحة تقارير الأداء التفاعلية", "priority": "medium", "status": "in_progress", "required_skills": ["JavaScript", "CSS", "SQL"], "estimated_hours": 20, "assigned_to_email": "n.qahtani@itds.com"},
        {"title": "تصميم هوية الشركة الجديدة", "priority": "medium", "status": "in_review", "required_skills": ["Graphic Design", "Figma"], "estimated_hours": 24, "actual_hours": 26.0, "assigned_to_email": "y.zubaidi@itds.com"},
        {"title": "تحليل بيانات المبيعات الربع سنوية", "priority": "high", "status": "completed", "required_skills": ["Python", "Data Analysis"], "estimated_hours": 10, "actual_hours": 9.0, "assigned_to_email": "s.harbi@itds.com"},
        {"title": "إصلاح ثغرات الأمان في النظام", "priority": "critical", "status": "assigned", "required_skills": ["Python", "SQL"], "estimated_hours": 6, "assigned_to_email": "m.nahdi@itds.com"},
        {"title": "تطوير تطبيق موبايل للموظفين", "priority": "medium", "status": "on_hold", "required_skills": ["React", "TypeScript"], "estimated_hours": 40},
        {"title": "إعداد خادم الإنتاج", "priority": "high", "status": "completed", "required_skills": ["Docker", "Linux"], "estimated_hours": 8, "actual_hours": 10.0, "assigned_to_email": "a.shahri@itds.com"},
        {"title": "كتابة وثائق API الشاملة", "priority": "low", "status": "completed", "required_skills": ["Technical Writing", "REST API"], "estimated_hours": 12, "actual_hours": 12.5, "assigned_to_email": "h.ghamdi@itds.com"},
        {"title": "خوارزمية التوصية الذكية", "priority": "critical", "status": "in_progress", "required_skills": ["Python", "Machine Learning"], "estimated_hours": 32, "assigned_to_email": "s.harbi@itds.com"},
        {"title": "إعادة تصميم صفحة الرئيسية", "priority": "medium", "status": "assigned", "required_skills": ["UI/UX", "CSS", "HTML"], "estimated_hours": 16, "assigned_to_email": "r.otaibi@itds.com"},
        {"title": "ربط نظام الدفع الإلكتروني", "priority": "critical", "status": "in_review", "required_skills": ["Python", "REST API", "SQL"], "estimated_hours": 20, "actual_hours": 22.0, "assigned_to_email": "m.nahdi@itds.com"},
        {"title": "تقرير الإرهاق الوظيفي الشهري", "priority": "medium", "status": "in_review", "required_skills": ["Data Analysis", "Tableau"], "estimated_hours": 8, "actual_hours": 7.0, "assigned_to_email": "d.rashidi@itds.com"},
        {"title": "إضافة ميزة الإشعارات الفورية", "priority": "medium", "status": "assigned", "required_skills": ["JavaScript", "Python"], "estimated_hours": 12, "assigned_to_email": "m.salem@itds.com"},
        {"title": "مراجعة أمان كلمات المرور", "priority": "high", "status": "new", "required_skills": ["Python", "Security"], "estimated_hours": 6},
        {"title": "تحسين أداء قاعدة البيانات", "priority": "high", "status": "analyzing", "required_skills": ["SQL", "PostgreSQL"], "estimated_hours": 10},
        {"title": "واجهة تصدير التقارير لـ PDF", "priority": "low", "status": "new", "required_skills": ["Python", "HTML", "CSS"], "estimated_hours": 8},
        {"title": "خطة مشروع التوسع Q2", "priority": "medium", "status": "completed", "required_skills": ["Project Management", "Agile"], "estimated_hours": 16, "actual_hours": 15.0, "assigned_to_email": "h.ghamdi@itds.com"},
        {"title": "لوحة مقارنة أداء الأقسام", "priority": "medium", "status": "on_hold", "required_skills": ["Power BI", "Data Analysis"], "estimated_hours": 14},
    ]

    admin_ids = []
    for a in admins:
        conn.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            (a["name"], a["email"], hash_password(a["password"]), "admin"),
        )
        admin_ids.append(conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"])

    creator_id = admin_ids[0]
    email_to_employee_id = {}

    for row in employees_seed:
        skills_json = json.dumps(row["skills"], ensure_ascii=False)
        conn.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            (row["name"], row["email"], hash_password(""), "employee"),
        )
        uid = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
        burnout = row.get("burnout_risk", 0.0)
        cw = row.get("current_workload", 0)
        conn.execute(
            """
            INSERT INTO employees (user_id, department, skills, performance_score, speed_score,
                current_workload, burnout_risk)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (uid, row["department"], skills_json, row["performance_score"], row["speed_score"], cw, burnout),
        )
        eid = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
        email_to_employee_id[row["email"]] = eid

    now = datetime.utcnow()
    day_offsets = [35, 30, 28, 25, 22, 20, 18, 15, 12, 10, 8, 6, 5, 4, 3, 2, 1, 0, 2, 5]

    for idx, t in enumerate(tasks_seed):
        assigned_to = None
        em = t.get("assigned_to_email")
        if em:
            assigned_to = email_to_employee_id.get(em)

        deadline = (now + timedelta(days=7 + idx)).strftime("%Y-%m-%d")
        created_at = (now - timedelta(days=abs(day_offsets[idx % len(day_offsets)]))).strftime("%Y-%m-%d %H:%M:%S")
        status = t["status"]
        assigned_at = None
        completed_at = None
        if assigned_to and status not in ("new", "analyzing"):
            assigned_at = created_at
        if status == "completed":
            completed_at = (now - timedelta(days=max(0, 10 - idx))).strftime("%Y-%m-%d %H:%M:%S")

        req_skills = json.dumps(t["required_skills"], ensure_ascii=False)

        conn.execute(
            """
            INSERT INTO tasks (title, description, priority, status, required_skills, deadline,
                estimated_hours, actual_hours, assigned_to, created_by, assigned_at, completed_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                t["title"],
                "",
                t["priority"],
                status,
                req_skills,
                deadline,
                float(t["estimated_hours"]),
                t.get("actual_hours"),
                assigned_to,
                creator_id,
                assigned_at,
                completed_at,
                created_at,
            ),
        )

        tid = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]

        if status == "completed" and assigned_to is not None and t.get("actual_hours") is not None:
            est = float(t["estimated_hours"])
            act = float(t["actual_hours"])
            on_time = 1 if act <= est * 1.2 else 0
            score = min(100.0, 70.0 + (est / max(act, 0.1)) * 15.0)
            conn.execute(
                """
                INSERT INTO performance_logs (employee_id, task_id, score, completion_time, on_time, logged_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (assigned_to, tid, score, act, on_time, completed_at or created_at),
            )

    conn.execute(
        """
        UPDATE employees SET current_workload = (
            SELECT COUNT(*) FROM tasks
            WHERE tasks.assigned_to = employees.id AND tasks.status IN ('assigned','in_progress','in_review','analyzing')
        )
        """
    )

    rows = conn.execute(
        "SELECT assigned_to FROM tasks WHERE status = ? AND assigned_to IS NOT NULL", ("completed",)
    ).fetchall()
    counts = {}
    for r in rows:
        eid = r["assigned_to"]
        counts[eid] = counts.get(eid, 0) + 1
    for eid, c in counts.items():
        conn.execute("UPDATE employees SET total_tasks_done = ? WHERE id = ?", (c, eid))

    for adm in admin_ids:
        conn.execute(
            "INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)",
            (
                adm,
                "تنبيه: يوجد موظفون بحالة خطر إرهاق وظيفي مرتفع. راجع صفحة التقارير واللوحة الرئيسية.",
                "warning",
            ),
        )

    conn.commit()


def sync_employee_workloads(conn):
    conn.execute(
        """
        UPDATE employees SET current_workload = (
            SELECT COUNT(*) FROM tasks
            WHERE tasks.assigned_to = employees.id AND tasks.status IN ('assigned','in_progress','in_review','analyzing')
        )
        """
    )


def init_database():
    conn = get_connection()
    try:
        init_tables(conn)
        seed_if_empty(conn)
    finally:
        conn.close()

    conn = get_connection()
    try:
        from ai_engine.burnout_detector import detect_burnout

        detect_burnout(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    init_database()
    print("تم تهيئة قاعدة البيانات.")
