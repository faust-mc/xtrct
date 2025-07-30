from django import forms
from .models import Type, FormObject, HeaderObjects, RowObjects, FieldObject

class TypeForm(forms.ModelForm):
    class Meta:
        model = Type
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