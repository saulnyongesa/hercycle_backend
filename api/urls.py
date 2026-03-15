from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from .views import (
    SyncDataView, SyncStatusView, NotificationViewSet, AdviceMessageViewSet,
    SignupView, ProfileView, ChangePasswordView, LogoutView,
    CycleViewSet, SymptomViewSet, MLRiskAssessmentView, StatsAnalyticsView,
    LibraryArticleViewSet, CustomTokenObtainPairView, CustomTokenRefreshView
)

router = SimpleRouter()
router.register(r'notifications', NotificationViewSet, basename='notifications')
router.register(r'advice', AdviceMessageViewSet, basename='advice')
router.register(r'cycles', CycleViewSet, basename='cycles')
router.register(r'symptoms', SymptomViewSet, basename='symptoms')
router.register(r'library', LibraryArticleViewSet, basename='library')

urlpatterns = [
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # 1. AUTHENTICATION
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/signup/', SignupView.as_view(), name='signup'),

    path('auth/profile/', ProfileView.as_view(), name='profile'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change_password'),

    # 3. ML MODEL INTEGRATION
    path('ml/assess/', MLRiskAssessmentView.as_view(), name='ml-assess'),

    # 4. STATS & ANALYTICS
    path('stats/summary/', StatsAnalyticsView.as_view(), name='stats-summary'),

    # 8. SYNC ENDPOINTS
    path('sync/', SyncDataView.as_view(), name='sync-post'),
    path('sync/status/', SyncStatusView.as_view(), name='sync-status'),

    # INCLUDES FOR VIEWSETS (Cycles, Symptoms, Advice, Notifications)
    path('', include(router.urls)),
]