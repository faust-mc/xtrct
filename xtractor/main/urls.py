from django.urls import path
from .views import ocr_result_view, quantity_graded_eggs

urlpatterns = [
    path("ocr/", ocr_result_view, name="ocr-result"),
    path("quantity_graded_eggs/", quantity_graded_eggs, name="quantity_graded_eggs"),

]
