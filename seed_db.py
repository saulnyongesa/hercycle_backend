import random
from datetime import timedelta, date
from django.contrib.auth import get_user_model
from core.models import CHVProfile, AdolescentProfile, CycleEntry, SymptomEntry

User = get_user_model()

FIRST_NAMES = ['Wanjiku', 'Akinyi', 'Muthoni', 'Achieng', 'Njeri', 'Nekesa', 'Moraa', 'Nyambura', 'Atieno', 'Nasimiyu', 'Kendi', 'Chebet', 'Wamalwa', 'Kwamboka', 'Auma']
LAST_NAMES = ['Kamau', 'Ochieng', 'Mwangi', 'Odhiambo', 'Ndung\'u', 'Wanjala', 'Onyango', 'Mutua', 'Kariuki', 'Kipkorir', 'Ouma', 'Macharia', 'Barasa', 'Wekesa', 'Otieno']

print("Checking for an active CHV account...")
chv_profile = CHVProfile.objects.filter(is_approved=True).first()

if not chv_profile:
    print("ERROR: No approved CHV found! Please create and approve a CHV in the admin panel first.")
else:
    print(f"Assigning 1000 new users to CHV: {chv_profile.user.username}")
    print("This might take a minute or two... please wait!")
    created_count = 0

    # GENERATING 1000 GIRLS
    for i in range(1000):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        # Randomize the username number more so we don't get duplicates with 1000 users
        username = f"{first_name.lower()}_{last_name.lower()}_{random.randint(1000, 99999)}"

        if User.objects.filter(username=username).exists():
            continue

        # 1. Create User
        user = User.objects.create_user(username=username, password='password123', is_adolescent=True)

        # 2. Create Profile (Age 12-19)
        age = random.randint(12, 19)
        days_old = age * 365 + random.randint(0, 364)
        dob = date.today() - timedelta(days=days_old)
        
        profile = AdolescentProfile.objects.create(user=user, chv=chv_profile, date_of_birth=dob)

        # 3. Generate 1 to 4 past cycles
        num_cycles = random.randint(1, 4)
        current_date = date.today() - timedelta(days=random.randint(5, 20))

        for _ in range(num_cycles):
            cycle_length = random.randint(21, 35)
            bleeding_days = random.randint(3, 7)
            
            start_date = current_date - timedelta(days=cycle_length)
            end_date = start_date + timedelta(days=bleeding_days)
            flow = random.choices(['Light', 'Medium', 'Heavy'], weights=[20, 50, 30])[0]

            CycleEntry.objects.create(
                profile=profile, start_date=start_date, end_date=end_date, flow_intensity=flow
            )

            # 4. Generate Symptoms
            symptom_types = ['Cramps', 'Fatigue', 'Headache', 'Dizziness', 'Pale Skin', 'Mood Swings', 'Bloating']
            
            if flow == 'Heavy':
                SymptomEntry.objects.create(
                    profile=profile, date=start_date + timedelta(days=1),
                    symptom_type=random.choice(['Fatigue', 'Dizziness', 'Pale Skin']), severity=random.randint(3, 5)
                )

            for _ in range(random.randint(0, 2)):
                SymptomEntry.objects.create(
                    profile=profile, date=start_date + timedelta(days=random.randint(0, bleeding_days)),
                    symptom_type=random.choice(symptom_types), severity=random.randint(1, 4)
                )

            current_date = start_date

        created_count += 1
        
        # Print a progress update every 100 users
        if created_count % 100 == 0:
            print(f"... generated {created_count} / 1000 girls")

    print(f"SUCCESS! Generated {created_count} adolescent girls with historical data.")
    print("All new accounts have the password: password123")