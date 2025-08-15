from django.contrib import admin
from django.urls import path, include
from admin_ui.views import superuser_login_view, create_superuser_view, register_lecturer_view

urlpatterns = [
    # 👋 Landing page for superuser login
    path('', superuser_login_view, name='superuser_login'),

    # ✅ Admin UI routes (namespaced)
    path('admin-panel/', include('admin_ui.urls', namespace='admin_ui')),

    # 🛠 Django Admin
    path('admin/', admin.site.urls),

    # 👤 Create Superuser (direct route — optional if already in admin_ui.urls)
    path('create-superuser/', create_superuser_view, name='create_superuser'),

    # 📊 Attendance App
    path('attendance/', include('attendance.urls')),

    # 📋 Lecturer Registration (optional if already namespaced)
    path('register-lecturer/', register_lecturer_view, name='register_lecturer'),
]
