from django.urls import path
from django.contrib.auth import views as auth_views


<<<<<<< HEAD
from .views import (ocr_result_view, quantity_graded_eggs, extract_table_rows_from_file, template_list, load_template_list, template_config, login,index, submit_form_ajax, extractor, submit_form_extractor , sample, logout_request, CustomLoginView, change_password, template_detail, edit_form_ajax, disable_form_ajax)
=======
from .views import (ocr_result_view, quantity_graded_eggs, extract_table_rows_from_file, template_list, load_template_list, template_config, login,index, submit_form_ajax, extractor, sample, logout_request, CustomLoginView, change_password, template_detail, edit_form_ajax, disable_form_ajax, get_ave, upload_form)
>>>>>>> 8bfa44fd6ec0ed3ad742937fc6ef48e465824e5f


app_name = 'main'

urlpatterns = [
    #LOGIN
    path("", CustomLoginView.as_view(), name="login"),
    #path("login/", login, name="login"),
    path("index/", index, name="index"),
    
    path("template_list/", template_list, name="template_list"),
    path("load_template_list/", load_template_list, name="load_template_list"),
    path("template_config/", template_config, name="template_config"),

    path("template_config/<int:pk>", template_config, name="template_config_edit"),
    path("template_detail/<int:pk>/", template_detail, name="template_detail"),
    
    path('submit_form_ajax/', submit_form_ajax, name='submit_form_ajax'),
    
    path('edit_form_ajax/<int:pk>', edit_form_ajax, name="edit_form_ajax"),
    path('disable_form_ajax/<int:pk>', disable_form_ajax, name="disable_form_ajax"),
<<<<<<< HEAD
    
=======

    
    path('get_ave/', get_ave, name='get_ave'),
    path('upload_form/', upload_form, name='upload_form'),
    path("template_detail/<int:pk>/", template_detail, name="template_detail"),
>>>>>>> 8bfa44fd6ec0ed3ad742937fc6ef48e465824e5f
    path("extractor/", extractor, name="extractor"),
    path("submit_form_extractor/", submit_form_extractor, name="submit_form_extractor"),
    
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
