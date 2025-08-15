from django import forms

# 🔐 Superuser Creation
class SuperUserCreationForm(forms.Form):
    username = forms.CharField(label="Username", max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    passkey = forms.CharField(label="Passkey", widget=forms.TextInput(attrs={'class': 'form-control'}))

# 👨‍🏫 Lecturer Registration
class LecturerRegistrationForm(forms.Form):
    superuser = forms.CharField(
        label='Registered By',
        required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )
    full_name = forms.CharField(max_length=150, label='Lecturer Full Name')
    email = forms.EmailField(label='Lecturer Email')
    department = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput, label='Lecturer Password')

# 🔐 Login Forms
class SuperUserLoginForm(forms.Form):
    username = forms.CharField(max_length=150, label='Username', widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter username'
    }))
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter password'
    }))

class LecturerLoginForm(forms.Form):
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter email'
    }))
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter password'
    }))

class OfficerLoginForm(forms.Form):
    email = forms.EmailField(label='Email Address')
    password = forms.CharField(widget=forms.PasswordInput)

class RegistrationOfficerLoginForm(forms.Form):
    email = forms.EmailField(label='Email Address')
    password = forms.CharField(widget=forms.PasswordInput)

# 📥 CSV Upload for Registration Officer Dashboard
class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(label="Upload Student CSV")

# 📥 CSV Upload for Admin Preview Flow
class StudentCSVUploadForm(forms.Form):
    session = forms.CharField(label='Academic Session', required=False)
    level = forms.CharField(label='Level', required=False)
    csv_file = forms.FileField(label='Upload Student CSV')


