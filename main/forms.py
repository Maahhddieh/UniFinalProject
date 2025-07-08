from django import forms
from .models import PlacementTestReservation
import datetime

ENGLISH_LEVELS = [
    ('Beginner', 'Beginner'),
    ('Elementary', 'Elementary'),
    ('Intermediate', 'Intermediate'),
    ('Upper Intermediate', 'Upper Intermediate'),
    ('Advanced', 'Advanced'),
]

TIME_CHOICES = []
start = datetime.time(9, 0)
end = datetime.time(18, 0)
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
        # شنبه و یکشنبه را بلاک می‌کنیم (در پایتون 5=شنبه، 6=یکشنبه نیست، 5=جمعه است؛
        # شنبه=5 در ایران است ولی در پایتون روز هفته به این صورت است: 0=دوشنبه تا 6=یکشنبه)
        # پس شنبه=5 یا یکشنبه=6 نیست، شنبه = 5 در ایران است ولی در پایتون شنبه=5 معنی ندارد.
        # برای هفته ایران باید شنبه و یکشنبه را اینطور چک کنیم:
        if date.weekday() in [5, 6]:  # 5=شنبه نیست، 5=جمعه، 6=شنبه؟
            # در پایتون 0=دوشنبه، 6=یکشنبه است
            # پس شنبه=5 یعنی جمعه نیست!
            # برای ایران شنبه و یکشنبه را بلاک کنیم: شنبه=5 و یکشنبه=6 نیست، شنبه=5 در پایتون = جمعه است
            # پس برای ایران باید جمعه و شنبه بلاک شود یعنی 4 و 5
            pass

        # پس اگر شنبه و یکشنبه بخواییم بلاک کنیم، یعنی روزهای 5 و 6 (شنبه=5, یکشنبه=6)
        if date.weekday() in [5, 6]:  # اینجا شنبه=5 و یکشنبه=6
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
