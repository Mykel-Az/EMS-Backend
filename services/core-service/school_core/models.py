from django.db import models
from django.conf import settings
from django.contrib.auth.models import Group
from .manager import TenantScopedModel
# Create your models here.

class School(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    school_code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, null=True)

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='school_logos/', blank=True, null=True)
    cover_image = models.ImageField(upload_to='school_covers/', blank=True, null=True)

    country = models.CharField(max_length=100, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class SchoolSettings(models.Model):
    school = models.OneToOneField(School, on_delete=models.CASCADE, related_name='settings')    
    timezone = models.CharField(max_length=50, default='UTC')
    currency = models.CharField(max_length=10, default='NGN')
    date_format = models.CharField(max_length=20, default='YYYY-MM-DD')
    term_per_session = models.PositiveSmallIntegerField(choices=[(2, "Semester (2 per session)"), (3, "Term (3 per sesion)")], default=3)


class Campus(TenantScopedModel):
    name = models.CharField(max_length=255)
    state = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField()

    def __str__(self):
        return self.name
    

class Division(TenantScopedModel):
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)


class Role(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Position(TenantScopedModel):
    """ Represents a position or job title within the school, e.g., Principal, Teacher, Administrator """
    name = models.CharField(max_length=255)
    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    inherits_from = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='inherited_positions')

    def __str__(self):
        return self.name


class AcademicSession(TenantScopedModel):
    name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.name


class Term(TenantScopedModel):
    academic_session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name='terms')
    name = models.CharField(max_length=50)
    sequence = models.PositiveSmallIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        unique_together = ('academic_session', 'sequence')
        ordering = ['academic_session', 'sequence']

    def __str__(self):
        return f"{self.academic_session.name} - {self.name}"




class Staff(TenantScopedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='staff_profile')
    position = models.ForeignKey(Position, on_delete=models.PROTECT, related_name='staff')
    hire_date = models.DateField(null=True, blank=True)
    employment_type = models.CharField(max_length=20, choices=[("full_time", "Full-time"), ("part_time", "Part-time")], default="full_time")
    extra_attributes = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return self.user.get_full_name()


class TeacherDetails(TenantScopedModel):
    staff = models.OneToOneField(Staff, on_delete=models.CASCADE, related_name='teacher')
    subject_taught = models.ManyToManyField('subject', blank=True)


class Student(TenantScopedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    admission_number = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.user.get_full_name()

    @property
    def current_class_arm(self):
        return self.class_arms.first()

    @property
    def core_subjects(self):
        arm = self.current_class_arm
        if not arm:
            return subject.objects.none()
        return subject.objects.filter(class_level=arm.class_level, term=... )  # current term, see below
    

class Class(TenantScopedModel):
    """ class or grade level, e.g. SS1, SS2 or Grade 1, Grade 2 """
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class ClassArm(TenantScopedModel):
    """Class arm/section, e.g. SS1A, SS1B."""
    class_level = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='arms')
    name = models.CharField(max_length=255)
    teacher = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, blank=True, related_name='arm_teacher')
    students = models.ManyToManyField(Student, blank=True, related_name='arm_students')

    class Meta:
        unique_together = ('class_level', 'name')

    def __str__(self):
        return f"{self.class_level} - {self.name}"
    

class subject(TenantScopedModel):
    name = models.CharField(max_length=255)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='subjects')
    class_level = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='subjects')
    class_arm = models.ForeignKey(ClassArm, on_delete=models.CASCADE, related_name='subjects', null=True, blank=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('name', 'term', 'class_level', 'class_arm')

    def __str__(self):
        return self.name


class SubjectClassArmAssignment(TenantScopedModel):
    subject = models.ForeignKey(subject, on_delete=models.CASCADE, related_name='arm_assignments')
    class_arm = models.ForeignKey(ClassArm, on_delete=models.CASCADE, related_name='subject_assignments')

    class Meta:
        unique_together = ('subject', 'class_arm')

    def __str__(self):
        return f"{self.subject} - {self.class_arm}"


class AssignmentTeacher(TenantScopedModel):
    """One teacher's involvement in a subject/arm assignment — supports
    multiple concurrent teachers (co-teaching, split topics) and tracks
    who is currently active vs. historical (substitutions)."""
    assignment = models.ForeignKey(SubjectClassArmAssignment, on_delete=models.CASCADE, related_name='teacher_assignments')
    teacher = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='teaching_assignments')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)  # null = still active
    reason = models.CharField(
        max_length=20,
        choices=[("primary", "Primary"), ("co_teacher", "Co-teacher"), ("substitute", "Substitute")],
        default="primary",
    )

    def __str__(self):
        status = "active" if self.end_date is None else f"ended {self.end_date}"
        return f"{self.teacher} on {self.assignment} ({self.reason}, {status})"
    

class Schedule(TenantScopedModel):
    assignment = models.ForeignKey(SubjectClassArmAssignment, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.CharField(max_length=10, choices=[
        ("mon", "Monday"), ("tue", "Tuesday"), ("wed", "Wednesday"),
        ("thu", "Thursday"), ("fri", "Friday"),
    ])
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.assignment} - {self.day_of_week} {self.start_time}-{self.end_time}"


class Attendance(TenantScopedModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    class_arm = models.ForeignKey(ClassArm, on_delete=models.CASCADE, related_name='attendance_records')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=[("present", "Present"), ("absent", "Absent"), ("indisposed", "Indisposed")])

    class Meta:
        unique_together = ('student', 'date')  # one attendance entry per student per day

    def __str__(self):
        return f"{self.student} - {self.date} - {self.status}"


class Grade(TenantScopedModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grades')
    subject = models.ForeignKey(subject, on_delete=models.CASCADE, related_name='grades')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='grades')
    score = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=5)


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    graded_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_given')

    class Meta:
        unique_together = ('student', 'subject', 'term')

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.term} - {self.grade}"



# class Schedule(TenantScopedModel):
#     class_name = models.ForeignKey(Class, on_delete=models.CASCADE)
#     subject = models.ForeignKey(subject, on_delete=models.CASCADE)
#     start_time = models.TimeField()
#     end_time = models.TimeField()

#     def __str__(self):
#         return f"{self.class_name} - {self.subject} - {self.start_time} to {self.end_time}"


# class Exam(TenantScopedModel):
#     name = models.CharField(max_length=255)
#     subject = models.ForeignKey(subject, on_delete=models.CASCADE)
#     date = models.DateField()

#     def __str__(self):
#         return f"{self.name} - {self.subject} - {self.date}"


# class ExamResult(TenantScopedModel):
#     exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
#     student = models.ForeignKey(Student, on_delete=models.CASCADE)
#     grade = models.CharField(max_length=5)

#     def __str__(self):
#         return f"{self.exam} - {self.student} - {self.grade}"








# class Announcement(TenantScopedModel):
#     title = models.CharField(max_length=255)
#     content = models.TextField()
#     date_posted = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.title


# class Event(TenantScopedModel):
    # name = models.CharField(max_length=255)
    # description = models.TextField()
    # date = models.DateField()

    # def __str__(self):
    #     return self.name