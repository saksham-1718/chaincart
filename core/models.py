from django.db import models
from django.contrib.auth.models import User
from bson import ObjectId
from pymongo import MongoClient

# 👤 User Profile (keep this)
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    member_since = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.user.username




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
        try:
            print("🎨 Fetching painting for:", self.painting_id)

            client = MongoClient("mongodb://localhost:27017/")
            db = client["chaincart"]   # ✅ make sure this matches your MongoDB name

            if not self.painting_id:
                print("⚠️ No painting_id found for this cart item")
                return None

            painting = db["products"].find_one({"_id": ObjectId(self.painting_id)})

            if painting:
                if "image_id" in painting:
                    painting["p_image_url"] = f"/media/mongo_image/{painting['image_id']}/"
                print("✅ Painting found:", painting.get("p_title"))
                return painting
            else:
                print("❌ Painting not found in MongoDB for:", self.painting_id)
                return None

        except Exception as e:
            print("🔥 Error fetching painting:", e)
            return None