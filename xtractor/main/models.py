from email.policy import default
from random import choices
from django.utils.timezone import now
from django.db import models
from django.contrib.auth.models import User
import json



class Pages(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        permissions = [
            ("access_extractor_page", "Can access Extractor Page"),
            ("access_template_list_page", "Can access Template List Page"),
            ("access_template_config_page", "Can access Template Config Page"),
            ("access_get_files_page", "Can access Extracted Files Page"),
        ]



class FormName(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=40, null=True, blank=True)
    status = models.IntegerField(default=1)
    allowed_users = models.ManyToManyField(User, related_name="forms_allowed", blank=True)
    
    def __str__(self):
        return self.name




class ComponentType(models.Model):
    type = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.type



class FormObject(models.Model):
    form_name = models.ForeignKey(FormName, on_delete=models.CASCADE, null=True, blank=True)
    type = models.ForeignKey(ComponentType, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=40, null=True, blank=True)

    def __str__(self):
        return self.title
        # return f"{self.form_name.name} - {self.title}"


class HeaderObjects(models.Model):
    HEADER_TYPE_CHOICES = [
        ('label', 'Label'),
        ('value', 'Value'),
    ]

    form_object = models.ForeignKey(FormObject, on_delete=models.CASCADE, related_name="headers")
    header_name = models.CharField(max_length=20, null=True, blank=True)
    header_width= models.FloatField(default=0.0)
    header_type = models.CharField(
        max_length=10,
        choices=HEADER_TYPE_CHOICES,
        default='label',
        null=True,
        blank=True
    )

    def __str__(self):
        return self.header_name


class RowObjects(models.Model):
    form_object = models.ForeignKey(FormObject, on_delete=models.CASCADE, related_name="rows")
    row_name = models.CharField(max_length=30, null=True, blank=True)

    def __str__(self):
        return self.row_name


class FieldObject(models.Model):
    label = models.CharField(max_length=50)


class Extraction(models.Model):
    source = models.CharField(max_length=255, blank=True, null=True)  # e.g., filename, API source
    form_name = models.ForeignKey(FormName, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Extraction {self.id} ({self.source})"





class ExtractedFields(models.Model):
    extraction = models.ForeignKey(
        "Extraction", on_delete=models.CASCADE, related_name="fields"
    )
    fields_raw = models.TextField()  # store raw JSON string

    @property
    def fields(self):
        """Return JSON as Python dict."""
        try:
            return json.loads(self.fields_raw)
        except (TypeError, ValueError):
            return {}

    @fields.setter
    def fields(self, value):
        """Save Python dict as JSON string."""
        self.fields_raw = json.dumps(value)

    def __str__(self):
        return f"Fields for Extraction {self.extraction_id}"


class ExtractedTable(models.Model):
    extraction = models.ForeignKey(
        "Extraction", on_delete=models.CASCADE, related_name="tables"
    )
    table_name = models.CharField(max_length=255)
    data_raw = models.TextField()  # store raw JSON string

    @property
    def data(self):
        """Return JSON as Python list of dicts."""
        try:
            return json.loads(self.data_raw)
        except (TypeError, ValueError):
            return []

    @data.setter
    def data(self, value):
        """Save Python list/dict as JSON string."""
        self.data_raw = json.dumps(value)

    def __str__(self):
        return f"Table: {self.table_name} (Extraction {self.extraction_id})"
