from rest_framework import serializers
from core.models import CycleEntry, LibraryResource, SymptomEntry, Notification, AdviceMessage, NutritionEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from core.models import AdolescentProfile
import re
from django.utils.html import strip_tags

User = get_user_model()

class MobileBaseSerializer(serializers.ModelSerializer):
    """Ensures all mobile payloads include the sync fields"""
    class Meta:
        abstract = True
        fields = ['id', 'last_modified', 'is_deleted']

class CycleEntrySerializer(MobileBaseSerializer):
    class Meta(MobileBaseSerializer.Meta):
        model = CycleEntry
        fields = MobileBaseSerializer.Meta.fields + ['start_date', 'end_date', 'flow_intensity']

class SymptomEntrySerializer(MobileBaseSerializer):
    class Meta(MobileBaseSerializer.Meta):
        model = SymptomEntry
        fields = MobileBaseSerializer.Meta.fields + ['date', 'symptom_type', 'severity']

class NutritionEntrySerializer(MobileBaseSerializer):
    class Meta(MobileBaseSerializer.Meta):
        model = NutritionEntry
        fields = MobileBaseSerializer.Meta.fields + ['date', 'score', 'notes']

class NotificationSerializer(MobileBaseSerializer):
    class Meta(MobileBaseSerializer.Meta):
        model = Notification
        fields = MobileBaseSerializer.Meta.fields + ['type', 'title', 'message', 'is_read', 'created_at']

class AdviceMessageSerializer(MobileBaseSerializer):
    class Meta(MobileBaseSerializer.Meta):
        model = AdviceMessage
        fields = MobileBaseSerializer.Meta.fields + ['sender_type', 'sender_name', 'message', 'is_read', 'created_at']


class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    date_of_birth = serializers.DateField()
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        # 1. Password Matching & Strength
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        
        try:
            validate_password(data['password'])
        except Exception as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        # 2. Email Uniqueness
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "This email is already in use."})

        # 3. Username Logic (Spaces allowed, but handle duplicates with suggestions)
        username = data['username']
        if User.objects.filter(username=username).exists():
            # Generate clean suggestions if taken
            clean_base = re.sub(r'[^a-zA-Z0-9]', '', username.lower())
            suggestions = [
                f"{clean_base}_{data['date_of_birth'].year}",
                f"{clean_base}123",
                f"{username.replace(' ', '_')}"
            ]
            raise serializers.ValidationError({
                "username": f"Username taken. Suggestions: {', '.join(suggestions)}"
            })

        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            is_adolescent=True
        )
        # Create the linked profile with DOB
        AdolescentProfile.objects.create(
            user=user,
            date_of_birth=validated_data['date_of_birth']
        )
        return user

class ProfileUpdateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email')
    
    class Meta:
        model = AdolescentProfile
        fields = ['username', 'email', 'date_of_birth'] # Add 'weight', 'height' if added to model

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user

        if 'username' in user_data:
            user.username = user_data['username']
        if 'email' in user_data:
            user.email = user_data['email']
        user.save()

        instance.date_of_birth = validated_data.get('date_of_birth', instance.date_of_birth)
        # instance.weight = validated_data.get('weight', instance.weight)
        instance.save()
        
        return instance

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value
    
class LibraryArticleSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='created_by.username', read_only=True)
    published_date = serializers.DateTimeField(source='created_at', read_only=True)
    category = serializers.CharField(source='topic', read_only=True)
    summary = serializers.SerializerMethodField()
    
    class Meta:
        model = LibraryResource
        fields = ['id', 'title', 'summary', 'content', 'author', 'published_date', 'category']
        
    def get_summary(self, obj):
        """Strips HTML tags and truncates to 150 characters for the list view."""
        if not obj.content:
            return ""
        clean_text = strip_tags(obj.content)
        return clean_text[:150] + "..." if len(clean_text) > 150 else clean_text