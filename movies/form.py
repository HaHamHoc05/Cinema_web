from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    # Thêm trường email bắt buộc nhập
    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(required=True, label="Họ")
    last_name = forms.CharField(required=True, label="Tên")

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')