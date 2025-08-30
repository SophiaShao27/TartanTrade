from django.contrib import admin
from django.urls import path
from tartantrade import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Home and info pages
    path('', views.home, name="home"),
    path('help/', views.help, name='help'),
    path('privacy_policy/', views.privacy_policy, name='privacy_policy'),
    path('about_us/', views.about_us, name='about_us'),
    path('shopping_instructions', views.shopping_instructions, name='shopping_instructions'),

    # Admin panel
    path('admin/', admin.site.urls),

    # Authentication
    path('google-login/', views.google_login, name='google_login'),
    path('login/', views.google_login, name='google_login'),  # alias
    path('oauthcallback/', views.oauthcallback, name='oauthcallback'),
    path('logout/', views.logout_action, name='logout'),

    # Product browsing and management
    path('products/', views.product_list, name='product_list'),
    path('api/products/', views.api_products, name='api_products'),
    path('api/products-count/', views.api_products_count, name='api_products_count'),
    path('post-product/', views.post_product, name='post_product'),
    path('products/my-products/', views.my_products, name='my_products'),
    path('products/seller-products/', views.seller_products, name='seller_products'),

    # User profiles
    path('my_profile/', views.profile, name='my_profile'),
    path('user/<int:user_id>/', views.user_profile, name='user_profile'),
    # wishlist
    path('wishlist/add/', views.add_to_wishlist, name='add_to_wishlist'),
    path('cart/toggle/', views.toggle_cart, name='toggle_cart'),



    # Orders
    path('my_orders', views.my_orders, name='my_orders'),
    path('orders/my-orders/', views.my_orders, name='my_orders'),
    path('orders/seller-orders/', views.seller_orders, name='seller_orders'),
    path('orders/<int:receiver_id>/', views.get_user_orders, name='get_user_orders'),

    # Chat
    path('chat/', views.chat_view, name='chat'),
    path('tartantrade/chat-list', views.chat_list, name='chat_list'),
    path('api/chat-list', views.chat_list, name='chat_list'),
    path('chat/history/<int:receiver_id>/', views.chat_history, name='chat_history'),

    # Item and auction detail
    # URL redirect helper
    path('item/<int:id>/', views.item_detail, name='item_detail'),
    # regular product detail pages
    #path('item/buy/<int:id>/', views.regular_item_buyer, name='regular_item_buyer'),
    #path('item/sell/<int:id>/', views.regular_item_seller, name='regular_item_seller'),
    # auction product detail pages
    path('auction/buy/<int:id>/', views.auction_buyer, name='auction_buyer'),
    path('auction/sell/<int:id>/', views.auction_seller, name='auction_seller'),

    path('item/edit/<int:id>/', views.edit_item, name='edit_item'),
    path('item/delete/<int:id>/', views.delete_item, name='delete_item'),
    path('auction/convert/<int:id>/', views.convert_to_auction, name='convert_to_auction'),
    path('auction/edit/<int:id>/', views.edit_auction, name='edit_auction'),
    path('auction/cancel/<int:id>/', views.cancel_auction, name='cancel_auction'),

    # Buying and bidding
    path('auction/bid/<int:id>/', views.place_bid, name='place_bid'),
    path('item/buy/<int:id>/', views.buy_now, name='buy_now'),
    path('item/watchlist/add/<int:id>/', views.add_to_list, name='add_to_watchlist'),

    # Messaging
    path('message/send/<int:user_id>/', views.send_message, name='send_message'),

    # Cart
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('cart/checkout/', views.redirect_to_checkout, name='redirect_to_checkout'),

    # Checkout and payments
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/payment-intent/', views.create_payment_intent, name='create_payment_intent'),
    path('checkout/process/', views.process_order, name='process_order'),
    path('order/confirmation/<str:order_number>/', views.order_confirmation, name='order_confirmation'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
