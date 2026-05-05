# نموذج المستخدم الأساسي (تعريف مشترك للمدير والموظف)
from abc import ABC, abstractmethod


class User(ABC):
    def __init__(self, user_id, name, email, role, created_at=None):
        self.id = user_id
        self.name = name
        self.email = email
        self.role = role
        self.created_at = created_at

    @staticmethod
    def from_row(row):
        if row is None:
            return None
        role = row["role"]
        if role == "admin":
            return Admin(row["id"], row["name"], row["email"], row["created_at"])
        return EmployeeUser(row["id"], row["name"], row["email"], row["created_at"])

    @abstractmethod
    def dashboard_path(self):
        pass


class EmployeeUser(User):
    def __init__(self, user_id, name, email, created_at=None):
        super().__init__(user_id, name, email, "employee", created_at)

    def dashboard_path(self):
        return "/employee/dashboard"


class Admin(User):
    def __init__(self, user_id, name, email, created_at=None):
        super().__init__(user_id, name, email, "admin", created_at)

    def dashboard_path(self):
        return "/admin/dashboard"
