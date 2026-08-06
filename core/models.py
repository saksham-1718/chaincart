from django.db import models
from django.contrib.auth.models import User
from bson import ObjectId




class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    painting_id = models.CharField(max_length=255, blank=True, null=True)
    painting_title = models.CharField(max_length=255, blank=True, null=True)
    painting_price = models.CharField(max_length=50, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.painting_title or 'Unknown'} ({self.quantity})"

    @property
    def painting(self):
        """Fetch painting details from MongoDB dynamically."""
        from .mongo import db  # local import avoids circular import at module load

        try:
            if not self.painting_id:
                return None

            painting = db["products"].find_one({"_id": ObjectId(self.painting_id)})

            if painting and "image_id" in painting:
                painting["p_image_url"] = f"/media/mongo_image/{painting['image_id']}/"

            return painting

        except Exception as e:
            print("🔥 Error fetching painting:", e)
            return None



class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    avatar_image_id = models.CharField(max_length=100, blank=True, null=True)
    member_since = models.DateField(auto_now_add=True)
    wallet_address = models.CharField(max_length=42, blank=True, null=True)
    encrypted_private_key = models.TextField(blank=True, null=True)
    email_otp = models.CharField(max_length=6, blank=True, null=True)
    email_otp_created_at = models.DateTimeField(blank=True, null=True)
    email_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username