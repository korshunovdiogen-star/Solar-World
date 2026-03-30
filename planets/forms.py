from django import forms
from .models import Mission

class MissionAdminForm(forms.ModelForm):
    class Meta:
        model = Mission
        fields = '__all__'

    class Media:
        js = ('js/mission_status_toggle.js',)