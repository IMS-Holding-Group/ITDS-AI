# نموذج المهمة


class Task:
    def __init__(
        self,
        task_id,
        title,
        description,
        priority,
        status,
        required_skills,
        deadline,
        estimated_hours,
        actual_hours,
        assigned_to,
        created_by,
        ai_match_score,
        ai_notes,
        created_at,
        assigned_at,
        completed_at,
        assignee_name=None,
    ):
        self.id = task_id
        self.title = title
        self.description = description or ""
        self.priority = priority
        self.status = status
        self.required_skills = required_skills
        self.deadline = deadline
        self.estimated_hours = estimated_hours
        self.actual_hours = actual_hours
        self.assigned_to = assigned_to
        self.created_by = created_by
        self.ai_match_score = ai_match_score
        self.ai_notes = ai_notes
        self.created_at = created_at
        self.assigned_at = assigned_at
        self.completed_at = completed_at
        self.assignee_name = assignee_name

    @staticmethod
    def from_row(row, assignee_name=None):
        if row is None:
            return None
        return Task(
            row["id"],
            row["title"],
            row["description"],
            row["priority"],
            row["status"],
            row["required_skills"],
            row["deadline"],
            row["estimated_hours"],
            row["actual_hours"],
            row["assigned_to"],
            row["created_by"],
            row["ai_match_score"],
            row["ai_notes"],
            row["created_at"],
            row["assigned_at"],
            row["completed_at"],
            assignee_name,
        )
