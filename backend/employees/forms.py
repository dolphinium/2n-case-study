from django import forms

class CheckInForm(forms.Form):
    check_in_time = forms.TimeField(widget=forms.TimeInput(format='%H:%M'), input_formats=['%H:%M'], required=False)

class CheckOutForm(forms.Form):
    check_out_time = forms.TimeField(widget=forms.TimeInput(format='%H:%M'), input_formats=['%H:%M'], required=False)