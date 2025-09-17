from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('register-customer/', views.register_customer, name = 'register_customer'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('update_profile/', views.update_profile, name='update_profile'),
    path('view_profile/', views.view_profile, name='view_profile'),
    path('change_password/', views.change_password, name='change_password'),
    path('manage_users/', views.manage_users, name='manage_users'),
    path('update_user_permissions/', views.update_user_permissions, name='update_user_permissions'),
    path('all_users/', views.all_users, name='all_users'),
    path('delete_user/<str:user_id>/', views.delete_user, name='delete_user'),
    path('profile_user/<str:user_id>/', views.profile_user, name='profile_user'),
]
