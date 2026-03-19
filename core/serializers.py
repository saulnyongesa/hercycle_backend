from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import AdolescentProfile, AdviceMessage, CHVNote, CHVProfile, CycleEntry, LibraryResource, SymptomEntry

User = get_user_model()

class CycleEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = CycleEntry
        fields = ['id', 'start_date', 'end_date', 'flow_intensity', 'last_modified', 'is_deleted']
        read_only_fields = ['last_modified']

class SymptomEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = SymptomEntry
        fields = ['id', 'date', 'symptom_type', 'severity', 'last_modified', 'is_deleted']
        read_only_fields = ['last_modified']

class CHVNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CHVNote
        fields = ['id', 'note', 'last_modified']

class AdolescentProfileSerializer(serializers.ModelSerializer):
    cycles = CycleEntrySerializer(many=True, read_only=True)
    symptoms = SymptomEntrySerializer(many=True, read_only=True)
    chv_notes = CHVNoteSerializer(many=True, read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    age = serializers.IntegerField(read_only=True) # <--- Explicitly expose the calculated property

    class Meta:
        model = AdolescentProfile
        fields = ['anonymous_id', 'username', 'date_of_birth', 'age', 'cycles', 'symptoms', 'chv_notes']


class CHVOnboardUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    date_of_birth = serializers.DateField(write_only=True, required=True) # <--- Require DOB on signup

    class Meta:
        model = User
        fields = ['username', 'password', 'date_of_birth']

    def create(self, validated_data):
        # Extract the DOB before creating the base user
        dob = validated_data.pop('date_of_birth')
        
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            is_adolescent=True
        )
        chv_profile = self.context['request'].user.chv_profile
        # Pass the DOB to the adolescent profile
        AdolescentProfile.objects.create(user=user, chv=chv_profile, date_of_birth=dob)
        return user

class SelfRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            is_adolescent=True
        )
        AdolescentProfile.objects.create(user=user, chv=None)
        return user

class CHVProfileSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = CHVProfile
        fields = ['id', 'user_username', 'organization', 'is_approved', 'date_joined', 'last_modified']

class LibraryResourceSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    topic_display = serializers.CharField(source='get_topic_display', read_only=True)
    
    class Meta:
        model = LibraryResource
        fields = [
            'id', 'topic', 'topic_display', 'title', 'content', 
            'is_published', 'created_by_username', 'created_at', 'updated_at'
        ]

class  AdviceMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(read_only=True)
    sender_type = serializers.CharField(read_only=True)

    class Meta:
        model = AdviceMessage
        fields = ['id', 'message', 'sender_name', 'sender_type', 'created_at', 'is_read']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Dynamically determine sender name and type based on the message's sender
        if instance.sender_type == 'chv' and instance.profile.chv:
            data['sender_name'] = instance.profile.chv.user.username
            data['sender_type'] = 'CHV'
        else:
            data['sender_name'] = 'System'
            data['sender_type'] = 'System'
