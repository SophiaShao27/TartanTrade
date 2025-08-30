from django.contrib import admin
from .models import Item, Order, Profile, Auction, RatingItem 

admin.site.register(Item)
admin.site.register(Order)
admin.site.register(Profile)
admin.site.register(Auction)
admin.site.register(RatingItem)
