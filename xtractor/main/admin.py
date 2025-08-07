from django.contrib import admin
from .models import ComponentType, FormObject, HeaderObjects, RowObjects, FieldObject, FormName


admin.site.register([ComponentType, FormObject, HeaderObjects, RowObjects, FieldObject, FormName])

