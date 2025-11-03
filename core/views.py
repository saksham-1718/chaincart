from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User, auth
from django.contrib.auth.decorators import login_required
from .models import Painting_detail, CartItem, Profile
from .mongo import save_user, save_product, save_payment, save_address, save_payment_preference, update_user_avatar
from .mongo import users_collection



# 🏠 Home
def home(request):
    artworks = Painting_detail.objects.all()
    return render(request, 'home.html', {'artworks': artworks})


# 🎨 Auction
def auction(request):
    artworks = Painting_detail.objects.all()
    return render(request, 'auction.html', {'artworks': artworks})


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

                # 💾 Save user to MongoDB
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

    # ✅ Sync from MongoDB to Django (if missing in Django)
    mongo_user = users_collection.find_one({"email": user.email})
    if mongo_user and not profile.avatar and "avatar" in mongo_user:
        avatar_url = mongo_user["avatar"]
        profile.avatar_url = avatar_url  # temporarily attach for template use

    # ✅ Handle avatar upload from Django form
    if request.method == "POST" and request.FILES.get("avatar"):
        avatar_file = request.FILES["avatar"]
        profile.avatar.save(avatar_file.name, avatar_file)
        profile.save()

        # ✅ Convert to absolute URL before storing in MongoDB
        avatar_url = request.build_absolute_uri(profile.avatar.url)
        try:
            update_user_avatar(user.email, avatar_url)
            print(f"✅ Avatar URL saved to MongoDB for {user.email}: {avatar_url}")
        except Exception as e:
            print(f"⚠️ MongoDB avatar update failed: {e}")

        return redirect("account")

    # ✅ Prefer Django avatar → fallback to MongoDB → fallback to default
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
    painting = Painting_detail.objects.get(id=id)

    # 💾 Sync product to MongoDB if not already present
    try:
        save_product(painting)
    except Exception as e:
        print(f"⚠️ Error syncing product to MongoDB: {e}")

    return render(request, 'product1.html', {'painting': painting})


# 🎭 Categories
def digital_art(request):
    artworks = Painting_detail.objects.all()
    return render(request, 'digital-art.html', {'artworks': artworks})


def sculpture(request):
    artworks = Painting_detail.objects.all()
    return render(request, 'sculpture.html', {'artworks': artworks})


def photography(request):
    artworks = Painting_detail.objects.all()
    return render(request, 'photography.html', {'artworks': artworks})


# 👛 Wallet
def wallet(request):
    return render(request, 'wallet.html')


# 🛒 Cart
def cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total_price = 0

    for item in cart_items:
        price_str = item.painting.p_price
        price_clean = ''.join(filter(str.isdigit, price_str))
        price_int = int(price_clean) if price_clean else 0
        total_price += price_int * item.quantity

    context = {
        'cart_items': cart_items,
        'total_price': total_price
    }
    return render(request, 'cart.html', context)


# ➕ Add to Cart
@login_required
def add_to_cart(request, painting_id):
    painting = get_object_or_404(Painting_detail, id=painting_id)
    cart_item, created = CartItem.objects.get_or_create(user=request.user, painting=painting)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('cart')


# 📦 Address Page
def address(request):
    if request.method == 'POST':
        addr_line = request.POST.get('line1')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip')
        country = "India"

        # 💾 Save to MongoDB
        try:
            save_address(
                user_email=request.user.email,
                address_line=addr_line,
                city=city,
                state=state,
                zip_code=zip_code,
                country=country
            )
        except Exception as e:
            print(f"⚠️ Error saving address: {e}")

        return redirect('review')

    return render(request, 'address.html')


# 📋 Order Summary
def order_summary(request):
    if not request.user.is_authenticated:
        return redirect('login')

    cart_items = CartItem.objects.filter(user=request.user)
    subtotal = 0
    for item in cart_items:
        try:
            price_str = ''.join(c for c in str(item.painting.p_price) if c.isdigit())
            price = int(price_str)
            subtotal += price * item.quantity
        except ValueError:
            print("Error: Input must be a positive number.")

    shipping = 100
    total = subtotal + shipping

    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total
    }
    return render(request, 'order-summary.html', context)


# 💳 Payment Mode
def payment_mode(request):
    if request.method == 'POST':
        method = request.POST.get('method')
        amount = request.POST.get('amount', 0)

        # 💾 Save payment info to MongoDB
        try:
            save_payment(
                user_email=request.user.email,
                amount=amount,
                status="Success",
                method=method
            )
        except Exception as e:
            print(f"⚠️ Error saving payment: {e}")

        return redirect('confirmation')

    return render(request, 'payment-mode.html')


# 🔍 Review Page
def review(request):
    return render(request, 'review.html')


# ✅ Confirmation Page
def confirmation(request):
    return render(request, 'confirmation.html')
