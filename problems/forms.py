from django import forms
from django.forms import inlineformset_factory

from .models import Problem, TestCase


class ProblemForm(forms.ModelForm):

    class Meta:
        model = Problem

        fields = [
            'title',
            'description',
            'input_description',
            'output_description',
            'constraints',
            'difficulty',
            'time_limit',
            'memory_limit',
        ]

        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Enter problem title...',
            }),

            'description': forms.Textarea(attrs={
                'rows': 8,
                'placeholder': 'Describe the problem...',
            }),

            'input_description': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Describe the input format...',
            }),

            'output_description': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Describe the output format...',
            }),

            'constraints': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Enter constraints...',
            }),

            'difficulty': forms.Select(),

            'time_limit': forms.NumberInput(attrs={
                'step': '0.1',
                'min': '0.1',
                'placeholder': 'Time limit in seconds...',
            }),

            'memory_limit': forms.NumberInput(attrs={
                'min': '1',
                'placeholder': 'Memory limit in MB...',
            }),
        }


class TestCaseForm(forms.ModelForm):

    class Meta:
        model = TestCase

        fields = [
            'input_data',
            'expected_output',
            'is_sample',
        ]

        widgets = {
            'input_data': forms.Textarea(attrs={
                'rows': 8,
                'placeholder': 'Enter the test input...',
            }),

            'expected_output': forms.Textarea(attrs={
                'rows': 8,
                'placeholder': 'Enter the expected output...',
            }),

            'is_sample': forms.CheckboxInput(),
        }


TestCaseFormSet = inlineformset_factory(
    Problem,
    TestCase,
    form=TestCaseForm,
    extra=1,
    can_delete=True,
)