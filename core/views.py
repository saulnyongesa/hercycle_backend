import csv
from datetime import date
import json

from django.contrib.auth.decorators import login_required
from rest_framework.decorators import action
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db import transaction
from rest_framework import filters
from rest_framework import generics, viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from dateutil.parser import parse
from django.contrib.admin.views.decorators import staff_member_required
from .models import AdolescentProfile, CHVProfile, CycleEntry, LibraryResource, SymptomEntry, User, AdviceMessage, CHVNote
from .serializers import (
    CHVProfileSerializer,
    LibraryResourceSerializer,
    SelfRegisterSerializer, 
    CHVOnboardUserSerializer, 
    AdolescentProfileSerializer,
    CycleEntrySerializer,
    SymptomEntrySerializer,
    AdviceMessageSerializer
)
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from .ml_service import analyze_health_data


# --- LANDING PAGE VIEW ---
@ensure_csrf_cookie
def chv_landing_view(request):
    """Renders the landing page. Redirects to dashboard if already logged in."""
    if request.user.is_authenticated and hasattr(request.user, 'chv_profile'):
        return redirect('chv-dashboard')
    return render(request, 'core/chv_landing.html')

# --- CHV AJAX AUTHENTICATION ACTIONS ---
def chv_login_action(request):
    """Handles standard Django session login with multi-role routing."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # 1. Check for Admin/Staff Access first
                if user.is_staff or user.is_superuser:
                    login(request, user)
                    return JsonResponse({
                        "success": True, 
                        "redirect": "/admin-dashboard/",
                        "message": "Welcome to the Admin Command Center."
                    })

                # 2. Check for CHV Access
                if hasattr(user, 'chv_profile'):
                    if user.chv_profile.is_approved:
                        login(request, user)
                        return JsonResponse({
                            "success": True, 
                            "redirect": "/dashboard/",
                            "message": "Login successful."
                        })
                    else:
                        return JsonResponse({
                            "error": "Account pending admin approval. Please wait to be vetted."
                        }, status=403)
                
                # 3. Deny if user is an Adolescent (they use the Mobile App only)
                return JsonResponse({
                    "error": "Access denied. Please use the HerCycle Mobile App."
                }, status=403)

            return JsonResponse({"error": "Invalid username or password."}, status=401)
            
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
            
    return JsonResponse({"error": "Method not allowed"}, status=405)

def chv_register_action(request):
    """Handles CHV registration via AJAX. Defaults is_approved to False."""
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        organization = data.get('organization', '')
        
        from django.contrib.auth import get_user_model
        User = get_user_model()

        if User.objects.filter(username=username).exists():
            return JsonResponse({"error": "Username is already taken."}, status=400)
        
        # Create user and link CHV profile
        user = User.objects.create_user(username=username, password=password, is_chv=True)
        from .models import CHVProfile
        CHVProfile.objects.create(user=user, organization=organization, is_approved=False)
        
        return JsonResponse({
            "success": True, 
            "message": "Registration successful! Your account is pending admin approval."
        })
    return JsonResponse({"error": "Invalid request method"}, status=400)

def chv_logout_action(request):
    """Logs the user out and redirects to the custom landing page."""
    logout(request)
    return redirect('chv-landing')
# --- WEB DASHBOARD VIEW ---
@login_required
def chv_dashboard_view(request):
    if not hasattr(request.user, 'chv_profile') or not request.user.chv_profile.is_approved:
        raise PermissionDenied("You are not an approved Community Health Volunteer.")
    return render(request, 'core/chv_dashboard.html')


@staff_member_required # Strictly restricts to users with is_staff=True
def admin_dashboard_view(request):
    # Total system stats
    stats = {
        'total_girls': AdolescentProfile.objects.count(),
        'total_chvs': CHVProfile.objects.count(),
        'pending_chvs': CHVProfile.objects.filter(is_approved=False).count(),
        'total_cycles': CycleEntry.objects.count(),
        'total_symptoms': SymptomEntry.objects.count(),
    }
    return render(request, 'core/admin_dashboard.html', {'stats': stats})

# CSV Export for Admin (All Data)
@staff_member_required
def admin_export_all_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="hercycle_master_report.csv"'
    writer = csv.writer(response)
    
    writer.writerow(['Global Report', date.today()])
    writer.writerow(['User ID', 'Role', 'Organization', 'Status', 'Date Joined'])
    
    for user in User.objects.all():
        role = "CHV" if user.is_chv else "Adolescent"
        org = user.chv_profile.organization if user.is_chv else "N/A"
        writer.writerow([user.username, role, org, user.is_active, user.date_joined])
        
    return response
class AdminCHVManagementViewSet(viewsets.ModelViewSet):
    serializer_class = CHVProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return CHVProfile.objects.all().order_by('-date_joined')
        return CHVProfile.objects.none()

    @action(detail=True, methods=['post'])
    def toggle_approval(self, request, pk=None):
        chv = self.get_object()
        chv.is_approved = not chv.is_approved
        chv.save()
        return Response({'status': 'success', 'is_approved': chv.is_approved})

    # Action to delete a CHV and their associated User account
    @action(detail=True, methods=['delete'])
    def remove_chv(self, request, pk=None):
        chv = self.get_object()
        user = chv.user
        user.delete() # This deletes the profile too via CASCADE
        return Response(status=status.HTTP_204_NO_CONTENT)
# --- 1. CSV EXPORT VIEW ---
@login_required
def export_dashboard_csv(request):
    """Generates a unified CSV with Summary Stats at the top, and User Data below."""
    if not hasattr(request.user, 'chv_profile'):
        raise PermissionDenied("Not authorized.")
        
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="hercycle_report.csv"'
    writer = csv.writer(response)

    chv = request.user.chv_profile
    users = AdolescentProfile.objects.filter(chv=chv)

    # Calculate some quick stats
    total_users = users.count()
    total_cycles = sum([u.cycles.count() for u in users])
    total_symptoms = sum([u.symptoms.count() for u in users])

    # Write Stats Section
    writer.writerow(['--- HERCYCLE CHV SUMMARY STATS ---'])
    writer.writerow(['Total Managed Girls', total_users])
    writer.writerow(['Total Logged Cycles', total_cycles])
    writer.writerow(['Total Logged Symptoms', total_symptoms])
    writer.writerow([]) # Blank row spacer

    # Write Data Section
    writer.writerow(['--- DETAILED USER DATA ---'])
    writer.writerow(['Anonymous ID', 'Username', 'Age', 'Cycle Count', 'Symptom Count', 'Risk Level'])
    
    from .ml_service import analyze_health_data
    for u in users:
        cycles = u.cycles.filter(is_deleted=False)
        symptoms = u.symptoms.filter(is_deleted=False)
        report = analyze_health_data(cycles, symptoms)
        
        writer.writerow([
            str(u.anonymous_id), 
            u.user.username, 
            u.age or 'N/A', 
            cycles.count(), 
            symptoms.count(), 
            report['anemia_risk']
        ])

    return response


# --- API VIEWS ---
class SelfRegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = SelfRegisterSerializer

# --- 1. NEW HTML VIEW FOR DETAIL PAGE ---
@login_required(redirect_field_name='chv-landing')
def chv_user_detail_view(request, anonymous_id):
    user = request.user
    
    # Check if the user is an Admin (staff) 
    # OR an approved CHV
    is_admin = user.is_staff or user.is_superuser
    is_approved_chv = hasattr(user, 'chv_profile') and user.chv_profile.is_approved

    if not (is_admin or is_approved_chv):
        raise PermissionDenied("You do not have permission to view this girl's insights.")

    # We pass the ID to the template so JS can use it to fetch the data
    return render(request, 'core/chv_user_detail.html', {'anonymous_id': anonymous_id})

# --- 2. UPDATE YOUR VIEWSET ---
class CHVManagedUsersViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    lookup_field = 'anonymous_id' # IMPORTANT: Tell DRF to look up users by their UUID
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__username', 'anonymous_id'] # Search girls by name or UUID

    def get_queryset(self):
        user = self.request.user
        # If Admin, return EVERYTHING
        if user.is_staff or user.is_superuser:
            return AdolescentProfile.objects.all().order_by('-id')
        
        # If regular CHV, return only their assigned girls
        if hasattr(user, 'chv_profile'):
            return AdolescentProfile.objects.filter(chv=user.chv_profile).order_by('-id')
            
        return AdolescentProfile.objects.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return CHVOnboardUserSerializer
        return AdolescentProfileSerializer

    # Overriding the 'retrieve' method to inject the ML analysis
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

        # Standard Health Data (Untouched)
        cycles = instance.cycles.filter(is_deleted=False).order_by('-start_date')
        symptoms = instance.symptoms.filter(is_deleted=False).order_by('-date')
        data['ml_report'] = analyze_health_data(cycles, symptoms)
        
        # Advice Section (Updated to use the fixed Serializer)
        advice = instance.advice_messages.all().order_by('-created_at')
        data['advice_messages'] = AdviceMessageSerializer(advice, many=True).data
        return Response(data)

    @action(detail=True, methods=['post'])
    def add_note(self, request, anonymous_id=None):
        profile = self.get_object()
        note_text = request.data.get('note')
        if not note_text:
            return Response({"error": "Note cannot be empty"}, status=400)

        AdviceMessage.objects.create(
            profile=profile,
            sender_type='chw',
            sender_name=f"CHV {request.user.username}",
            message=note_text
        )
        return Response({"status": "Success"}, status=201)

    @action(detail=False, methods=['patch'], url_path='edit-advice/(?P<advice_id>[^/.]+)')
    def edit_advice(self, request, advice_id=None):
        advice = AdviceMessage.objects.filter(id=advice_id).first()
        if not advice:
            return Response({"error": "Advice not found"}, status=404)
        
        advice.message = request.data.get('message', advice.message)
        advice.save()
        return Response({"status": "Updated"})

    @action(detail=False, methods=['delete'], url_path='delete-advice/(?P<advice_id>[^/.]+)')
    def delete_advice(self, request, advice_id=None):
        AdviceMessage.objects.filter(id=advice_id).delete()
        return Response(status=204)
    
    def destroy(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response({"error": "Only admins can delete girls"}, status=403)
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_details(self, request, anonymous_id=None):
        profile = self.get_object()
        user_account = profile.user

        new_username = request.data.get('username')
        new_dob = request.data.get('date_of_birth')

        # 1. Update Username if provided and changed
        if new_username and new_username != user_account.username:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            if User.objects.filter(username=new_username).exists():
                return Response({"error": "This username is already taken."}, status=status.HTTP_400_BAD_REQUEST)
            user_account.username = new_username
            user_account.save()

        # 2. Update Date of Birth if provided
        if new_dob:
            profile.date_of_birth = new_dob
            profile.save()

        return Response({
            "status": "Profile updated successfully!",
            "username": user_account.username,
            "date_of_birth": profile.date_of_birth
        }, status=status.HTTP_200_OK)

class SyncDataView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        last_sync_time_str = request.data.get('last_sync_time')
        client_changes = request.data.get('changes', {})
        last_sync_time = parse(last_sync_time_str) if last_sync_time_str else None
        
        try:
            user_profile = request.user.adolescent_profile
        except AdolescentProfile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=status.HTTP_400_BAD_REQUEST)

        # App -> Server sync
        for cycle_data in client_changes.get('cycles', []):
            CycleEntry.objects.update_or_create(
                id=cycle_data['id'],
                profile=user_profile,
                defaults={
                    'start_date': cycle_data['start_date'],
                    'end_date': cycle_data.get('end_date'),
                    'flow_intensity': cycle_data['flow_intensity'],
                    'is_deleted': cycle_data.get('is_deleted', False),
                }
            )

        for symptom_data in client_changes.get('symptoms', []):
            SymptomEntry.objects.update_or_create(
                id=symptom_data['id'],
                profile=user_profile,
                defaults={
                    'date': symptom_data['date'],
                    'symptom_type': symptom_data['symptom_type'],
                    'severity': symptom_data['severity'],
                    'is_deleted': symptom_data.get('is_deleted', False),
                }
            )

        # Server -> App sync
        server_updates = {'cycles': [], 'symptoms': []}
        if last_sync_time:
            updated_cycles = CycleEntry.objects.filter(profile=user_profile, last_modified__gt=last_sync_time)
            updated_symptoms = SymptomEntry.objects.filter(profile=user_profile, last_modified__gt=last_sync_time)
            server_updates['cycles'] = CycleEntrySerializer(updated_cycles, many=True).data
            server_updates['symptoms'] = SymptomEntrySerializer(updated_symptoms, many=True).data
        else:
            server_updates['cycles'] = CycleEntrySerializer(CycleEntry.objects.filter(profile=user_profile), many=True).data
            server_updates['symptoms'] = SymptomEntrySerializer(SymptomEntry.objects.filter(profile=user_profile), many=True).data

        return Response({
            'updates': server_updates,
            'current_server_time': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
    

# --- HTML View ---
@login_required(login_url='chv-landing')
def library_view(request):
    """
    Stand-alone Library Management Page.
    Only accessible by Staff or Approved CHVs.
    """
    user = request.user
    is_approved_chv = hasattr(user, 'chv_profile') and user.chv_profile.is_approved
    
    if not (user.is_staff or is_approved_chv):
        # Redirect unauthorized users (like Adolescents) back to landing or raise error
        return redirect('chv-landing')
        
    return render(request, 'core/library.html')

# --- API Viewset ---
class LibraryResourceViewSet(viewsets.ModelViewSet):
    queryset = LibraryResource.objects.all().order_by('-created_at')
    serializer_class = LibraryResourceSerializer
    # 1. Ensure user is logged in for all API calls
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Optional: If you want girls to see only 'published' articles 
        but CHVs to see everything.
        """
        user = self.request.user
        if user.is_staff or (hasattr(user, 'chv_profile') and user.chv_profile.is_approved):
            return LibraryResource.objects.all().order_by('-created_at')
        
        # Adolescents only see published content
        return LibraryResource.objects.filter(is_published=True).order_by('-created_at')

    def perform_create(self, serializer):
        # 2. Attach the logged-in user as the author
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def toggle_publish(self, request, pk=None):
        # 3. Extra Security: Only authors or staff can publish/unpublish
        resource = self.get_object()
        if not (request.user.is_staff or resource.created_by == request.user):
            return Response({"error": "Not authorized to change status"}, status=403)
            
        resource.is_published = not resource.is_published
        resource.save()
        return Response({'status': 'success', 'is_published': resource.is_published})