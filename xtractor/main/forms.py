from django import forms
from .models import ComponentType, FormObject, HeaderObjects, RowObjects, FieldObject

class TypeForm(forms.ModelForm):
    class Meta:
        model = ComponentType
        fields = ['type']

class FormObjectForm(forms.ModelForm):
    class Meta:
        model = FormObject
        fields = ['type','title']
        
class HeaderObjectsForm(forms.ModelForm):
    class Meta:
        model = HeaderObjects
        fields = ['form_object','header_name','header_type']
        widgets = {
            'header_type':forms.Select(choices=HeaderObjects.HEADER_TYPE_CHOICES)
        }

class RowObjectsForm(forms.ModelForm):
    class Meta:
        model = RowObjects
        fields = ['form_object','row_name']
        
class FieldObjectForm(forms.ModelForm):
    class Meta:
        model = FieldObject
        fields = ['label']





class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Old Password'}),
        label="Old Password"
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'New Password'}),
        label="New Password"
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm New Password'}),
        label="Confirm New Password"
    )
