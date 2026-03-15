from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    AdminCHVManagementViewSet,
    SelfRegisterView, 
    CHVManagedUsersViewSet, 
    SyncDataView,
    admin_dashboard_view,
    admin_export_all_csv, 
    chv_dashboard_view,
    chv_landing_view,       
    chv_login_action,
    chv_logout_action,       
    chv_register_action,
    chv_user_detail_view,
    export_dashboard_csv     
)

router = DefaultRouter()
router.register(r'chv/users', CHVManagedUsersViewSet, basename='chv-managed-users')
admin_router = DefaultRouter()
admin_router.register(r'admin/chvs', AdminCHVManagementViewSet, basename='admin-chv-mgmt')

urlpatterns = [
    # --- WEB VIEWS ---
    path('', chv_landing_view, name='chv-landing'),
    path('dashboard/', chv_dashboard_view, name='chv-dashboard'),
    path('dashboard/export/', export_dashboard_csv, name='dashboard-export'),
    
    # --- WEB AJAX AUTH ---
    path('auth/chv/login/', chv_login_action, name='chv-login-action'),
    path('auth/chv/register/', chv_register_action, name='chv-register-action'),
    path('dashboard/user/<uuid:anonymous_id>/', chv_user_detail_view, name='chv-user-detail'),
    path('auth/chv/logout/', chv_logout_action, name='chv-logout'),
    path('admin-dashboard/', admin_dashboard_view, name='admin-dashboard'),
    path('admin/export-all/', admin_export_all_csv, name='admin-export-all'),

    # 2. Admin API Endpoints (Included via the router)
    path('api/', include(admin_router.urls)),

    # --- MOBILE APP API ---
    path('api/auth/register/', SelfRegisterView.as_view(), name='api-self-register'),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='api-login'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='api-token-refresh'),
    path('api/sync/', SyncDataView.as_view(), name='api-sync'),
    path('api/', include(router.urls)),
]