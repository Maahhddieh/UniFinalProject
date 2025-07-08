from django import forms
from .models import PlacementTestReservation
import datetime

TIME_CHOICES = []
start = datetime.time(9, 0)
end = datetime.time(18, 0)
current = datetime.datetime.combine(datetime.date.today(), start)

while current.time() <= end:
    TIME_CHOICES.append((current.time().strftime('%H:%M'), current.time().strftime('%H:%M')))
    current += datetime.timedelta(minutes=15)

class PlacementTestReservationForm(forms.ModelForm):
    time = forms.ChoiceField(choices=TIME_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = PlacementTestReservation
        fields = ['date', 'time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def clean_date(self):
        date = self.cleaned_data['date']
        if date.weekday() == 4:  # جمعه‌ها
            raise forms.ValidationError('رزرو در روز جمعه امکان‌پذیر نیست.')
        if date < datetime.date.today():
            raise forms.ValidationError('تاریخ نمی‌تواند قبل از امروز باشد.')
        return date

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        time_str = cleaned_data.get('time')
        if date and time_str:
            time = datetime.datetime.strptime(time_str, '%H:%M').time()
            exists = PlacementTestReservation.objects.filter(date=date, time=time).exists()
            if exists:
                raise forms.ValidationError('این زمان قبلاً رزرو شده است.')
