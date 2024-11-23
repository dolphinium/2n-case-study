from django import forms
from .models import LeaveRequest


class CheckInForm(forms.Form):
    check_in_time = forms.TimeField(widget=forms.TimeInput(
        format='%H:%M'), input_formats=['%H:%M'], required=False)


class CheckOutForm(forms.Form):
    check_out_time = forms.TimeField(widget=forms.TimeInput(
        format='%H:%M'), input_formats=['%H:%M'], required=False)


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError(
                    "End date must be after start date.")
