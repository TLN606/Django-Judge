from django import forms

from .models import Classroom


class JoinClassroomForm(forms.Form):

    code = forms.CharField(
        max_length=20,
        label='Class Code',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Enter classroom code...',
                'autocomplete': 'off',
            }
        )
    )


class CreateClassroomForm(forms.ModelForm):

    class Meta:

        model = Classroom

        fields = [
            'name',
            'description',
        ]

        widgets = {

            'name': forms.TextInput(
                attrs={
                    'placeholder': 'Enter classroom name...',
                }
            ),

            'description': forms.Textarea(
                attrs={
                    'placeholder': 'Describe your classroom...',
                    'rows': 4,
                }
            ),

        }