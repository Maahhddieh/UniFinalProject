from django import forms
from .models import PlacementTestReservation, EnrollmentRequest, Assignment, Conversation, Comment, EducationalPost
import datetime
from .models import Course
from django.contrib.auth import get_user_model

User = get_user_model()

ENGLISH_LEVELS = [
    ('Beginner', 'Beginner'),
    ('Elementary', 'Elementary'),
    ('Intermediate', 'Intermediate'),
    ('Upper Intermediate', 'Upper Intermediate'),
    ('Advanced', 'Advanced'),
]

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

TIME_CHOICES = []
start = datetime.time(19, 0)
end = datetime.time(21, 0)
current = datetime.datetime.combine(datetime.date.today(), start)

while current.time() <= end:
    TIME_CHOICES.append((current.time().strftime('%H:%M'), current.time().strftime('%H:%M')))
    current += datetime.timedelta(minutes=15)


class PlacementTestReservationForm(forms.ModelForm):
    date = forms.DateField(
        label='Date',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    time = forms.ChoiceField(choices=TIME_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    level = forms.ChoiceField(choices=ENGLISH_LEVELS, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = PlacementTestReservation
        fields = ['full_name', 'phone', 'level', 'date', 'time']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_date(self):
        date = self.cleaned_data['date']
        if date.weekday() in [5, 6]:
            pass
        if date.weekday() in [5, 6]:
            raise forms.ValidationError('Booking on Saturdays and Sundays is not allowed.')

        if date < datetime.date.today():
            raise forms.ValidationError('Date cannot be in the past.')

        return date

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        time_str = cleaned_data.get('time')
        if date and time_str:
            time = datetime.datetime.strptime(time_str, '%H:%M').time()
            if PlacementTestReservation.objects.filter(date=date, time=time).exists():
                raise forms.ValidationError('This time slot is already booked.')


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'required_level', 'description', 'class_days', 'class_time', 'start_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
        }


class StudentSearchForm(forms.Form):
    query = forms.CharField(label='Search students', required=False)


class AddStudentToCourseForm(forms.Form):
    student_id = forms.IntegerField(widget=forms.HiddenInput())

    course_id = forms.ModelChoiceField(
        queryset=Course.objects.none(),
        label="Select a class",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['course_id'].queryset = Course.objects.filter(teacher=teacher)


class SetStudentLevelForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['level']
        widgets = {
            'level': forms.Select(attrs={'class': 'form-control'}),
        }


class EnrollmentRequestForm(forms.ModelForm):
    class Meta:
        model = EnrollmentRequest
        fields = ['full_name', 'age', 'email', 'phone', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional message to the teacher'}),
        }


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'deadline']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'})
        }


class ConversationForm(forms.ModelForm):
    class Meta:
        model = Conversation
        fields = ['topic', 'title', 'body']


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write your comment...'})
        }


class EducationalPostForm(forms.ModelForm):
    class Meta:
        model = EducationalPost
        fields = ['title', 'image', 'description']
