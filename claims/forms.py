from django import forms
from django.contrib.auth.models import Permission
from .models import User, Claim, Comment, Document, Voyage, ShipOwner


class ClaimForm(forms.ModelForm):
    class Meta:
        model = Claim
        fields = [
            'voyage', 'claim_type', 'cost_type', 'status', 'payment_status',
            'laytime_used', 'claim_amount', 'paid_amount', 'currency',
            'claim_deadline', 'description', 'internal_notes', 'assigned_to'
        ]
        widgets = {
            'voyage': forms.Select(attrs={'class': 'form-select'}),
            'claim_type': forms.Select(attrs={'class': 'form-select'}),
            'cost_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'laytime_used': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'claim_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'paid_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'claim_deadline': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'internal_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(role__in=['WRITE', 'ADMIN'])
        self.fields['assigned_to'].required = False
        self.fields['cost_type'].required = False
        self.fields['laytime_used'].required = False


class ClaimStatusForm(forms.ModelForm):
    class Meta:
        model = Claim
        fields = ['status', 'payment_status', 'paid_amount', 'settlement_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'paid_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'settlement_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class VoyageAssignmentForm(forms.Form):
    analyst = forms.ModelChoiceField(
        queryset=User.objects.filter(role__in=['WRITE', 'ADMIN']),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Assign to Analyst"
    )


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Add a comment...'}),
        }


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'document_type', 'file', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }


# DEPRECATED: UserRegistrationForm removed Jan 4, 2026
# Self-registration feature removed from system for security
# Admin-only user creation via AdminUserCreationForm is now used


class UserProfileEditForm(forms.ModelForm):
    """Form for users to edit their own profile"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'position', 'department', 'profile_photo', 'bio']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Tell us about yourself...'}),
        }


class AdminUserEditForm(forms.ModelForm):
    """Form for admins to edit all user fields"""
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'position', 'department',
                  'role', 'is_active', 'profile_photo', 'bio']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }


class AdminUserCreationForm(forms.ModelForm):
    """Form for admins to create new user accounts with role and permissions"""
    password1 = forms.CharField(
        label='Temporary Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'id_password1',
            'autocomplete': 'new-password'
        }),
        help_text='User will be required to change this password on first login.',
        required=True
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password'
        }),
        help_text='Enter the same password again for verification.',
        required=True
    )

    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.filter(content_type__app_label='claims'),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        help_text='Select specific permissions for this user. Note: Role-based permissions are automatically granted.'
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'position', 'department', 'role']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., jdoe',
                'autocomplete': 'off'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., John',
                'autocomplete': 'off'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Doe',
                'autocomplete': 'off'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., john.doe@company.com',
                'autocomplete': 'off'
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Claims Analyst',
                'autocomplete': 'off'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Claims Department',
                'autocomplete': 'off'
            }),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }
        help_texts = {
            'username': 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
            'email': 'User will receive account details at this email address.',
            'role': 'Determines what the user can do in the system.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields required except permissions
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.must_change_password = True  # Force password change on first login

        if commit:
            user.save()
            # Set permissions
            if self.cleaned_data.get('permissions'):
                user.user_permissions.set(self.cleaned_data['permissions'])

        return user
