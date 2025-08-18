from django.contrib import admin
from django.urls import path, include
from admin_ui.views import admin_login_view, create_admin_view, register_lecturer_view

urlpatterns = [
    # 👋 Landing page for Admin login
path('', admin_login_view, name='admin_login'),

    # ✅ Admin UI routes (namespaced)
    path('admin-panel/', include('admin_ui.urls', namespace='admin_ui')),

    # 🛠 Django Admin
    path('admin/', admin.site.urls),

    # 👤 Create Admin (direct route — optional if already in admin_ui.urls)
path('create-admin/', create_admin_view, name='create_admin'),

    # 📊 Attendance App
    path('attendance/', include('attendance.urls')),

    # 📋 Lecturer Registration (optional if already namespaced)
    path('register-lecturer/', register_lecturer_view, name='register_lecturer'),
]
