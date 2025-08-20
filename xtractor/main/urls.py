from django.urls import path
from django.contrib.auth import views as auth_views


from .views import (ocr_result_view, quantity_graded_eggs, extract_table_rows_from_file, template_config, login,index, submit_form_ajax, extractor, sample, logout_request, CustomLoginView, change_password)


app_name = 'main'

urlpatterns = [
    #LOGIN
    path("", CustomLoginView.as_view(), name="login"),
   # path("login/", login, name="login"),
    path("index/", index, name="index"),
    path("template_config/", template_config, name="template_config"),
    path("extractor/", extractor, name="extractor"),
    
    path("sample1/", ocr_result_view, name="ocr-result"),
    path("sample2/", quantity_graded_eggs, name="quantity_graded_eggs"),
    #path("sample3/", extract_table_by_headers2, name="quantity_graded_eggs"),
    path("sample3/", extract_table_rows_from_file, name="quantity_graded_eggs"),
    
    #AJAX
    path('submit_form_ajax/', submit_form_ajax, name='submit_form_ajax'),
    
    
    path("sample/", sample, name="sample"),

    path("login/", CustomLoginView.as_view(), name='login_request'),
    path("logout/", logout_request, name='logout_request'),

    path("change-password/", change_password, name="change_password"),

]
