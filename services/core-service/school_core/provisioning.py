from datetime import timedelta

from django.contrib.auth.models import Group, Permission
from .models import Position, AcademicSession, Term
from .position_templates import POSITION_PERMISSION_TEMPLATES
from django.db import transaction


def create_position(school, name, inherits_from=None, extra_permission_codenames=None):
    group = Group.objects.create(name=f"{school.slug}-{name.lower().replace(' ', '-')}")

    codenames = POSITION_PERMISSION_TEMPLATES.get(name, [])
    if extra_permission_codenames:
        codenames = list(codenames) + list(extra_permission_codenames)

    if codenames:
        perms = Permission.objects.filter(codename__in=codenames)
        group.permissions.set(perms)

    return Position.objects.create(
        school=school, name=name, group=group, inherits_from=inherits_from
    )


def assign_position(user, position):
    """Adds the user to this Position's Group and every Group in its
    inheritance chain — composition, not copying."""
    user.position = position
    user.save(update_fields=['position'])

    current = position
    seen = set()
    while current and current.id not in seen:
        seen.add(current.id)
        user.groups.add(current.group)
        current = current.inherits_from


DEFAULT_TERM_NAMES = {
    2: ["Semester 1", "Semester 2"],
    3: ["First Term", "Second Term", "Third Term"],
}


@transaction.atomic
def create_academic_session(school, name, start_date, end_date):
    """
    Creates an AcademicSession and auto-generates its Terms based on
    school.settings.terms_per_session (2 or 3), splitting the session's
    date range evenly across them.
    """

    session = AcademicSession.objects.create(
        school=school, name=name, start_date=start_date, end_date=end_date
    )

    terms_per_session = school.settings.term_per_session
    term_names = DEFAULT_TERM_NAMES[terms_per_session]

    total_days = (end_date - start_date).days + 1
    days_per_term = total_days // terms_per_session

    for i, term_name in enumerate(term_names):
        term_start = start_date + timedelta(days=i * days_per_term)
        if i == terms_per_session - 1:
            term_end = end_date
        else:
            term_end = start_date + timedelta(days=days_per_term * (i + 1) - 1)

        Term.objects.create(
            school=school,
            academic_session=session,
            name=term_name,
            sequence=i + 1,
            start_date=term_start,
            end_date=term_end,
        )

    return session