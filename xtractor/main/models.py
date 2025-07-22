from email.policy import default
from random import choices
from django.utils.timezone import now
from django.db import models
from django.contrib.auth.models import User


# class Type(models.Model):
# 	delivery_code = models.ForeignKey(DeliveryCode, on_delete=models.CASCADE, null=True, blank=True)
# 	by_request_item = models.ForeignKey(ByRequestItems, on_delete=models.CASCADE, null=True, blank=True)
# 	total_weekly_request = models.FloatField(default=0, null=True, blank=True)
# 	first_delivery = models.FloatField(default=0, null=True, blank=True)
# 	second_delivery = models.FloatField(default=0, null=True, blank=True)
# 	third_delivery = models.FloatField(default=0, null=True, blank=True)
# 	fourth_delivery = models.FloatField(default=0, null=True, blank=True)
# 	first_final_delivery = models.FloatField(default=0, null=True, blank=True)
# 	second_final_delivery = models.FloatField(default=0, null=True, blank=True)
# 	third_final_delivery = models.FloatField(default=0, null=True, blank=True)
# 	fourth_final_delivery = models.FloatField(default=0, null=True, blank=True)
# 	first_qty_delivery = models.FloatField(default=0, null=True, blank=True)
# 	second_qty_delivery = models.FloatField(default=0, null=True, blank=True)
# 	third_qty_delivery = models.FloatField(default=0, null=True, blank=True)
# 	fourth_qty_delivery = models.FloatField(default=0, null=True, blank=True)
# 	first_qty_uom = models.CharField(max_length=20, null=True, blank=True)
# 	second_qty_byrequest_uom = models.CharField(max_length=20, null=True, blank=True)
# 	third_qty_byrequest_uom = models.CharField(max_length=20, null=True, blank=True)
# 	fourth_qty_byrequest_uom = models.CharField(max_length=20, null=True, blank=True)




class Type(models.Model):
    type = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.type



class FormObject(models.Model):
    type = models.ForeignKey(Type, on_delete=models.CASCADE)
    title = models.CharField(max_length=40, null=True, blank=True)

    def __str__(self):
        return self.title


class HeaderObjects(models.Model):
    HEADER_TYPE_CHOICES = [
        ('label', 'Label'),
        ('value', 'Value'),
    ]

    form_object = models.ForeignKey(FormObject, on_delete=models.CASCADE)
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
    form_object = models.ForeignKey(FormObject, on_delete=models.CASCADE)
    row_name = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.row_name


class FieldObject(models.Model):
    label = models.CharField(max_length=50)

