from django.urls import path

from .views import ocr_result_view, quantity_graded_eggs, extract_table_rows_from_file, template_config, login,index

urlpatterns = [
    #LOGIN
    path("", login, name="login"),
    path("login/", login, name="login"),
    
    path("index/", index, name="index"),
    
    path("template_config/", template_config, name="template_config"),
    path("sample1/", ocr_result_view, name="ocr-result"),
    path("sample2/", quantity_graded_eggs, name="quantity_graded_eggs"),
    path("sample3/", extract_table_rows_from_file, name="quantity_graded_eggs"),

]
