from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.conf import settings, Settings

ENGLISH_LEVELS = [
    ('Beginner', 'Beginner'),
    ('Elementary', 'Elementary'),
    ('Intermediate', 'Intermediate'),
    ('Upper Intermediate', 'Upper Intermediate'),
    ('Advanced', 'Advanced'),
]

USER_TYPE_CHOICES = [
    ('student', 'Student'),
    ('teacher', 'Teacher'),
]


class CustomUser(AbstractUser):
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    level = models.CharField(max_length=30, choices=ENGLISH_LEVELS, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.png', blank=True)
    rating = models.FloatField(default=0.0)

    def is_student(self):
        return self.user_type == 'student'

    def is_teacher(self):
        return self.user_type == 'teacher'


User = get_user_model()


class PlacementTestReservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations_made')
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    level = models.CharField(max_length=20, choices=ENGLISH_LEVELS)
    date = models.DateField()
    time = models.TimeField()
    assigned_teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations_assigned')
    is_seen = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.full_name} - {self.date} {self.time}"


class Course(models.Model):
    LEVEL_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Elementary', 'Elementary'),
        ('Intermediate', 'Intermediate'),
        ('Upper Intermediate', 'Upper Intermediate'),
        ('Advanced', 'Advanced'),
    ]

    DAYS_CHOICES = [
        ('Monday-Wednesday', 'Monday-Wednesday'),
        ('Tuesday-Thursday', 'Tuesday-Thursday'),
        ('Only Fridays', 'Only Fridays'),
    ]

    TIME_CHOICES = [
        ('8-10 am', '8-10 am'),
        ('10-12 am', '10-12 am'),
        ('1-3 pm', '1-3 pm'),
        ('3-5 pm', '3-5 pm'),
        ('5-7 pm', '5-7 pm'),
        ('8-12 am', '8-12 am'),
    ]

    title = models.CharField(max_length=100)
    required_level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    description = models.TextField()
    class_days = models.CharField(max_length=100, choices=DAYS_CHOICES)
    class_time = models.CharField(max_length=50, choices=TIME_CHOICES)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'teacher'})
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='enrolled_courses')
    join_link = models.URLField(default="#")
    start_date = models.DateField(default=timezone.now)
    def __str__(self):
        return self.title


class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    grade = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'course')


class EnrollmentRequest(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'student'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    age = models.IntegerField()
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(null=True, default=None)
    is_seen = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.username} - {self.course.title}"


class Rating(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings')
    score = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'teacher')


class Assignment(models.Model):
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField()
    deadline = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    submitted_file = models.FileField(upload_to='assignments/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    graded = models.BooleanField(default=False)
    grade = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('assignment', 'student')


CONVERSATION_TOPICS = [
    ('Reading Skills', 'Reading Skills'),
    ('English Grammar', 'English Grammar'),
    ('Speaking', 'Speaking'),
    ('Vocabulary and Idiom', 'Vocabulary and Idiom'),
    ('Daily Life', 'Daily Life'),
    ('Fun', 'Fun'),
    ('Social Topics', 'Social Topics'),
    ('Movies', 'Movies'),
    ('Books', 'Books'),
    ('Music', 'Music'),
]




class Conversation(models.Model):
    topic = models.CharField(max_length=100, choices=CONVERSATION_TOPICS)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=200)
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    participants = models.ManyToManyField(User, related_name='participated_conversations', blank=True)

    def __str__(self):
        return f"{self.title} - by {self.user.username}"


class Comment(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name='liked_comments', blank=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.conversation.title}"

    def like_count(self):
        return self.likes.count()

    def is_liked_by(self, user):
        return self.likes.filter(id=user.id).exists()



class EducationalPost(models.Model):
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='educational_posts'
    )
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='educational_posts/', blank=True, null=True)
    description = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f"{self.title} - {self.teacher.username}"


class Exam(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="exams")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to="exams/", blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} - {self.course.title}"


class ExamSubmission(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.FileField(upload_to="exam_submissions/")
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    graded = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.student.username} - {self.exam.title}"