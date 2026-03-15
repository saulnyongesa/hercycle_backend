import random
from datetime import timedelta, date
from django.contrib.auth import get_user_model
from core.models import CHVProfile, AdolescentProfile, CycleEntry, SymptomEntry

User = get_user_model()

# Authentic Kenyan Names
FIRST_NAMES = ['Wanjiku', 'Akinyi', 'Muthoni', 'Achieng', 'Njeri', 'Nekesa', 'Moraa', 'Nyambura', 'Atieno', 'Nasimiyu', 'Kendi', 'Chebet', 'Wamalwa', 'Kwamboka', 'Auma', 'Zari', 'Makena', 'Hadassah']
LAST_NAMES = ['Kamau', 'Ochieng', 'Mwangi', 'Odhiambo', 'Ndung\'u', 'Wanjala', 'Onyango', 'Mutua', 'Kariuki', 'Kipkorir', 'Ouma', 'Macharia', 'Barasa', 'Wekesa', 'Otieno', 'Maina', 'Karanja']

# TARGET CHV USERNAME
TARGET_CHV_USERNAME = "REAGAN OLUOCH"

print(f"Searching for CHV with username: {TARGET_CHV_USERNAME}...")
chv_profile = CHVProfile.objects.filter(user__username=TARGET_CHV_USERNAME).first()

if not chv_profile:
    print(f"ERROR: CHV '{TARGET_CHV_USERNAME}' not found! Please ensure this user exists and is a CHV.")
else:
    print(f"Assigning 1000 women (reproductive age 15-45) to CHV: {chv_profile.user.username}")
    print("Populating database... this may take a moment.")
    created_count = 0

    for i in range(1000):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        # Unique username generation
        username = f"{first_name.lower()}_{last_name.lower()}_{random.randint(10000, 999999)}"

        if User.objects.filter(username=username).exists():
            continue

        # 1. Create User Account
        user = User.objects.create_user(
            username=username, 
            password='password123', 
            is_adolescent=True # Using the existing boolean for tracking users
        )

        # 2. Create Profile (Reproductive Age: 15 to 45)
        age = random.randint(15, 45)
        days_old = age * 365 + random.randint(0, 364)
        dob = date.today() - timedelta(days=days_old)
        
        profile = AdolescentProfile.objects.create(
            user=user, 
            chv=chv_profile, 
            date_of_birth=dob
        )

        # 3. Generate Historical Cycle Data (Last 4-6 months)
        num_cycles = random.randint(3, 6)
        current_date = date.today() - timedelta(days=random.randint(2, 15))

        for _ in range(num_cycles):
            # Normal cycle variation: 24 to 38 days for reproductive age
            cycle_length = random.randint(24, 38)
            bleeding_days = random.randint(3, 8)
            
            start_date = current_date - timedelta(days=cycle_length)
            end_date = start_date + timedelta(days=bleeding_days)
            
            # Flow distribution
            flow = random.choices(['Light', 'Medium', 'Heavy'], weights=[15, 60, 25])[0]

            CycleEntry.objects.create(
                profile=profile, 
                start_date=start_date, 
                end_date=end_date, 
                flow_intensity=flow
            )

            # 4. Generate Symptoms
            symptom_types = ['Cramps', 'Fatigue', 'Headache', 'Dizziness', 'Pale Skin', 'Mood Swings', 'Bloating', 'Backache']
            
            # Risk pattern: Heavy flow linked to anemia symptoms
            if flow == 'Heavy':
                SymptomEntry.objects.create(
                    profile=profile, 
                    date=start_date + timedelta(days=random.randint(1, 3)),
                    symptom_type=random.choice(['Fatigue', 'Dizziness', 'Pale Skin']), 
                    severity=random.randint(3, 5)
                )

            # General symptoms
            for _ in range(random.randint(0, 3)):
                SymptomEntry.objects.create(
                    profile=profile, 
                    date=start_date + timedelta(days=random.randint(0, bleeding_days)),
                    symptom_type=random.choice(symptom_types), 
                    severity=random.randint(1, 4)
                )

            current_date = start_date # Iterate backwards

        created_count += 1
        
        if created_count % 100 == 0:
            print(f"... generated {created_count} / 1000 women")

    print(f"SUCCESS! Created {created_count} users for CHV {TARGET_CHV_USERNAME}.")
    print("Passwords for all new accounts: password123")