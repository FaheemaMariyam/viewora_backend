from authentication.models import Profile
from django.db import transaction

def assign_broker_to_interest(interest):
    
    #Assign first available approved broker
    

    brokers = Profile.objects.filter(
        role='broker',
        is_admin_approved=True
    ).select_related('user')

    #  pick first available broker
    broker_profile = brokers.first()

    if not broker_profile:
        return None

    interest.broker = broker_profile.user
    interest.status = 'assigned'
    interest.save(update_fields=['broker', 'status'])

    return broker_profile.user
