from django.utils import timezone
from django.db import transaction
from django.db.models import Count
from django.utils.html import strip_tags
from dateutil.parser import parse
from datetime import date, timedelta

from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.decorators import action

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core.models import (
    CycleEntry, SymptomEntry, NutritionEntry, Notification, 
    AdviceMessage, LibraryResource
)
from core.ml_service import analyze_health_data
from .renderers import EnvelopeJSONRenderer
from .serializers import (
    CycleEntrySerializer, SymptomEntrySerializer, NutritionEntrySerializer,
    NotificationSerializer, AdviceMessageSerializer, SignupSerializer, 
    ProfileUpdateSerializer, ChangePasswordSerializer, LibraryArticleSerializer
)

# --- Section 1: Authentication & JWT ---

class CustomTokenObtainPairView(TokenObtainPairView):
    """POST /api/v1/auth/login/"""
    renderer_classes = [EnvelopeJSONRenderer]

class CustomTokenRefreshView(TokenRefreshView):
    """POST /api/v1/auth/refresh/"""
    renderer_classes = [EnvelopeJSONRenderer]

class SignupView(APIView):
    """POST /api/v1/auth/signup/"""
    permission_classes = [AllowAny]
    renderer_classes = [EnvelopeJSONRenderer]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                "user_id": user.id,
                "username": user.username,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(generics.RetrieveUpdateAPIView):
    """GET and PATCH /api/v1/auth/profile/"""
    permission_classes = [IsAuthenticated]
    renderer_classes = [EnvelopeJSONRenderer]
    serializer_class = ProfileUpdateSerializer

    def get_object(self):
        return self.request.user.adolescent_profile

class ChangePasswordView(APIView):
    """POST /api/v1/auth/change-password/"""
    permission_classes = [IsAuthenticated]
    renderer_classes = [EnvelopeJSONRenderer]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"message": "Password updated successfully."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    """POST /api/v1/auth/logout/"""
    permission_classes = [IsAuthenticated]
    renderer_classes = [EnvelopeJSONRenderer]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Successfully logged out."})
        except Exception as e:
            return Response({"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)


# --- Section 2: Menstrual Cycle & Symptom Tracking ---

class CycleViewSet(viewsets.ModelViewSet):
    """CRUD for Cycles and custom actions for starting/ending periods."""
    serializer_class = CycleEntrySerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [EnvelopeJSONRenderer]

    def get_queryset(self):
        return CycleEntry.objects.filter(
            profile=self.request.user.adolescent_profile
        ).order_by('-start_date')

    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.adolescent_profile)

    @action(detail=False, methods=['post'])
    def start(self, request):
        profile = request.user.adolescent_profile
        active = CycleEntry.objects.filter(profile=profile, end_date__isnull=True).first()
        
        if active:
            return Response({"error": "A cycle is already active."}, status=status.HTTP_400_BAD_REQUEST)
        
        start_date = request.data.get('start_date', date.today().isoformat())
        flow = request.data.get('flow_intensity', 'Medium')
        
        cycle = CycleEntry.objects.create(profile=profile, start_date=start_date, flow_intensity=flow)
        return Response(CycleEntrySerializer(cycle).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def end(self, request):
        profile = request.user.adolescent_profile
        active = CycleEntry.objects.filter(profile=profile, end_date__isnull=True).first()
        
        if not active:
            return Response({"error": "No active cycle found to end."}, status=status.HTTP_400_BAD_REQUEST)
        
        end_date = request.data.get('end_date', date.today().isoformat())
        active.end_date = end_date
        active.save()
        return Response(CycleEntrySerializer(active).data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        profile = request.user.adolescent_profile
        active = CycleEntry.objects.filter(profile=profile, end_date__isnull=True).first()
        
        if not active:
            return Response({"is_active": False, "days_in": 0})
            
        days_in = (date.today() - active.start_date).days + 1
        data = CycleEntrySerializer(active).data
        data.update({"is_active": True, "days_in": days_in})
        return Response(data)

class SymptomViewSet(viewsets.ModelViewSet):
    """CRUD for daily symptom logging."""
    serializer_class = SymptomEntrySerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [EnvelopeJSONRenderer]

    def get_queryset(self):
        return SymptomEntry.objects.filter(
            profile=self.request.user.adolescent_profile
        ).order_by('-date')

    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.adolescent_profile)


# --- Section 3: ML Model Integration ---

class MLRiskAssessmentView(APIView):
    """GET /api/v1/ml/assess/"""
    permission_classes = [IsAuthenticated]
    renderer_classes = [EnvelopeJSONRenderer]

    def get(self, request):
        profile = request.user.adolescent_profile
        
        cycles = list(CycleEntry.objects.filter(profile=profile).order_by('-start_date')[:6])
        symptoms = list(SymptomEntry.objects.filter(profile=profile).order_by('-date')[:15])

        ml_report = analyze_health_data(cycles, symptoms)

        avg_cycle_len = 28
        if len(cycles) >= 2:
            lengths = [(cycles[i].start_date - cycles[i+1].start_date).days for i in range(len(cycles)-1)]
            avg_cycle_len = sum(lengths) // len(lengths)

        next_period_date = None
        if cycles:
            next_period_date = cycles[0].start_date + timedelta(days=avg_cycle_len)

        suggestions = ["Ensure you are drinking 8 glasses of water daily."]
        if ml_report.get("anemia_risk") in ["Moderate", "High"]:
            suggestions.append("Your risk profile suggests prioritizing iron-rich meals today.")
        if next_period_date and (next_period_date - date.today()).days <= 3:
            suggestions.append("Your period is approaching. Rest up and keep tracking your mood.")

        return Response({
            "anemia_risk": ml_report.get("anemia_risk", "Low"),
            "risk_score": 2 if ml_report.get("anemia_risk") == "High" else (1 if ml_report.get("anemia_risk") == "Moderate" else 0),
            "insights": ml_report.get("insights", []),
            "predictions": {
                "expected_cycle_length": avg_cycle_len,
                "next_period_date": next_period_date.isoformat() if next_period_date else None
            },
            "suggestions": suggestions
        })


# --- Section 4: Stats & Analytics ---

class StatsAnalyticsView(APIView):
    """GET /api/v1/stats/summary/"""
    permission_classes = [IsAuthenticated]
    renderer_classes = [EnvelopeJSONRenderer]

    def get(self, request):
        profile = request.user.adolescent_profile
        
        cycles = CycleEntry.objects.filter(profile=profile).order_by('-start_date')
        total_cycles = cycles.count()
        
        cycle_trends = []
        total_period_duration = 0
        completed_periods = 0
        total_cycle_length = 0
        valid_cycle_links = 0

        cycles_list = list(cycles)
        for i, cycle in enumerate(cycles_list):
            period_duration = None
            if cycle.end_date:
                period_duration = (cycle.end_date - cycle.start_date).days
                total_period_duration += period_duration
                completed_periods += 1

            cycle_length = None
            if i > 0:
                cycle_length = (cycles_list[i-1].start_date - cycle.start_date).days
                total_cycle_length += cycle_length
                valid_cycle_links += 1

            cycle_trends.append({
                "cycle_id": cycle.id,
                "start_date": cycle.start_date.isoformat(),
                "period_duration": period_duration,
                "cycle_length": cycle_length
            })

        avg_period = round(total_period_duration / completed_periods) if completed_periods > 0 else 0
        avg_cycle = round(total_cycle_length / valid_cycle_links) if valid_cycle_links > 0 else 28

        symptoms_query = SymptomEntry.objects.filter(profile=profile) \
            .values('symptom_type') \
            .annotate(count=Count('id')) \
            .order_by('-count')
            
        most_frequent = [s['symptom_type'] for s in symptoms_query[:3]]

        streak = 0
        check_date = date.today()
        logged_dates = set(SymptomEntry.objects.filter(profile=profile).values_list('date', flat=True))
        
        while check_date in logged_dates:
            streak += 1
            check_date -= timedelta(days=1)

        four_weeks_ago = date.today() - timedelta(weeks=4)
        nutrition_logs = NutritionEntry.objects.filter(
            profile=profile, date__gte=four_weeks_ago
        ).order_by('date')
        
        nutrition_trend = [{"date": n.date.isoformat(), "score": n.score} for n in nutrition_logs]

        data = {
            "summary": {
                "total_cycles": total_cycles,
                "average_cycle_length": avg_cycle,
                "average_period_duration": avg_period,
                "most_frequent_symptoms": most_frequent,
                "current_streak_days": streak
            },
            "charts": {
                "cycle_trends": cycle_trends,
                "symptom_frequency": list(symptoms_query),
                "nutrition_history": nutrition_trend,
                "risk_trend": [] 
            }
        }
        return Response(data)


# --- Section 5 & 6: Notifications and Advice ---

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [EnvelopeJSONRenderer]

    def get_queryset(self):
        return Notification.objects.filter(
            profile=self.request.user.adolescent_profile
        ).order_by('is_read', '-created_at')

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().update(is_read=True)
        return Response({"message": "All notifications marked as read."})

class AdviceMessageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AdviceMessageSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [EnvelopeJSONRenderer]

    def get_queryset(self):
        return AdviceMessage.objects.filter(
            profile=self.request.user.adolescent_profile
        ).order_by('created_at')


# --- Section 7: Library (CHW Articles) ---

class LibraryArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/v1/library/ - Lists and retrieves published CHW articles."""
    serializer_class = LibraryArticleSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [EnvelopeJSONRenderer]

    def get_queryset(self):
        queryset = LibraryResource.objects.filter(is_published=True).order_by('-created_at')
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(topic__iexact=category)
        return queryset

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        article = self.get_object()
        return Response({
            "message": f"Article '{article.title}' marked as read locally."
        }, status=status.HTTP_200_OK)


# --- Section 8: Sync Engine ---

class SyncStatusView(APIView):
    """GET /api/v1/sync/status/"""
    permission_classes = [IsAuthenticated]
    renderer_classes = [EnvelopeJSONRenderer]

    def get(self, request):
        last_sync_str = request.query_params.get('last_sync_time')
        profile = request.user.adolescent_profile
        
        pending_changes = 0
        if last_sync_str:
            last_sync = parse(last_sync_str)
            pending_changes += CycleEntry.objects.filter(profile=profile, last_modified__gt=last_sync).count()
            pending_changes += SymptomEntry.objects.filter(profile=profile, last_modified__gt=last_sync).count()
            pending_changes += AdviceMessage.objects.filter(profile=profile, last_modified__gt=last_sync).count()
            pending_changes += Notification.objects.filter(profile=profile, last_modified__gt=last_sync).count()

        return Response({
            "last_successful_sync": last_sync_str,
            "pending_server_changes": pending_changes
        })

class SyncDataView(APIView):
    """POST /api/v1/sync/"""
    permission_classes = [IsAuthenticated]
    renderer_classes = [EnvelopeJSONRenderer]

    @transaction.atomic
    def post(self, request):
        last_sync_time_str = request.data.get('last_sync_time')
        client_changes = request.data.get('changes', {})
        profile = request.user.adolescent_profile
        
        last_sync_time = parse(last_sync_time_str) if last_sync_time_str else None
        current_server_time = timezone.now()

        # 1. PROCESS CLIENT TO SERVER CHANGES
        self._sync_model(CycleEntry, client_changes.get('cycles', []), profile)
        self._sync_model(SymptomEntry, client_changes.get('symptoms', []), profile)
        self._sync_model(NutritionEntry, client_changes.get('nutrition', []), profile)

        # 2. GATHER SERVER TO CLIENT UPDATES
        updates = {}
        if last_sync_time:
            server_cycles = CycleEntry.objects.filter(profile=profile, last_modified__gt=last_sync_time)
            server_symptoms = SymptomEntry.objects.filter(profile=profile, last_modified__gt=last_sync_time)
            server_nutrition = NutritionEntry.objects.filter(profile=profile, last_modified__gt=last_sync_time)
            server_advice = AdviceMessage.objects.filter(profile=profile, last_modified__gt=last_sync_time)
            server_notifs = Notification.objects.filter(profile=profile, last_modified__gt=last_sync_time)
        else:
            server_cycles = CycleEntry.objects.filter(profile=profile)
            server_symptoms = SymptomEntry.objects.filter(profile=profile)
            server_nutrition = NutritionEntry.objects.filter(profile=profile)
            server_advice = AdviceMessage.objects.filter(profile=profile)
            server_notifs = Notification.objects.filter(profile=profile)

        updates['cycles'] = CycleEntrySerializer(server_cycles, many=True).data
        updates['symptoms'] = SymptomEntrySerializer(server_symptoms, many=True).data
        updates['nutrition'] = NutritionEntrySerializer(server_nutrition, many=True).data
        updates['advice'] = AdviceMessageSerializer(server_advice, many=True).data
        updates['notifications'] = NotificationSerializer(server_notifs, many=True).data

        return Response({
            "new_last_sync_time": current_server_time.isoformat(),
            "updates": updates
        })

    def _sync_model(self, model_class, client_records, profile):
        for record in client_records:
            record_id = record.get('id')
            client_modified_str = record.get('last_modified')
            if not client_modified_str:
                continue
                
            client_modified = parse(client_modified_str)

            try:
                db_instance = model_class.objects.get(id=record_id, profile=profile)
                if db_instance.last_modified > client_modified:
                    continue 
                
                for key, value in record.items():
                    if key not in ['id', 'last_modified', 'profile']:
                        setattr(db_instance, key, value)
                db_instance.save()

            except model_class.DoesNotExist:
                record.pop('last_modified', None)
                model_class.objects.create(profile=profile, **record)