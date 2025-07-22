from django.contrib import admin
from .models import Type, FormObject, HeaderObjects, RowObjects, FieldObject


admin.site.register([Type, FormObject, HeaderObjects, RowObjects, FieldObject])

