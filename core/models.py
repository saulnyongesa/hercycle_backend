from datetime import date
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    is_chv = models.BooleanField(default=False)
    is_adolescent = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)  # For CHVs, indicates if admin has approved the account

class CHVProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='chv_profile')
    organization = models.CharField(max_length=255, blank=True)
    is_approved = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True, null=True)
    last_modified = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f"CHV: {self.user.username}"


class AdolescentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='adolescent_profile')
    chv = models.ForeignKey(CHVProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_girls')
    anonymous_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    date_of_birth = models.DateField(null=True, blank=True) 
    date_joined = models.DateTimeField(auto_now_add=True, null=True)
    last_modified = models.DateTimeField(auto_now=True, null=True)

    @property
    def age(self):
        """Dynamically calculates age based on DOB."""
        if not self.date_of_birth:
            return None
        today = date.today()
        # Subtracts 1 year if the current month/day is before their birth month/day
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

    def __str__(self):
        return f"Girl ID: {self.anonymous_id}"

class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    last_modified = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True

class CHVNote(BaseModel):
    profile = models.ForeignKey(AdolescentProfile, on_delete=models.CASCADE, related_name='chv_notes')
    chv = models.ForeignKey(CHVProfile, on_delete=models.SET_NULL, null=True)
    note = models.TextField()

    class Meta:
        ordering = ['-last_modified']

class CycleEntry(BaseModel):
    profile = models.ForeignKey(AdolescentProfile, on_delete=models.CASCADE, related_name='cycles')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    flow_intensity = models.CharField(max_length=50)

class SymptomEntry(BaseModel):
    profile = models.ForeignKey(AdolescentProfile, on_delete=models.CASCADE, related_name='symptoms')
    date = models.DateField()
    symptom_type = models.CharField(max_length=100)
    severity = models.IntegerField(default=1)