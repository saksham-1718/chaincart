from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Painting_detail(models.Model):
    p_title= models.CharField(max_length=100)
    p_artist=models.CharField(max_length=50)
    p_desc=models.CharField(max_length=500)
    p_dims = models.CharField(max_length=500)
    p_price = models.CharField(max_length=100)
    p_image_url = models.URLField(max_length=500, default='')
    # p_image = models.ImageField(upload_to='paintings/', blank=True, null=True)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    member_since = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.user.username
    


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    painting = models.ForeignKey('Painting_detail', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.painting.p_title} x {self.quantity} ({self.user.username})"