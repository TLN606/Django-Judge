from django import forms

from .models import Submission


class SubmissionForm(forms.ModelForm):

    language = forms.ChoiceField(
        choices=Submission.LANGUAGE_CHOICES,
        initial='cpp',
        required=True,
        widget=forms.Select(
            attrs={
                'class': 'submission-language-select',
                'id': 'languageSelect',
            }
        )
    )

    class Meta:
        model = Submission

        fields = [
            'language',
            'source_code',
        ]

        widgets = {
            'source_code': forms.Textarea(
                attrs={
                    'class': 'submission-code-editor',
                    'placeholder': 'Write your solution here...',
                    'spellcheck': 'false',
                }
            ),
        }

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    self.fields['language'].initial = 'cpp'