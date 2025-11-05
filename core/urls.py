from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('auction/',views.auction, name='auction'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('account/', views.account, name='account'),
    path('product1/<str:id>/', views.product1, name='product1'),
    path('add-to-cart/<str:painting_id>/', views.add_to_cart, name='add-to-cart'),
    path('digital-art/', views.digital_art, name='digital-art'),
    path('logout/', views.logout, name='logout'),
    path('sculpture/', views.sculpture, name='sculpture'),
    path('photography/', views.photography, name='photography'),
    path('cart/', views.cart, name='cart'),
    path('wallet/', views.wallet, name='wallet'),
    path('order-summary/', views.order_summary, name='order-summary'),
    path('address/', views.address, name='address'),
    path('payment-mode/', views.payment_mode, name='payment-mode'),
    path('review/', views.review, name='review'),
    path('confirmation/', views.confirmation, name='confirmation'),
    path('listing/', views.listing, name='listing'),
    path('media/mongo_image/<str:image_id>/', views.mongo_image, name='mongo_image'),
]
