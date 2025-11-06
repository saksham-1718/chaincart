from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User, auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import CartItem, Profile
from .mongo import add_user as save_user
from .mongo import users_col as users_collection
from .mongo_client import db
import gridfs
from bson import ObjectId
from pymongo import MongoClient
from core.blockchain_utils import sync_artwork_to_blockchain

client = MongoClient("mongodb+srv://sakshamsingh171845_db_user:Saksham1718@cluster0.6vepxmg.mongodb.net/?appName=Cluster0")
db = client["chaincart"]

# 🏠 Home
def home(request):
    artworks = list(db["products"].find({"category": "painting"}))
    for art in artworks:
        art["id"] = str(art["_id"])

        if "image_id" in art:
            art["p_image_url"] = f"/media/mongo_image/{art['image_id']}/"
    return render(request, 'home.html', {'artworks': artworks})


# 🎨 Auction
def auction(request):
    artworks = list(db["products"].find())
    for art in artworks:
        art["id"] = str(art["_id"])
        if "image_id" in art:
            art["p_image_url"] = f"/media/mongo_image/{art['image_id']}/"
    return render(request, 'auction.html', {'artworks': artworks})


# 🖼️ Listing Art
def listing(request):
    if request.method == "POST":
        fs = gridfs.GridFS(db)
        image_file = request.FILES.get('artwork_image')

        if not image_file:
            messages.error(request, "Please upload an image.")
            return redirect("listing")

        image_id = fs.put(image_file, filename=image_file.name)

        db["products"].insert_one({
            "p_title": request.POST.get("title"),
            "p_artist": request.POST.get("aname"),
            "category": request.POST.get("category"),
            "p_price": request.POST.get("price"),
            "p_desc": request.POST.get("description"),
            "p_dims": request.POST.get("dimensions"),
            "p_medium": request.POST.get("medium"),
            "year": request.POST.get("year"),
            "p_condition": request.POST.get("condition"),
            "p_shipping": request.POST.get("shipping"),
            "image_id": str(image_id)
        })
        title = request.POST["p_title"]
        artist = request.POST["p_artist"]
        price = request.POST["p_price"]

        sync_artwork_to_blockchain(title, artist, int(price))
        messages.success(request, "Artwork successfully added to blockchain!")

        messages.success(request, "🎨 Artwork listed successfully!")
        return redirect("listing")

    return render(request, "listing.html")


# 👤 Register
def register(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('confirm_password')

        username = email.split('@')[0]
        first_name = name.split()[0]
        last_name = " ".join(name.split()[1:]) if len(name.split()) > 1 else ''

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email already used.')
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username already exists.')
            else:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                user.save()
                try:
                    save_user(user)
                except Exception as e:
                    print(f"⚠️ Error saving user to MongoDB: {e}")

                messages.success(request, 'Account created successfully! Please login.')
                return redirect('login')
        else:
            messages.info(request, 'Passwords do not match.')

        return redirect('register')

    return render(request, 'register.html')


# 🔐 Login
def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
            user = auth.authenticate(username=username, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            auth.login(request, user)
            return redirect('account')
        else:
            messages.info(request, 'Invalid email or password.')
            return redirect('login')
    else:
        return render(request, 'login.html')


# 🚪 Logout
def logout(request):
    auth.logout(request)
    return redirect('login')


# 👤 Account Page
@login_required
def account(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)

    mongo_user = users_collection.find_one({"email": user.email})
    if mongo_user and not profile.avatar and "avatar" in mongo_user:
        profile.avatar_url = mongo_user["avatar"]

    user_avatar = (
        request.build_absolute_uri(profile.avatar.url)
        if profile.avatar
        else mongo_user.get("avatar", "/static/default-avatar.png")
        if mongo_user
        else "/static/default-avatar.png"
    )

    context = {
        "user_avatar": user_avatar,
        "user_name": f"{user.first_name} {user.last_name}".strip() or user.username,
        "user_email": user.email,
        "member_since": user.date_joined.strftime("%B %Y"),
    }

    return render(request, "account.html", context)


# 🖼️ Product Detail
def product1(request, id):

    try:
        art = db["products"].find_one({"_id": ObjectId(id)})
        if art:
            art["id"] = str(art["_id"])  # ✅ add this
            art["p_image_url"] = f"/media/mongo_image/{art['image_id']}/"
            return render(request, "product1.html", {"painting": art})
            
    except Exception as e:
            print("⚠️ No artwork found in DB for ID:", id)
    return redirect("home")



# ➕ Add to Cart
@login_required
def add_to_cart(request, painting_id):
    try:
        painting = db["products"].find_one({"_id": ObjectId(painting_id)})
    except Exception as e:
        return redirect('home')

    if not painting:
        return redirect('home')

    # Create or update cart item in SQL DB
    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        painting_id=str(painting["_id"]),
        defaults={
            "painting_title": painting.get("p_title", ""),
            "painting_price": painting.get("p_price", ""),
            "quantity": 1,
        },
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    print(f"✅ Added to cart: {painting.get('p_title')}")
    return redirect('cart')


@login_required
def cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total_price = 0
    updated_cart_items = []

    for item in cart_items:
        # Try fetching painting details from MongoDB
        try:
            painting = db["products"].find_one({"_id": ObjectId(item.painting_id)})
        except Exception as e:
            painting = None
            print(f"⚠️ Error fetching painting {item.painting_id}: {e}")

        # Fallback to saved info if product missing in MongoDB
        if painting:
            title = painting.get("p_title", item.painting_title)
            artist = painting.get("p_artist", "Unknown")
            price = float(painting.get("p_price", 0))
            image_url = f"/media/mongo_image/{painting.get('image_id', '')}/"
        else:
            title = item.painting_title
            artist = "Unknown"
            price = float(item.painting_price or 0)
            image_url = ""

        total_item_price = price * item.quantity
        total_price += total_item_price

        updated_cart_items.append({
            "painting_title": title,
            "painting_artist": artist,
            "painting_price": price,
            "painting_image_url": image_url,
            "quantity": item.quantity,
            "total": total_item_price,
        })

    context = {
        "cart_items": updated_cart_items,
        "total_price": total_price,
    }

    return render(request, "cart.html", context)


# 💳 Payment / Confirmation / Address
@login_required
def address(request):
    order_data = request.session.get('order_summary')
    if not order_data:
        return redirect('order-summary')

    if request.method == "POST":
        name = request.POST.get("name")
        address = request.POST.get("address")
        city = request.POST.get("city")
        state = request.POST.get("state")
        pincode = request.POST.get("pincode")
        phone = request.POST.get("phone")

        # Save in session
        request.session["shipping_address"] = {
            "name": name,
            "address": address,
            "city": city,
            "state": state,
            "pincode": pincode,
            "phone": phone,
        }

        return redirect("review")

    # Prefill data if exists
    shipping = request.session.get("shipping_address", {})

    return render(request, "address.html", {
        "order_data": order_data,
        "shipping": shipping
    })

def review(request):
    if not request.user.is_authenticated:
        return redirect("login")

    # Get address and order info from session
    shipping = request.session.get("shipping_address")
    order_data = request.session.get("order_summary")

    # Re-fetch cart data (optional: same as in order_summary)
    cart_items = order_data.get("cart_data", []) if order_data else []
    subtotal = order_data.get("subtotal", 0) if order_data else 0
    shipping_charge = 0
    total = subtotal + shipping_charge

    context = {
        "shipping": shipping,
        "cart_data": cart_items,
        "subtotal": subtotal,
        "shipping_charge": shipping_charge,
        "total": total,
    }

    return render(request, "review.html", context)


def payment_mode(request):
    return render(request, 'payment-mode.html')

def confirmation(request):
    return render(request, 'confirmation.html')


# 🧾 Serve MongoDB Image
def mongo_image(request, image_id):
    fs = gridfs.GridFS(db)
    try:
        image_file = fs.get(ObjectId(image_id))
        response = HttpResponse(image_file.read(), content_type="image/jpeg")
        return response
    except Exception:
        return HttpResponse("Image not found", status=404)


# 🧩 Categories
def digital_art(request):
    artworks = list(db["products"].find({"category": "digital-art"}))
    for art in artworks:
        art["id"] = str(art["_id"])
        art["p_image_url"] = f"/media/mongo_image/{art['image_id']}/"
    return render(request, 'digital-art.html', {'artworks': artworks})

def sculpture(request):
    artworks = list(db["products"].find({"category": "sculpture"}))
    for art in artworks:
        art["id"] = str(art["_id"])

        if "image_id" in art:
            art["p_image_url"] = f"/media/mongo_image/{art['image_id']}/"
    return render(request, 'sculpture.html', {'artworks': artworks})

def photography(request):
    artworks = list(db["products"].find({"category": "photography"}))
    for art in artworks:
        art["id"] = str(art["_id"])
        art["p_image_url"] = f"/media/mongo_image/{art['image_id']}/"
    return render(request, 'photography.html', {'artworks': artworks})

def order_summary(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # Connect to MongoDB
    client = MongoClient("mongodb+srv://sakshamsingh171845_db_user:Saksham1718@cluster0.6vepxmg.mongodb.net/?appName=Cluster0")
    db = client["chaincart"]

    user_cart = CartItem.objects.filter(user=request.user)
    cart_items = []

    for item in user_cart:
        painting = None

        # Safely try converting painting_id to ObjectId
        if item.painting_id:
            try:
                painting = db["products"].find_one({"_id": ObjectId(item.painting_id)})
            except Exception:
                # fallback if painting_id is already a string or invalid ObjectId
                painting = db["products"].find_one({"_id": item.painting_id})

        if painting:
            price_str = str(painting.get("p_price", "0"))
            price = int(''.join(c for c in price_str if c.isdigit()) or 0)

            cart_items.append({
                "title": painting.get("p_title", "Unknown"),
                "artist": painting.get("p_artist", "Unknown"),
                "price": price,
                "image_id": painting.get("image_id", ""),
                "quantity": item.quantity,
                "total": price * item.quantity,
            })
        else:
            cart_items.append({
                "title": "Not Found",
                "artist": "",
                "price": 0,
                "quantity": item.quantity,
                "total": 0,
            })

    subtotal = sum(p["total"] for p in cart_items)

    context = {
        "cart_data": cart_items,
        "subtotal": subtotal,
        "shipping": 0,   # optional fixed shipping cost
        "total": subtotal,
    }
    # Save summary details in session for next steps
    request.session['order_summary'] = {
        "cart_data": cart_items,
        "subtotal": subtotal,
        "shipping": 0,
        "total": subtotal
    }

    return render(request, "order-summary.html", context)

# 👛 Wallet
def wallet(request):
    return render(request, 'wallet.html')