from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.urls import path, include



urlpatterns = [
    path('', views.attendance_dashboard, name='attendance_dashboard'),  # /attendance/
    #path('logout/', auth_views.LogoutView.as_view(next_page='admin-panel/superuser_login'), name='logout'),
    #path('accounts/', include('django.contrib.auth.urls')),
    path('logout/', views.custom_logout_view, name='logout'),

]
