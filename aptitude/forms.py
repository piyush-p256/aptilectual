# aptitude/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, UserAnswer

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')
    name = forms.CharField(max_length=100, required=False, help_text='Full name')
    start_year = forms.IntegerField(required=False, help_text='Start year')
    end_year = forms.IntegerField(required=False, help_text='End year')
    branch = forms.CharField(max_length=100, required=False, help_text='Branch')
    student_class = forms.IntegerField(required=False, help_text='Class (as integer)')
    enrollment_number = forms.CharField(max_length=20, required=False, help_text='Enrollment number')
    contact_number = forms.CharField(max_length=15, required=False, help_text='Contact number')
    
    

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'name', 'password1', 'password2',   'start_year', 'end_year', 'branch', 'student_class', 'enrollment_number', 'contact_number')


class LoginForm(AuthenticationForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'password')

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = UserAnswer
        fields = ['selected_option', 'solution_image_url']
