from django.contrib import admin
from .models import Profile, CartItem

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'member_since')

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'painting_title', 'painting_price', 'quantity')
