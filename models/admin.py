# نموذج المدير — تمثيل الحساب الإداري


class AdminProfile:
    def __init__(self, user_id, name, email, created_at=None):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.created_at = created_at

    @staticmethod
    def from_row(row):
        if row is None:
            return None
        return AdminProfile(row["id"], row["name"], row["email"], row["created_at"])
