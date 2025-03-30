from django import forms
from wasteapp.models import WasteTip, CommunityInitiative


class WasteTipForm(forms.ModelForm):
    class Meta:
        model = WasteTip
        fields = ['title', 'content', 'tag', 'youtube_link']

class CommunityInitiativeForm(forms.ModelForm):
    class Meta:
        model = CommunityInitiative
        fields = ['title', 'description', 'location', 'start_date', 'end_date', 'location_link']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
        }

