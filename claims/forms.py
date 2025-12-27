from django import forms
from django.contrib.auth.forms import UserCreationForm
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


class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'department', 'phone', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})


class UserProfileEditForm(forms.ModelForm):
    """Form for users to edit their own profile"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'position', 'department', 'phone', 'profile_photo', 'bio']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Tell us about yourself...'}),
        }


class AdminUserEditForm(forms.ModelForm):
    """Form for admins to edit all user fields"""
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'position', 'department',
                  'phone', 'role', 'is_active', 'profile_photo', 'bio']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }
