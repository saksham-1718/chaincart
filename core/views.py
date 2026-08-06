import os
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User, auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import CartItem, Profile
from .mongo import add_user as save_user
from .mongo import users_col as users_collection
from .mongo import db, products_col, record_transaction
import gridfs
from bson import ObjectId
from core.blockchain_utils import sync_artwork_to_blockchain
from core.payment_utils import verify_payment_signature
from contracts.interact_contract import get_artwork
from core.wallet_utils import create_wallet, fund_wallet
from core.payment_utils import create_order, verify_payment_signature
import json as pyjson
from core.wallet_utils import decrypt_private_key
from contracts.interact_contract import buy_artwork
from django.http import JsonResponse
import razorpay
from contracts.interact_contract import relist_artwork
from core.address_utils import verify_pincode
from django.http import JsonResponse
import requests
from django.utils import timezone
from .mongo import db, products_col, record_transaction, save_image_to_gridfs
from core.email_utils import generate_otp, send_otp_email, is_otp_valid, send_order_confirmation_email

def pincode_lookup(request):
    pincode = request.GET.get("pincode", "")

    if not pincode.isdigit() or len(pincode) != 6:
        return JsonResponse({"success": False, "error": "Invalid pincode"})

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(f"https://api.postalpincode.in/pincode/{pincode}", headers=headers, timeout=10)
        data = response.json()
    except Exception as e:
        print(f"⚠️ Pincode lookup failed: {e}")
        return JsonResponse({"success": False, "error": "Lookup service unavailable"})

    if not data or data[0].get("Status") != "Success":
        return JsonResponse({"success": False, "error": "Pincode not found"})

    post_offices = data[0].get("PostOffice", [])
    if not post_offices:
        return JsonResponse({"success": False, "error": "Pincode not found"})

    first = post_offices[0]
    return JsonResponse({
        "success": True,
        "state": first.get("State", ""),
        "city": first.get("District", ""),
    })


@login_required
def relist(request, painting_id):
    if request.method != "POST":
        return redirect("home")

    painting = db["products"].find_one({"_id": ObjectId(painting_id)})
    if not painting:
        return redirect("home")

    # Only the current owner can relist
    if painting.get("current_owner_user") != request.user.username:
        messages.error(request, "Only the current owner can relist this artwork.")
        return redirect("home")

    profile, _ = Profile.objects.get_or_create(user=request.user)
    if not profile.wallet_address or not profile.encrypted_private_key:
        messages.error(request, "Your wallet isn't set up.")
        return redirect("home")

    new_price = request.POST.get("new_price")
    try:
        new_price_int = int(float(new_price))
    except (TypeError, ValueError):
        messages.error(request, "Invalid price.")
        return redirect("home")

    owner_private_key = decrypt_private_key(profile.encrypted_private_key)
    chain_id = painting.get("chain_id")

    receipt = relist_artwork(chain_id, new_price_int, profile.wallet_address, owner_private_key)

    if receipt:
        db["products"].update_one(
            {"_id": ObjectId(painting_id)},
            {"$set": {"p_price": str(new_price_int), "listed_for_resale": True}}
        )
        messages.success(request, "Artwork relisted for resale!")
    else:
        messages.error(request, "Failed to relist on-chain.")

    return redirect("home")


@login_required
def checkout(request, painting_id):
    painting = db["products"].find_one({"_id": ObjectId(painting_id)})
    if not painting:
        return redirect("home")

    price = int(float(painting.get("p_price", 0)))
    order = create_order(price)

    context = {
        "painting": painting,
        "painting_id": str(painting["_id"]),
        "order_id": order["id"],
        "amount": order["amount"],
        "razorpay_key_id": os.getenv("RAZORPAY_KEY_ID"),
    }
    return render(request, "checkout.html", context)

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
@login_required
def listing(request):
    if request.method == "POST":
        fs = gridfs.GridFS(db)
        image_file = request.FILES.get('artwork_image')

        if not image_file:
            messages.error(request, "Please upload an image.")
            return redirect("listing")

        image_id = fs.put(image_file, filename=image_file.name)

        insert_result = db["products"].insert_one({
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
        mongo_id = insert_result.inserted_id

        title = request.POST.get("title")
        artist = request.POST.get("aname")
        price = request.POST.get("price")

        try:
            price_int = int(float(price))
        except (TypeError, ValueError):
            price_int = 0

        profile, _ = Profile.objects.get_or_create(user=request.user)
        if not profile.wallet_address or not profile.encrypted_private_key:
            messages.error(request, "Your wallet isn't set up — cannot list on blockchain.")
            return redirect("listing")

        artist_private_key = decrypt_private_key(profile.encrypted_private_key)
        tx_receipt, chain_id = sync_artwork_to_blockchain(
            title, artist, price_int, profile.wallet_address, artist_private_key
        )


        if chain_id is not None:
            db["products"].update_one(
                {"_id": mongo_id},
                {"$set": {"chain_id": chain_id}}
            )
            messages.success(request, "Artwork successfully added to blockchain!")
        else:
            messages.warning(request, "Artwork saved, but blockchain sync failed — it won't be verifiable on-chain yet.")

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
        avatar_file = request.FILES.get('avatar')  # optional

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
                    last_name=last_name,
                    is_active=False,  # not usable until email is verified
                )
                user.save()

                try:
                    save_user({
                        "username": user.username,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                    })
                except Exception as e:
                    print(f"⚠️ Error saving user to MongoDB: {e}")

                profile, _ = Profile.objects.get_or_create(user=user)

                if avatar_file:
                    profile.avatar = avatar_file

                otp = generate_otp()
                profile.email_otp = otp
                profile.email_otp_created_at = timezone.now()
                profile.save()

                try:
                    send_otp_email(user.email, otp)
                except Exception as e:
                    print(f"⚠️ Failed to send OTP email: {e}")

                try:
                    address, encrypted_key = create_wallet()
                    profile.wallet_address = address
                    profile.encrypted_private_key = encrypted_key
                    profile.save()
                    fund_wallet(address, amount_eth=0.001)
                except Exception as e:
                    print(f"⚠️ Error creating/funding wallet for user: {e}")

                request.session['pending_verification_user_id'] = user.id
                messages.success(request, 'Account created! Check your email for a verification code.')
                return redirect('verify-email')
        else:
            messages.info(request, 'Passwords do not match.')

        return redirect('register')

    return render(request, 'register.html')





def verify_email(request):
    user_id = request.session.get('pending_verification_user_id')
    if not user_id:
        return redirect('register')

    try:
        user = User.objects.get(id=user_id)
        profile = Profile.objects.get(user=user)
    except (User.DoesNotExist, Profile.DoesNotExist):
        return redirect('register')

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')

        if is_otp_valid(profile, entered_otp):
            user.is_active = True
            user.save()
            profile.email_verified = True
            profile.email_otp = None
            profile.save()

            del request.session['pending_verification_user_id']
            auth.login(request, user)
            messages.success(request, 'Email verified! Welcome to ChainCart.')
            return redirect('account')
        else:
            messages.error(request, 'Invalid or expired code. Please try again.')

    return render(request, 'verify_email.html', {'email': user.email})


def resend_otp(request):
    user_id = request.session.get('pending_verification_user_id')
    if not user_id:
        return redirect('register')

    try:
        user = User.objects.get(id=user_id)
        profile = Profile.objects.get(user=user)
    except (User.DoesNotExist, Profile.DoesNotExist):
        return redirect('register')

    otp = generate_otp()
    profile.email_otp = otp
    profile.email_otp_created_at = timezone.now()
    profile.save()

    try:
        send_otp_email(user.email, otp)
        messages.success(request, 'A new code has been sent.')
    except Exception as e:
        print(f"⚠️ Failed to resend OTP email: {e}")
        messages.error(request, 'Failed to send code. Please try again shortly.')

    return redirect('verify-email')


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

    if request.method == "POST" and request.FILES.get("avatar"):
        try:
            profile.avatar_image_id = save_image_to_gridfs(request.FILES["avatar"])
            profile.save()
        except Exception as e:
            print(f"⚠️ Failed to update avatar: {e}")
        return redirect("account")

    if profile.avatar_image_id:
        user_avatar = f"/media/mongo_image/{profile.avatar_image_id}/"
    else:
        user_avatar = "/static/default-avatar.png"

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
        address_line = request.POST.get("address")
        city = request.POST.get("city")
        state = request.POST.get("state")
        pincode = request.POST.get("pincode")
        phone = request.POST.get("phone")

        result = verify_pincode(pincode, city, state)

        if not result["valid"]:
            messages.error(request, result["error"])
            return render(request, "address.html", {
                "order_data": order_data,
                "shipping": request.POST,
            })

        if result["warning"]:
            messages.warning(request, result["warning"])

        request.session["shipping_address"] = {
            "name": name,
            "address": address_line,
            "city": city,
            "state": state,
            "pincode": pincode,
            "phone": phone,
        }

        return redirect("review")

    # GET request — show the form, prefilled if a previous address exists
    shipping = request.session.get("shipping_address", {})

    return render(request, "address.html", {
        "order_data": order_data,
        "shipping": shipping
    })

    
def review(request):
    if not request.user.is_authenticated:
        return redirect("login")

    shipping = request.session.get("shipping_address")
    order_data = request.session.get("order_summary")

    cart_items = order_data.get("cart_data", []) if order_data else []
    subtotal = order_data.get("subtotal", 0) if order_data else 0
    shipping_charge = 0
    total = subtotal + shipping_charge
    painting_id = order_data.get("painting_id") if order_data else None

    context = {
        "shipping": shipping,
        "cart_data": cart_items,
        "subtotal": subtotal,
        "shipping_charge": shipping_charge,
        "total": total,
        "painting_id": painting_id,
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



# 🔗 Verify Artwork On-Chain
def verify_artwork(request, id):
    art = db["products"].find_one({"_id": ObjectId(id)})
    if not art:
        return redirect("home")

    art["id"] = str(art["_id"])
    if "image_id" in art:
        art["p_image_url"] = f"/media/mongo_image/{art['image_id']}/"

    chain_data = None
    mismatches = []
    chain_id = art.get("chain_id")

    if chain_id is not None:
        result = get_artwork(chain_id)
        if result:
            (onchain_id, onchain_title, onchain_artist, onchain_original,
             onchain_owner, onchain_price, onchain_listed) = result

            chain_data = {
                "id": onchain_id,
                "title": onchain_title,
                "artist": onchain_artist,
                "original_artist": onchain_original,
                "current_owner": onchain_owner,
                "price": onchain_price,
                "listed": onchain_listed,
            }

            if onchain_title != art.get("p_title"):
                mismatches.append("title")
            if onchain_artist != art.get("p_artist"):
                mismatches.append("artist")
            try:
                if int(onchain_price) != int(float(art.get("p_price", 0))):
                    mismatches.append("price")
            except (TypeError, ValueError):
                pass

    context = {
        "art": art,
        "chain_data": chain_data,
        "mismatches": mismatches,
        "verified": chain_data is not None and not mismatches,
    }
    return render(request, "verify_artwork.html", context)


@login_required
def purchase(request, painting_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid method"}, status=405)

    try:
        data = pyjson.loads(request.body)
        razorpay_order_id = data.get("razorpay_order_id")
        razorpay_payment_id = data.get("razorpay_payment_id")
        razorpay_signature = data.get("razorpay_signature")

        # 1. Verify the payment genuinely came from Razorpay
        verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature)

        # 2. Look up the artwork
        painting = db["products"].find_one({"_id": ObjectId(painting_id)})
        if not painting:
            return JsonResponse({"success": False, "error": "Artwork not found"}, status=404)

        chain_id = painting.get("chain_id")
        if chain_id is None:
            return JsonResponse({"success": False, "error": "Artwork has no on-chain record — cannot purchase"}, status=400)

        # 3. Get the buyer's custodial wallet
        profile, _ = Profile.objects.get_or_create(user=request.user)
        if not profile.wallet_address or not profile.encrypted_private_key:
            return JsonResponse({"success": False, "error": "Your wallet isn't set up"}, status=400)

        buyer_private_key = decrypt_private_key(profile.encrypted_private_key)

        # 4. Execute the on-chain purchase, signed as the real buyer
        price = int(float(painting.get("p_price", 0)))
        receipt = buy_artwork(chain_id, price, profile.wallet_address, buyer_private_key)

        if receipt is None:
            return JsonResponse({"success": False, "error": "Blockchain purchase failed"}, status=500)

        # 5. Record the sale in MongoDB
        db["products"].update_one(
            {"_id": ObjectId(painting_id)},
            {"$set": {"listed": False, "current_owner_user": request.user.username}}
        )
        record_transaction({
            "painting_id": str(painting_id),
            "buyer": request.user.username,
            "price": price,
            "tx_hash": receipt.transactionHash.hex(),
        })

        CartItem.objects.filter(user=request.user, painting_id=str(painting_id)).delete()

        try:
            record_transaction({
            "painting_id": str(painting_id),
            "buyer": request.user.username,
            "price": price,
            "tx_hash": receipt.transactionHash.hex(),
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_order_id": razorpay_order_id,
        })
        except Exception as e:
            print(f"⚠️ Failed to send confirmation email: {e}")

        return JsonResponse({"success": True})

    except razorpay.errors.SignatureVerificationError:
        return JsonResponse({"success": False, "error": "Payment verification failed"}, status=400)
    except Exception as e:
        print(f"⚠️ Purchase failed: {e}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)






@login_required
def buy_now(request, painting_id):
    painting = db["products"].find_one({"_id": ObjectId(painting_id)})
    if not painting:
        return redirect("home")
    price_str = str(painting.get("p_price", "0"))
    price = int(''.join(c for c in price_str if c.isdigit()) or 0)
    cart_items = [{
        "title": painting.get("p_title", "Unknown"),
        "artist": painting.get("p_artist", "Unknown"),
        "price": price,
        "image_id": painting.get("image_id", ""),
        "quantity": 1,
        "total": price,
    }]
    request.session['order_summary'] = {
        "cart_data": cart_items,
        "subtotal": price,
        "shipping": 0,
        "total": price,
        "painting_id": str(painting_id),
    }
    return redirect("address")