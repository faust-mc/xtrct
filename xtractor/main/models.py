from email.policy import default
from random import choices
from django.utils.timezone import now
from django.db import models
from django.contrib.auth.models import User
import json


# class Type(models.Model):
#   delivery_code = models.ForeignKey(DeliveryCode, on_delete=models.CASCADE, null=True, blank=True)
#   by_request_item = models.ForeignKey(ByRequestItems, on_delete=models.CASCADE, null=True, blank=True)
#   total_weekly_request = models.FloatField(default=0, null=True, blank=True)
#   first_delivery = models.FloatField(default=0, null=True, blank=True)
#   second_delivery = models.FloatField(default=0, null=True, blank=True)
#   third_delivery = models.FloatField(default=0, null=True, blank=True)
#   fourth_delivery = models.FloatField(default=0, null=True, blank=True)
#   first_final_delivery = models.FloatField(default=0, null=True, blank=True)
#   second_final_delivery = models.FloatField(default=0, null=True, blank=True)
#   third_final_delivery = models.FloatField(default=0, null=True, blank=True)
#   fourth_final_delivery = models.FloatField(default=0, null=True, blank=True)
#   first_qty_delivery = models.FloatField(default=0, null=True, blank=True)
#   second_qty_delivery = models.FloatField(default=0, null=True, blank=True)
#   third_qty_delivery = models.FloatField(default=0, null=True, blank=True)
#   fourth_qty_delivery = models.FloatField(default=0, null=True, blank=True)
#   first_qty_uom = models.CharField(max_length=20, null=True, blank=True)
#   second_qty_byrequest_uom = models.CharField(max_length=20, null=True, blank=True)
#   third_qty_byrequest_uom = models.CharField(max_length=20, null=True, blank=True)
#   fourth_qty_byrequest_uom = models.CharField(max_length=20, null=True, blank=True)




class FormName(models.Model):
    name = models.CharField(max_length=40, null=True, blank=True)
    status = models.IntegerField(default=1)
    
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
