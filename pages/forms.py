from django import forms
from .models import Documents

COUNTRY_CHOICES = [
    ('all', 'All Countries (Global)'),
    ('234', 'Nigeria (+234) Only'),
]

class UpFile(forms.ModelForm):
    contact_prefix = forms.CharField(
        max_length=30,
        required=False,
        initial='ZG',
        label='Contact Name Prefix',
        help_text='Prefix used for contact names (e.g. ZG1, ZG2...)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. ZG, GroupLead, Contact'
        })
    )
    country_filter = forms.ChoiceField(
        choices=COUNTRY_CHOICES,
        required=False,
        initial='all',
        label='Country Filter',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    class Meta:
        model = Documents
        fields = ['documents']
        widgets = {
            'documents': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.html,.htm,.txt',
                'id': 'document-file-input',
            })
        }
        labels = {
            'documents': 'WhatsApp HTML / Text File',
        }