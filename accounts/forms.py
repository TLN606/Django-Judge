from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


User = get_user_model()


class RegisterForm(UserCreationForm):

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'Enter your email',
                'autocomplete': 'email',
            }
        )
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password1',
            'password2',
        ]

        widgets = {
            'username': forms.TextInput(
                attrs={
                    'placeholder': 'Choose a username',
                    'autocomplete': 'username',
                }
            ),
        }

    def save(self, commit=True):

        user = super().save(commit=False)

        # Người dùng đăng ký công khai
        # luôn được tạo với quyền Student
        user.email = self.cleaned_data['email']
        user.role = 'student'

        if commit:
            user.save()

        return user