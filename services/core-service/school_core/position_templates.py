
POSITION_PERMISSION_TEMPLATES = {
    "Teacher": ["view_student", "add_attendance", "add_grade"],
    "Principal": ["view_student", "add_attendance", "add_grade", "approve_results", "manage_teachers"],
    "IT Officer": ["manage_users", "reset_passwords"],
}