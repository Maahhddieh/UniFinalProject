from django.contrib import admin

from main.models import Assignment, AssignmentSubmission, Course, CustomUser, PlacementTestReservation, Enrollment, \
    EnrollmentRequest, Rating, Conversation

# Register your models here.
admin.site.register(Assignment)
admin.site.register(AssignmentSubmission)
admin.site.register(Course)
admin.site.register(CustomUser)
admin.site.register(PlacementTestReservation)
admin.site.register(Enrollment)
admin.site.register(EnrollmentRequest)
admin.site.register(Rating)
admin.site.register(Conversation)
