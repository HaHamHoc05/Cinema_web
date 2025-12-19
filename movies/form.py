from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from movies.models import Review


class SignUpForm(UserCreationForm):
    # Thêm trường email bắt buộc nhập
    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(required=True, label="Họ")
    last_name = forms.CharField(required=True, label="Tên")

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3, 'class': 'form-control bg-dark text-white border-secondary',
                                             'placeholder': 'Viết cảm nhận của bạn...'}),
            'rating': forms.NumberInput(
                attrs={'type': 'range', 'min': '1', 'max': '5', 'class': 'form-range', 'step': '1'}),
        }


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control bg-dark text-white'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control bg-dark text-white'}),
            'email': forms.EmailInput(attrs={'class': 'form-control bg-dark text-white'}),
        }