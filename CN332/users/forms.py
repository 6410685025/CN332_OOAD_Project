from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from .models import User, Resident

class LoginForm(AuthenticationForm):
    # You can add custom styling here if needed
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class ResidentCreationForm(forms.Form):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label='First Name',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label='Last Name',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'})
    )
    username = forms.CharField(
        max_length=150,
        required=True,
        label='Username',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        required=True,
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    password_confirm = forms.CharField(
        required=True,
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )
    contact_number = forms.CharField(
        max_length=20,
        required=False,
        label='Contact Number',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number (optional)'})
    )
    building = forms.CharField(
        max_length=50,
        required=True,
        label='Building',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Building A'})
    )
    floor = forms.IntegerField(
        required=True,
        label='Floor',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Floor number'})
    )
    room_number = forms.CharField(
        max_length=20,
        required=True,
        label='Room Number',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Room number'})
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username already exists.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already in use.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise forms.ValidationError('Passwords do not match.')
        
        return cleaned_data


class ResidentProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label='First Name',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label='Last Name',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    contact_number = forms.CharField(
        max_length=20,
        required=False,
        label='Contact Number',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'})
    )
    profile_photo = forms.ImageField(
        required=False,
        label='Profile Photo',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'contact_number', 'profile_photo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].initial = self.instance.first_name
        self.fields['last_name'].initial = self.instance.last_name
        self.fields['email'].initial = self.instance.email


class ResidentPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label='Current Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
