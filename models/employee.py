# نموذج الموظف وربطه بجدول المستخدمين


class Employee:
    def __init__(
        self,
        emp_id,
        user_id,
        name,
        email,
        department,
        skills,
        performance_score,
        speed_score,
        current_workload,
        max_workload,
        total_tasks_done,
        burnout_risk,
        is_available,
        joined_at=None,
    ):
        self.id = emp_id
        self.user_id = user_id
        self.name = name
        self.email = email
        self.department = department
        self.skills = skills
        self.performance_score = performance_score
        self.speed_score = speed_score
        self.current_workload = current_workload
        self.max_workload = max_workload
        self.total_tasks_done = total_tasks_done
        self.burnout_risk = burnout_risk
        self.is_available = bool(is_available)
        self.joined_at = joined_at

    @staticmethod
    def from_join_row(row):
        if row is None:
            return None
        return Employee(
            row["id"],
            row["user_id"],
            row["name"],
            row["email"],
            row["department"],
            row["skills"],
            row["performance_score"],
            row["speed_score"],
            row["current_workload"],
            row["max_workload"],
            row["total_tasks_done"],
            row["burnout_risk"],
            row["is_available"],
            row["joined_at"],
        )

    def workload_ratio(self):
        if self.max_workload <= 0:
            return 0.0
        return min(1.0, self.current_workload / self.max_workload)
