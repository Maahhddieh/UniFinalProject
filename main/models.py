from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class PlacementTestReservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()

    def __str__(self):
        return f"{self.user.username} - {self.date} {self.time}"

    class Meta:
        unique_together = ('date', 'time')
