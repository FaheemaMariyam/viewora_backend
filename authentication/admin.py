from django.contrib import admin

from .models import BrokerDetails, Profile, SellerDetails

admin.site.register(Profile)
admin.site.register(BrokerDetails)
admin.site.register(SellerDetails)
