from django.db import models
from django.contrib.auth.models import User

ENGLISH_LEVELS = [
    ('Beginner', 'Beginner'),
    ('Elementary', 'Elementary'),
    ('Intermediate', 'Intermediate'),
    ('Upper Intermediate', 'Upper Intermediate'),
    ('Advanced', 'Advanced'),
]

class PlacementTestReservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    level = models.CharField(max_length=20, choices=ENGLISH_LEVELS)
    date = models.DateField()
    time = models.TimeField()

    def __str__(self):
        return f"{self.full_name} - {self.date} {self.time}"
