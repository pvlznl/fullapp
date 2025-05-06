from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload-excel/', views.upload_excel, name='upload_excel'),
    path('manage-critical-points/', views.manage_critical_points, name='manage_critical_points'),
    path('update-critical-point/<str:param>/', views.update_critical_point, name='update_critical_point'),
    path('delete-critical-point/<str:param>/', views.delete_critical_point, name='delete_critical_point'),
    path('problem-pc-list', views.problem_pc_list, name='problem_pc_list'),
    path('update-pc-list/', views.update_pc_list, name='update_pc_list'),
    path('update-pc<int:id_raw>/', views.update_pc, name='update_pc'),
    path('analitic', views.analitic, name='analitic'),
    path('login/', auth_views.LoginView.as_view(template_name='main/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
]