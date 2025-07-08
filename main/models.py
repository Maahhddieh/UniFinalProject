from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model

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

    def is_student(self):
        return self.user_type == 'student'

    def is_teacher(self):
        return self.user_type == 'teacher'


User = get_user_model()

class PlacementTestReservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    level = models.CharField(max_length=20, choices=ENGLISH_LEVELS)
    date = models.DateField()
    time = models.TimeField()

    def __str__(self):
        return f"{self.full_name} - {self.date} {self.time}"
