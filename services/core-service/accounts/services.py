# accounts/services.py
from django.db import transaction
from accounts.models import CustomUser
from school_core.models import Staff, Student, Teacher
from school_core.provisioning import assign_position


@transaction.atomic
def create_school_user(school, email, password, first_name, last_name, role, position=None, **extra):
    user = CustomUser.objects.create_user(
        email=email, password=password,
        first_name=first_name, last_name=last_name,
        school=school, role=role, position=position,
    )
    if position:
        assign_position(user, position)  # Group membership + inheritance chain
    return user


@transaction.atomic
def create_staff(school, position, email, password, first_name, last_name,
                  hire_date=None, employment_type="full_time",
                  extra_attributes=None, subjects_taught=None, **user_kwargs):
    staff_role = Role.objects.get(school=school, name="Staff")  # or however Role is resolved

    user = create_school_user(
        school=school, email=email, password=password,
        first_name=first_name, last_name=last_name,
        role=staff_role, position=position, **user_kwargs,
    )

    staff = Staff.objects.create(
        user=user, school=school, position=position,
        hire_date=hire_date, employment_type=employment_type,
        extra_attributes=extra_attributes or {},
    )

    # Only well-known teaching positions get the extension table
    if position.name == "Teacher" and subjects_taught:
        details = Teacher.objects.create(staff=staff)
        details.subjects_taught.set(subjects_taught)

    return staff


@transaction.atomic
def create_student(school, admission_number, email, password, first_name, last_name, **user_kwargs):
    student_role = Role.objects.get(school=school, name="Student")

    user = create_school_user(
        school=school, email=email, password=password,
        first_name=first_name, last_name=last_name,
        role=student_role, **user_kwargs,
    )

    return Student.objects.create(user=user, school=school, admission_number=admission_number)