import os
import django

# 1. Setup Django Environment
# IMPORTANT: Change 'hemacycle_backend.settings' to whatever your actual settings folder is named!
# It is the exact same string you see inside your manage.py file.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hercycle_backend.settings') 
django.setup()

from django.contrib.auth import get_user_model

def migrate_usernames_to_emails():
    User = get_user_model()
    users = User.objects.all()
    
    updated_count = 0
    skipped_count = 0

    print("Starting user migration...")

    for user in users:
        # If there is no '@' symbol in the username
        if '@' not in user.username:
            old_username = user.username
            new_email = f"{old_username}@gmail.com"
            
            # Update both the username and the actual email field
            user.username = new_email
            user.email = new_email
            user.save()
            
            print(f"✅ Updated: '{old_username}' -> '{new_email}'")
            updated_count += 1
            
        else:
            # If it already has an '@', just make sure the email field matches
            if not user.email:
                user.email = user.username
                user.save()
                print(f"✅ Synced email field for existing user: {user.username}")
                updated_count += 1
            else:
                skipped_count += 1

    print("\n--- MIGRATION COMPLETE ---")
    print(f"Users fixed: {updated_count}")
    print(f"Users skipped (already perfect): {skipped_count}")

if __name__ == '__main__':
    migrate_usernames_to_emails()