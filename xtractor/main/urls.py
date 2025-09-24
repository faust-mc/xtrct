from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf.urls import handler403

from .views import (ocr_result_view, quantity_graded_eggs, extract_table_rows_from_file, template_list, load_template_list, template_config, login,index, submit_form_ajax, extractor, sample, logout_request, CustomLoginView, change_password, template_detail, edit_form_ajax, disable_form_ajax, get_ave, upload_form, save_form, download_excel, filter_data, get_files, form_detail)


app_name = 'main'


handler403 = "main.views.custom_permission_denied_view"

urlpatterns = [
    #LOGIN
    path("", CustomLoginView.as_view(), name="login"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("index/", index, name="index"),
    
    
    path("template_list/", template_list, name="template_list"),
    path("load_template_list/", load_template_list, name="load_template_list"),
    path("template_config/", template_config, name="template_config"),

    path("template_config/<int:pk>", template_config, name="template_config_edit"),
    path("template_detail/<int:pk>/", template_detail, name="template_detail"),
    
    path('submit_form_ajax/', submit_form_ajax, name='submit_form_ajax'),
    
    path('edit_form_ajax/<int:pk>', edit_form_ajax, name="edit_form_ajax"),
    path('disable_form_ajax/<int:pk>', disable_form_ajax, name="disable_form_ajax"),

    path('get_ave/', get_ave, name='get_ave'),
    path('upload_form/', upload_form, name='upload_form'),
    path("template_detail/<int:pk>/", template_detail, name="template_detail"),

    path("extractor/", extractor, name="extractor"),
    path('save_form/', save_form, name='save_form'),
    path("download_excel/<str:filename>", download_excel, name="download_excel"),
    path("extract_text/", ocr_result_view, name="ocr-result"),

    path("filter_data/", filter_data, name="filter_data"),
    path("get_files/", get_files, name="get_files"),
    path("form_detail/<int:pk>/", form_detail, name="form_detail"),


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
