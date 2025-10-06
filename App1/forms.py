from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Profile
#from django.contrib.auth.models import User

class ProfileRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)  # Ensure email is required
    phone_number = forms.CharField(max_length=15, required=False)
    

    class Meta:
        model = Profile
        fields = ['username', 'email', 'phone_number', 'password1', 'password2']
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['username', 'email', 'phone_number', 'address', 'child_name', 'whatsapp_number', 'gender', 'date_of_birth', 'disability', 'disability_description']        