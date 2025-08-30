import time
import json
import uuid
import random
import stripe
import requests
import traceback

from urllib.parse import urlencode
from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from django.db.models import Avg
from django.db.models import Max
from django.db.models import Count
from django.db.models import Sum

from .models import ChatMessage
from .models import Order
from .models import Item
from .models import Profile
from .models import RatingItem
from .models import Auction

from .forms import ItemForm
from .forms import AuctionForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST




# Wendi
import secrets
import logging
from django.conf import settings
from django.contrib.auth import login
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import redirect
import requests
from django.views.decorators.csrf import csrf_protect
from django.utils.html import escape
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_POST



logger = logging.getLogger(__name__)

# Wendi: 0403 modified for safer
def google_login(request):
    """
    Initiate Google OAuth login process with enhanced session management

    Handles various login scenarios:
    - Already authenticated users
    - Previous session handling
    - Secure state generation
    """
    # Check if user is already authenticated
    if request.user.is_authenticated:
        # Extend existing session if needed
        request.session.set_expiry(1209600)  # 2 weeks
        messages.info(request, "You are already logged in.")
        return redirect('home')

    # Generate a secure, cryptographically strong state
    state = secrets.token_urlsafe(64)  # Increased entropy

    try:
        # Store state with enhanced session management
        request.session['oauth_state'] = state
        request.session['oauth_state_timestamp'] = time.time()

        # Preserve any intended destination
        if 'next' in request.GET:
            request.session['next_url'] = request.GET['next']

        # Prepare OAuth authorization URL
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            "response_type": "code",
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",  # Request refresh token
            "prompt": "select_account"
        }

        # Construct full authorization URL
        query_string = urlencode(params)
        authorization_url = f"{base_url}?{query_string}"

        # Log login attempt
        logger.info(f"OAuth login initiated. State generated: {state[:10]}...")

        return redirect(authorization_url)

    except Exception as e:
        # Comprehensive error handling
        logger.error(f"OAuth login initialization failed: {str(e)}")
        messages.error(request, "Login initialization failed. Please try again.")
        return redirect('home')


def oauthcallback(request):
    """
    Handle Google OAuth callback with comprehensive security and user management.

    Key Features:
    - Robust state and CSRF protection
    - Strict email domain validation
    - Comprehensive error handling
    - Secure user authentication
    """
    # Capture start time for logging and tracking
    start_time = timezone.now()

    try:
        # Validate essential callback parameters
        received_state = request.GET.get("state")
        code = request.GET.get("code")

        # Check for missing critical parameters
        if not received_state or not code:
            logger.warning(f"Missing critical OAuth parameters. State: {bool(received_state)}, Code: {bool(code)}")
            messages.error(request, "Invalid login attempt. Please try again.")
            return redirect('home')

        # Retrieve and validate stored state
        stored_state = request.session.get('oauth_state')
        state_timestamp = request.session.get('oauth_state_timestamp', 0)
        current_time = time.time()

        # Comprehensive state validation
        state_validation_failed = (
                not stored_state or
                received_state != stored_state or
                (current_time - state_timestamp > 3600)  # 1-hour validity window
        )

        if state_validation_failed:
            logger.warning(
                f"OAuth state validation failed. Stored state: {stored_state}, Received state: {received_state}")
            messages.error(request, "Login session has expired. Please try again.")
            return redirect('home')

        # Clear state from session to prevent reuse
        request.session.pop('oauth_state', None)
        request.session.pop('oauth_state_timestamp', None)

        # Prepare token exchange request
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        }

        # Exchange authorization code for tokens
        try:
            token_response = requests.post(token_url, data=token_data, timeout=15)
            token_response.raise_for_status()
            tokens = token_response.json()
        except requests.RequestException as e:
            logger.error(f"Token retrieval failed: {str(e)}")
            messages.error(request, "Authentication failed. Unable to retrieve access token.")
            return redirect('home')

        # Validate access token
        access_token = tokens.get("access_token")
        if not access_token:
            logger.warning("No access token received in OAuth response")
            messages.error(request, "Authentication failed. No access token provided.")
            return redirect('home')

        # Fetch user information
        try:
            userinfo_response = requests.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10
            )
            userinfo_response.raise_for_status()
            userinfo = userinfo_response.json()
        except requests.RequestException as e:
            logger.error(f"User information retrieval failed: {str(e)}")
            messages.error(request, "Failed to retrieve user information.")
            return redirect('home')

        # Extract and sanitize user information
        email = userinfo.get("email", "").lower().strip()
        name = userinfo.get("name", "").strip()[:150]  # Limit name length

        # Strict email domain validation
        allowed_domains = ['@andrew.cmu.edu', '@cmu.edu']
        if not any(email.endswith(domain) for domain in allowed_domains):
            logger.warning(f"Unauthorized email domain attempted: {email}")
            messages.error(request, "Only CMU email addresses are allowed.")
            return redirect('home')

        # User creation or retrieval with atomic transaction
        try:
            with transaction.atomic():
                user, created = User.objects.get_or_create(
                    username=email,
                    defaults={
                        "first_name": name,
                        "email": email,
                        "is_active": True
                    }
                )

                # Ensure user profile exists
                Profile.objects.get_or_create(
                    user=user,
                    defaults={
                        'content_type': 'text/plain',
                        'last_oauth_login': start_time
                    }
                )

                # Update last login for existing users
                if not created:
                    user.last_login = start_time
                    user.save(update_fields=['last_login'])

        except Exception as e:
            logger.error(f"User management failed: {str(e)}")
            messages.error(request, "Unable to complete login process.")
            return redirect('home')

        # Authenticate user
        login(request, user)

        # Configure persistent session
        request.session.set_expiry(1209600)  # 2 weeks
        request.session['login_timestamp'] = start_time.isoformat()

        # Prepare success message and logging
        login_message = f"Welcome {'to TartanTrade' if created else 'back'}, {name}!"
        messages.success(request, login_message)
        logger.info(f"Successful OAuth login: {email} ({'New user' if created else 'Existing user'})")

        # Redirect handling
        next_url = request.session.pop('next_url', 'home')
        return redirect(next_url)

    except Exception as unexpected_error:
        # Catch-all error handling
        logger.critical(f"Unexpected OAuth callback error: {unexpected_error}")
        logger.critical(traceback.format_exc())

        # Clear session and show generic error
        request.session.flush()
        messages.error(request, "An unexpected error occurred. Please try again.")
        return redirect('home')


# Wendi: home page modified on 0405
@csrf_protect
def home(request):
    if request.method == 'GET':
        try:
            # parameter check
            category_name = request.GET.get('category', '').strip()
            search_query = request.GET.get('nav_top_search', '').strip()

            # too long string search
            if len(category_name) > 50 or len(search_query) > 100:
                logger.warning(f"Invalid query length. Category: {category_name}, Search: {search_query}")
                return HttpResponse("Invalid query parameters", status=400)

            # safe escape: prevent browsers from parsing dangerous searches as HTML or scripts
            # <script>alert('hi')</script>
            category_name = escape(category_name)
            search_query = escape(search_query)

            # valid categories check
            valid_categories = ['All', 'Electronics', 'Books', 'Furniture', 'Grocery']
            if category_name and category_name not in valid_categories:
                logger.warning(f"Invalid category: {category_name}")
                return HttpResponse("Invalid category", status=400)

            # newly posted products
            new_products = Item.objects.order_by('-upload_time')[:15]

            # initially search and filter
            is_search = False
            product_list = Item.objects.all()

            # search
            if search_query:
                product_list = product_list.filter(
                    Q(title__icontains=search_query) |
                    Q(description__icontains=search_query)
                )
                is_search = True

                # no results
                if not product_list.exists():
                    logger.info(f"No results found for search query: {search_query}")
                    return render(request, 'tartantrade/home.html', {
                        'is_search': True,
                        'query': search_query,
                        'product_list': [],
                        'message': f"No results found for '{search_query}'. Try different keywords."
                    })

            # filter by category
            if category_name and category_name != 'All':
                product_list = product_list.filter(category=category_name)

            # every page has 20 products
            paginator = Paginator(product_list, 20)
            page = request.GET.get('page', 1)
            try:
                product_list = paginator.page(page)
            except (PageNotAnInteger, EmptyPage):
                logger.warning(f"Invalid page number: {page}")
                product_list = paginator.page(1)

            # banner
            trending_items = Item.objects.annotate(
                order_count=Count('orders')
            ).order_by('-order_count')[:3]


            context = {
                'new_products': new_products,
                'trending_items': trending_items,
                'query': search_query,
                'is_search': is_search,
                'selected_category': category_name,
                'product_list': product_list,
                'total_pages': paginator.num_pages,
                'current_page': page,
            }

            return render(request, 'tartantrade/home.html', context)

        except ValidationError as e:
            logger.error(f"Validation Error: {str(e)}")
            return HttpResponse("Invalid input", status=400)

        except Exception as e:
            logger.critical(f"Unexpected error in home view: {str(e)}")
            logger.critical(traceback.format_exc())
            return HttpResponse("Internal Server Error", status=500)
    elif request.method == 'POST':
        if 'item_id' in request.POST:
            # Add to cart and then redirect back to home with updated cart count
            try:
                # Call the add_to_cart function
                add_to_cart_response = add_to_cart(request)

                # Check if the operation was successful
                response_data = json.loads(add_to_cart_response.content)
                if response_data.get('success'):
                    # Get the redirect URL (back to home with current filters)
                    redirect_url = request.POST.get('redirect_url', '/')

                    # Add success message for user feedback
                    messages.success(request, "Item added to cart successfully!")

                    # Redirect back to the home page
                    return redirect(redirect_url)
                else:
                    # If there was an error in add_to_cart, show error message
                    messages.error(request, response_data.get('error', 'Error adding item to cart'))
                    return redirect('/')
            except Exception as e:
                logger.error(f"Error in add_to_cart from home view: {str(e)}")
                messages.error(request, "Error adding item to cart")
                return redirect('/')
    else:
        # Handle other possible POST actions or return error for invalid POST
        logger.warning("Invalid POST request to home view without product_id")
        return HttpResponse("Invalid request", status=400)




# Wendi: logout
@login_required
def logout_action(request):
    logout(request)
    return redirect("google_login")



# Wendi: add_to_cart unified interface modified on 0404
@login_required
def add_to_cart(request, item_id):
    """
    Add item to cart view that handles both form submissions and AJAX requests
    """
    try:
        # Check if it's a JSON request
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            quantity = int(data.get('quantity', 1))
        else:
            # Handle regular form submission
            quantity = int(request.POST.get('quantity', 1))

        # Get the item
        item = get_object_or_404(Item, id=item_id)

        # Get or create cart in session
        cart = request.session.get('cart', {})

        # Add to cart
        item_id_str = str(item_id)
        if item_id_str in cart:
            cart[item_id_str] += quantity
        else:
            cart[item_id_str] = quantity

        # Update session
        request.session['cart'] = cart
        request.session.modified = True

        # Return JSON response for AJAX or redirect for form
        if request.content_type == 'application/json':
            return JsonResponse({
                'success': True,
                'cart': cart,
                'cart_count': sum(cart.values()),
                'item': {
                    'id': item.id,
                    'title': item.title,
                    'price': float(item.price),
                    'quantity': cart[item_id_str]
                }
            })
        else:
            messages.success(request, f"{item.title} added to your cart!")
            return redirect(request.META.get('HTTP_REFERER', 'home'))

    except Item.DoesNotExist:
        if request.content_type == 'application/json':
            return JsonResponse({
                'success': False,
                'error': 'Item not found'
            }, status=404)
        else:
            messages.error(request, "Item not found")
            return redirect('home')

    except (ValueError, TypeError) as e:
        if request.content_type == 'application/json':
            return JsonResponse({
                'success': False,
                'error': 'Invalid quantity'
            }, status=400)
        else:
            messages.error(request, "Invalid quantity")
            return redirect('home')

    except Exception as e:
        if request.content_type == 'application/json':
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        else:
            messages.error(request, "Error adding item to cart")
            return redirect('home')




# Wendi: product listing
@ensure_csrf_cookie
def product_list_ajax(request):
    """渲染包含Ajax功能的产品列表页面"""
    # 获取筛选参数
    category = request.GET.get('category', 'All')
    min_price = request.GET.get('min_price', None)
    max_price = request.GET.get('max_price', None)
    conditions = request.GET.getlist('condition')
    search_query = request.GET.get('nav_top_search', '')
    sort_by = request.GET.get('sort', 'default')
    page_number = request.GET.get('page', 1)

    # 开始查询
    products = Item.objects.all()

    # 应用筛选条件
    if category != 'All':
        products = products.filter(category=category)

    if min_price:
        products = products.filter(price__gte=float(min_price))

    if max_price:
        products = products.filter(price__lte=float(max_price))

    if conditions:
        products = products.filter(condition__in=conditions)

    if search_query:
        products = products.filter(title__icontains=search_query) | products.filter(description__icontains=search_query)

    # sort by
    if sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')

    # 分页
    paginator = Paginator(products, 12)  # 每页12个产品
    page_obj = paginator.get_page(page_number)

    context = {
        'product_list': page_obj,
        'total_products': paginator.count,
        'selected_category': category,
        'min_price': min_price,
        'max_price': max_price,
        'selected_conditions': conditions,
        'search_query': search_query,
        'sort_by': sort_by,
        'enable_realtime_updates': True  # 启用实时更新
    }

    return render(request, 'tartantrade/product_list_ajax.html', context)





# Wendi: product listing
def api_products(request):
    """API端点：获取产品数据"""
    # 获取筛选参数
    category = request.GET.get('category', 'All')
    min_price = request.GET.get('min_price', None)
    max_price = request.GET.get('max_price', None)
    conditions = request.GET.getlist('condition')
    search_query = request.GET.get('nav_top_search', '')
    sort_by = request.GET.get('sort', 'default')
    page_number = request.GET.get('page', 1)

    # 开始查询
    products = Item.objects.all()

    # 应用筛选条件
    if category != 'All':
        products = products.filter(category=category)

    if min_price:
        products = products.filter(price__gte=float(min_price))

    if max_price:
        products = products.filter(price__lte=float(max_price))

    if conditions:
        products = products.filter(condition__in=conditions)

    if search_query:
        products = products.filter(title__icontains=search_query) | products.filter(description__icontains=search_query)

    # 应用排序
    if sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')

    # 分页
    paginator = Paginator(products, 12)  # 每页12个产品
    page_obj = paginator.get_page(page_number)

    # 格式化结果
    product_list = []
    for product in page_obj:
        product_list.append({
            'id': product.id,
            'title': product.title,
            'description': product.description,
            'price': float(product.price),
            'category': product.category,
            'condition': product.condition,
            'picture': product.picture.url if product.picture else None,
            'created_at': product.created_at.isoformat() if hasattr(product, 'created_at') else None
        })

    # 返回JSON响应
    return JsonResponse({
        'products': product_list,
        'total_products': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': int(page_number),
        'is_authenticated': request.user.is_authenticated
    })

# Wendi product listing
def api_products_count(request):
    """API端点：获取产品总数"""
    # 可以添加与product_list_ajax相同的筛选条件以获取准确的计数
    count = Item.objects.all().count()
    return JsonResponse({'count': count})


# Wendi: remove because I have unified add_to_cart
@login_required
def api_add_to_cart(request):
    """API：add products to cart"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)

        if not product_id:
            return JsonResponse({'error': 'Product ID is required'}, status=400)

        # 获取购物车或创建新购物车
        cart = request.session.get('cart', {})

        # 将商品添加到购物车
        if str(product_id) in cart:
            cart[str(product_id)] += quantity
        else:
            cart[str(product_id)] = quantity

        # 保存购物车到会话
        request.session['cart'] = cart
        request.session.modified = True

        return JsonResponse({'success': True, 'cart': cart})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# Wendi: product listing
@login_required
def api_cart_count(request):
    """API端点：获取购物车商品数量"""
    cart = request.session.get('cart', {})
    count = sum(cart.values())
    return JsonResponse({'count': count})



# Wendi: chatting
@login_required
def chat_view(request):
    chat_user = request.user
    return render(request, 'tartantrade/chat.html', {
        'chat_user': chat_user
    })


# Wendi: chatting
@login_required
def chat_history(request, receiver_id):
    current_user = request.user
    page = int(request.GET.get('page', 1))
    # every page has 10 messages
    page_size = 10
    start = (page - 1) * page_size
    end = page * page_size

    #
    try:
        receiver = User.objects.get(id=receiver_id)
        # current_user and receiver has been assigned
        # query all messages between current user and receiver
        base_query = ChatMessage.objects.filter(
            ((Q(send_from=current_user) & Q(send_to=receiver)) |
            (Q(send_from=receiver) & Q(send_to=current_user)))
        ).order_by('-creation_time')
        # mark current message as read and seen
        unread_messages = base_query.filter(send_to=current_user, is_read=False)
        unread_messages.update(is_read=True)
        # current page message
        messages = base_query[start:end + 1]
        # whether it has more messages
        has_more = len(messages) > page_size
        # assigned number of messsages
        messages = messages[:page_size]
        
        messages_data = [{
            'message': msg.message,
            'sender_id': msg.send_from.id,
            'sender_name': msg.send_from.username,
            'order_info': msg.order_info,
            'creation_time': msg.creation_time.strftime('%Y-%m-%d %H:%M:%S')
        } for msg in messages]

        return JsonResponse({
            'messages': messages_data,
            'has_more': has_more
        })
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)


# Wendi: chatting
@login_required
def get_user_orders(request, receiver_id):
    current_user = request.user
    try:
        receiver = User.objects.get(id=receiver_id)
        # get orders
        orders = Order.objects.filter(
            (Q(buyer=current_user) & Q(seller=receiver)) |
            (Q(buyer=receiver) & Q(seller=current_user))
        ).order_by('-created_time')

        # there does not exist orders
        if not orders.exists():
            # create an item for testing
            test_item1 = Item.objects.create(
                description='Test Item 1',
                condition='New',
                category='Electronics',
                user=current_user,
                price=99.99,
                upload_time=timezone.now(),
                pickup_location='CMU Campus'
            )
            test_item2 = Item.objects.create(
                description='Test Item 2',
                condition='Used',
                category='Books',
                user=receiver,
                price=19.99,
                upload_time=timezone.now(),
                pickup_location='CMU Library'
            )

            # 生成唯一订单号

            timestamp = int(time.time())
            order_number1 = f'TEST{timestamp}_{random.randint(1000, 9999)}'
            order_number2 = f'TEST{timestamp}_{random.randint(1000, 9999)}'

            # 创建测试订单
            Order.objects.create(
                order_number=order_number1,
                status='pending',
                total_price=test_item1.price,
                payment_method='Credit Card',
                buyer=receiver,
                seller=current_user,
                item=test_item1,
                shipping_address='5000 Forbes Ave, Pittsburgh, PA 15213'
            )
            Order.objects.create(
                order_number=order_number2,
                status='paid',
                total_price=test_item2.price,
                payment_method='PayPal',
                buyer=current_user,
                seller=receiver,
                item=test_item2,
                shipping_address='4800 Forbes Ave, Pittsburgh, PA 15213'
            )

            # 重新获取订单
            orders = Order.objects.filter(
                (Q(buyer=current_user) & Q(seller=receiver)) |
                (Q(buyer=receiver) & Q(seller=current_user))
            ).order_by('-created_time')

        orders_data = [{
            'item_name': order.item.description,
            'price': float(order.total_price),
            'status': order.status,
            'id': order.id
        } for order in orders]

        return JsonResponse({'orders': orders_data})
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)


# Wendi: chatting
@login_required
def chat_list(request):
    current_user = request.user
    # all users except the current user
    chat_partners = User.objects.filter(
    (Q(chat_from__send_to=current_user) | Q(chat_to__send_from=current_user)) &
    ~Q(id=current_user.id)
    ).distinct()
    #  test: all users chatting creation
    chat_partners = User.objects.filter(
        ~Q(id=current_user.id)
    ).distinct()
    # 构建聊天列表数据
    chat_list_data = []
    for partner in chat_partners:
        # 获取与该用户的最后一条消息
        last_message = ChatMessage.objects.filter(
            Q(send_from=current_user, send_to=partner) |
            Q(send_from=partner, send_to=current_user)
        ).order_by('-creation_time').first()
        if last_message:
            # 获取未读消息数量
            unread_count = ChatMessage.objects.filter(
                send_from=partner,
                send_to=current_user,
                is_read=False
            ).count()

            chat_list_data.append({
                'user_id': partner.id,
                'user_name': partner.get_full_name() or partner.username,
                'last_message': last_message.message,
                'last_message_time': last_message.creation_time.strftime('%Y-%m-%d %H:%M'),
                'unread_count': unread_count
            })
        else:
            # if there is no chatting message, welcome message
            # welcome_msg = ChatMessage.objects.create(
            #     message=f"Welcome to chat with {partner.get_full_name() or partner.username}!",
            #     send_from=current_user,
            #     send_to=partner
            # )
            chat_list_data.append({
                'user_id': partner.id,
                'user_name': partner.get_full_name() or partner.username,
                'last_message': f"Welcome to chat with {partner.get_full_name() or partner.username}!",
                'last_message_time': timezone.now().strftime('%Y-%m-%d %H:%M'),
                'unread_count': 0
            })
    
    # -update
    chat_list_data.sort(key=lambda x: x['last_message_time'], reverse=True)
    return JsonResponse(chat_list_data, safe=False)


# Wendi: cart page
@login_required
def cart_view(request):
    # GET only
    if request.method != 'GET':
        return HttpResponse(status=405)

    # Get items from session cart or from a Cart model if you implement one
    cart_items = []
    cart_data = request.session.get('cart', {})

    total_price = 0

    # Retrieve full item details for each item in cart
    for item_id, quantity in cart_data.items():
        try:
            item = Item.objects.get(id=item_id)
            item_total = item.price * quantity
            total_price += item_total

            # Format data to match cart.html template
            cart_items.append({
                'item': item,
                'quantity': quantity,
                'item_total': item_total,
                'price': item.price,
                # modify!
                'image_url': item.picture.url if item.picture else 'https://via.placeholder.com/100',
                'title': item.title,
                'description': item.description[:100]  # Truncate description if too long
            })
        except Item.DoesNotExist:
            # Remove invalid items from cart
            if item_id in cart_data:
                del cart_data[item_id]
                request.session['cart'] = cart_data

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'tartantrade/cart.html', context)


# Wendi: cart done
@login_required
def update_cart(request):
    """Update cart quantities via AJAX - POST method only"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    # Handle both AJAX and form submissions
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Process AJAX request
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            quantity = int(data.get('quantity', 1))
            action = data.get('action')

            if not all([item_id, action]):
                return JsonResponse({'status': 'error', 'message': 'Missing required data'})

            cart = request.session.get('cart', {})

            if action == 'update':
                if quantity < 1:
                    quantity = 1  # Minimum quantity is 1
                cart[str(item_id)] = quantity
            elif action == 'remove':
                if str(item_id) in cart:
                    del cart[str(item_id)]

            request.session['cart'] = cart

            # Recalculate total
            total_price = 0
            for item_id, qty in cart.items():
                try:
                    item = Item.objects.get(id=item_id)
                    total_price += item.price * qty
                except Item.DoesNotExist:
                    pass

            return JsonResponse({
                'status': 'success',
                'total_price': total_price
            })
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    else:
        # Process form submission
        item_id = request.POST.get('item_id')
        action = request.POST.get('action')
        quantity = int(request.POST.get('quantity', 1))

        if not item_id:
            messages.error(request, "Item ID is required.")
            return redirect('cart_view')

        cart = request.session.get('cart', {})

        if action == 'update':
            if quantity < 1:
                quantity = 1
            cart[str(item_id)] = quantity
        elif action == 'remove':
            if str(item_id) in cart:
                del cart[str(item_id)]

        request.session['cart'] = cart
        messages.success(request, "Cart updated successfully.")
        return redirect('cart_view')

# Wendi: checkout debugging
@login_required
def redirect_to_checkout(request):
    """Handle 'Proceed to Payment' button - POST method only"""
    if request.method != 'POST':
        return HttpResponse(status=405)  # Method Not Allowed

    # Verify cart has items
    cart_data = request.session.get('cart', {})
    if not cart_data:
        messages.warning(request, "Your cart is empty.")
        return redirect('cart_view')

    # Optional: update cart items if quantities were changed
    if 'update_cart' in request.POST:
        for item_id, quantity in cart_data.items():
            new_quantity = request.POST.get(f'quantity_{item_id}')
            if new_quantity and new_quantity.isdigit():
                cart_data[item_id] = int(new_quantity)

        request.session['cart'] = cart_data
        messages.success(request, "Cart updated successfully.")

    return redirect('checkout')

# Wendi: checkout
@login_required
def checkout(request):
    """Checkout page - GET method only"""
    if request.method != 'GET':
        return HttpResponse(status=405)  # Method Not Allowed

    cart_data = request.session.get('cart', {})

    if not cart_data:
        messages.warning(request, "Your cart is empty.")
        return redirect('cart_view')

    cart_items = []
    total_price = 0

    for item_id, quantity in cart_data.items():
        try:
            item = Item.objects.get(id=item_id)

            # Check if item is still available
            if item.user == request.user:
                messages.warning(request, f"You cannot buy your own item: {item.title}")
                continue

            item_total = item.price * quantity
            total_price += item_total

            cart_items.append({
                'item': item,
                'quantity': quantity,
                'item_total': item_total
            })
        except Item.DoesNotExist:
            # Remove invalid items
            if item_id in cart_data:
                del cart_data[item_id]
                request.session['cart'] = cart_data

    # Get user profile for shipping address if available
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        profile = None

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'profile': profile,
    }
    return render(request, 'tartantrade/checkout.html', context)

# Wendi: checkout
@login_required
def create_payment_intent(request):
    """Create Stripe payment intent - POST method only"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    cart_data = request.session.get('cart', {})

    if not cart_data:
        return JsonResponse({'error': 'Cart is empty'}, status=400)

    # Calculate total
    total_amount = 0
    for item_id, quantity in cart_data.items():
        try:
            item = Item.objects.get(id=item_id)
            total_amount += item.price * quantity
        except Item.DoesNotExist:
            pass

    # Convert to cents for Stripe
    amount_cents = int(total_amount * 100)

    try:
        # Create payment intent with Stripe
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency='usd',
            metadata={'user_id': request.user.id}
        )

        return JsonResponse({
            'clientSecret': intent.client_secret
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=403)

# Wendi: checkout
@login_required
def process_order(request):
    """Process successful order after payment - POST method only"""
    if request.method != 'POST':
        return HttpResponse(status=405)  # Method Not Allowed

    cart_data = request.session.get('cart', {})
    shipping_address = request.POST.get('shipping_address')
    payment_method = request.POST.get('payment_method', 'credit_card')

    if not cart_data:
        messages.error(request, "Your cart is empty.")
        return redirect('checkout')

    if not shipping_address:
        messages.error(request, "Shipping address is required.")
        return redirect('checkout')

    # Generate unique order number
    order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"

    # Process each item in cart
    for item_id, quantity in cart_data.items():
        try:
            item = Item.objects.get(id=item_id)
            seller = item.user

            # Create order
            order = Order.objects.create(
                order_number=order_number,
                status='paid',  # Assuming payment is already processed
                total_price=item.price * quantity,
                payment_method=payment_method,
                created_time=timezone.now(),
                paid_time=timezone.now(),
                buyer=request.user,
                seller=seller,
                item=item,
                shipping_address=shipping_address
            )

            # Update user profiles
            buyer_profile, _ = Profile.objects.get_or_create(user=request.user)
            buyer_profile.items_bought.add(item)

            seller_profile, _ = Profile.objects.get_or_create(user=seller)
            seller_profile.items_sold.add(item)

        except Item.DoesNotExist:
            continue

    # Clear cart after successful order
    request.session['cart'] = {}

    messages.success(request, f"Order #{order_number} placed successfully!")
    return redirect('order_confirmation', order_number=order_number)

# Wendi: checkout
@login_required
def order_confirmation(request, order_number):
    """Order confirmation page - GET method only"""
    if request.method != 'GET':
        return HttpResponse(status=405)  # Method Not Allowed

    # Get all orders with this order number (could be multiple items)
    orders = Order.objects.filter(order_number=order_number, buyer=request.user)

    if not orders.exists():
        messages.error(request, "Order not found.")
        return redirect('home')

    total_amount = orders.aggregate(Sum('total_price'))['total_price__sum']

    context = {
        'orders': orders,
        'order_number': order_number,
        'total_amount': total_amount,
    }
    return render(request, 'tartantrade/order_confirmation.html', context)

# Wendi: my_orders
@login_required
def my_orders(request):
    """View user's orders - GET method only"""
    if request.method != 'GET':
        return HttpResponse(status=405)  # Method Not Allowed

    # Get all orders where user is buyer
    orders = Order.objects.filter(buyer=request.user).order_by('-created_time')

    # Paginate results
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'tartantrade/my_orders.html', context)

# Wendi Cai: seller_orders
@login_required
def seller_orders(request):
    """View orders where user is seller - GET method only"""
    if request.method != 'GET':
        return HttpResponse(status=405)  # Method Not Allowed

    # Get all orders where user is seller
    orders = Order.objects.filter(seller=request.user).order_by('-created_time')

    # Paginate results
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'tartantrade/seller_orders.html', context)



def profile(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)
    cart_data = request.session.get('cart', {})
    cart_items = []

    for item_id in cart_data:
        try:
            item = Item.objects.get(id=item_id)
            cart_items.append(item)
        except Item.DoesNotExist:
            continue

    purchased_products = profile.itemsBought.all()
    posted_products = Item.objects.filter(user=user)
    sold_products = profile.itemsSold.all()
    received_reviews = RatingItem.objects.filter(sendto=user)
    avg_rating = received_reviews.aggregate(avg=Avg("rating"))['avg']
    last_oauth_login = models.DateTimeField(blank=True, null=True)

    # handle upload picture or post review
    if request.method == 'POST':
        if 'profile_picture' in request.FILES:
            profile.picture = request.FILES['profile_picture']
            profile.content_type = request.FILES['profile_picture'].content_type
            profile.save()
            return redirect('profile')

        # submit review to someone else
        rating = request.POST.get("rating")
        rating_message = request.POST.get("rating_message")
        sendto_id = request.POST.get("sendto")

        if rating and rating_message and sendto_id:
            sendto_user = get_object_or_404(User, id=sendto_id)
            already = RatingItem.objects.filter(sendfrom=user, sendto=sendto_user).exists()
            has_bought = Item.objects.filter(user=sendto_user, auction__buyer=user).exists()

            if not already and has_bought:
                RatingItem.objects.create(
                    sendfrom=user,
                    sendto=sendto_user,
                    rating=rating,
                    rating_message=rating_message
                )
        return redirect('profile')

    return render(request, 'tartantrade/my_profile.html', {
        'profile': profile,
        'cart_items': cart_items,
        'purchased_products': purchased_products,
        'posted_products': posted_products,
        'sold_products': sold_products,
        'reviews': received_reviews,
        'avg_rating': avg_rating,
    })

def user_profile(request, user_id):
    # viewing another user's profile
    target_user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(Profile, user=target_user)

    # things they posted
    posted_products = Item.objects.filter(user=target_user)

    # reviews they received
    received_reviews = RatingItem.objects.filter(sendto=target_user)
    avg_rating = received_reviews.aggregate(avg=Avg("rating"))['avg']

    # check if I bought from them
    has_bought = Item.objects.filter(user=target_user, auction__buyer=request.user).exists()
    already_reviewed = RatingItem.objects.filter(sendfrom=request.user, sendto=target_user).exists()

    # I can only review them if I bought and haven’t reviewed yet
    if request.method == 'POST' and has_bought and not already_reviewed:
        rating = request.POST.get("rating")
        rating_message = request.POST.get("rating_message")

        if rating and rating_message:
            RatingItem.objects.create(
                sendfrom=request.user,
                sendto=target_user,
                rating=rating,
                rating_message=rating_message
            )
            return redirect('user_profile', user_id=user_id)

    return render(request, 'tartantrade/user_profile.html', {
        'posted_products': posted_products,
        'reviews': received_reviews,
        'avg_rating': avg_rating,
        'profile': profile,
        'can_review': has_bought and not already_reviewed,
    })



@login_required
@require_POST
def add_to_wishlist(request):
    item_id = request.POST.get("item_id")
    try:
        item = Item.objects.get(id=item_id)
        request.user.profile.wishlist.add(item)
        return JsonResponse({'success': True})
    except Item.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Item not found'})

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required
@require_POST
def toggle_cart(request):
    try:
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))

        if not product_id:
            return JsonResponse({'status': 'error', 'message': 'Missing product ID'}, status=400)

        cart = request.session.get('cart', {})

        if product_id in cart:
            del cart[product_id]
            status = 'removed'
        else:
            cart[product_id] = 1  
            status = 'added'

        request.session['cart'] = cart
        request.session.modified = True

        return JsonResponse({'status': status, 'cart_count': sum(cart.values())})
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)




def my_products(request):
    return render(request, 'tartantrade/base.html')

def seller_products(request):
    return render(request, 'tartantrade/base.html')

def help(request):
    return render(request, 'tartantrade/help_center.html')

def privacy_policy(request):
    return render(request, 'tartantrade/privacy_policy.html')

def about_us(request):
    return  render(request, 'tartantrade/base.html')

def shopping_instructions(request):
    return render(request, 'tartantrade/shopping_instructions.html')


def product_list(request):
    products = Item.objects.all().order_by('-upload_time')  
    context = {
        'products': products
    }
    return render(request, 'tartantrade/product_list_ajax.html', context)




@login_required
def logout_action(request):
    logout(request)
    return redirect("google_login")

@login_required
def chat_view(request):
    chat_user = request.user
    return render(request, 'tartantrade/chat.html', {
        'chat_user': chat_user
    })




# for item page
@login_required
def item_detail(request, id):
    """View for item details - determines if it's an auction or regular item
    and routes to the appropriate view"""
    try:
        item = Item.objects.get(id=id)
        
        # Check if item is an auction
        try:
            auction = Auction.objects.get(item=item)
            # If user is the seller, show seller view
            if request.user == item.user:
                return redirect('auctionItemSeller', id=id)
            else:
                return redirect('auctionItemBuyer', id=id)
        except Auction.DoesNotExist:
            # If it's a regular item
            if request.user == item.user:
                return render(request, 'tartantrade/regularItemSeller.html', {'item': item})
            else:
                return render(request, 'tartantrade/regularItemBuyer.html', {'item': item})
    except Item.DoesNotExist:
        return redirect('home')

@login_required
def auction_buyer(request, id):
    """View for auction item - buyer perspective"""
    try:
        item = Item.objects.get(id=id)
        auction = Auction.objects.get(item=item)
        
        # Prevent seller from accessing buyer view
        if request.user == item.user:
            return redirect('auctionItemSeller', id=id)
        
        context = {
            'item': item,
            'auction': auction,
            'seller': item.user,
        }
        return render(request, 'tartantrade/auctionItemBuyer.html', context)
    except (Item.DoesNotExist, Auction.DoesNotExist):
        return redirect('home')

@login_required
def auction_seller(request, id):
    """View for auction item - seller perspective"""
    try:
        item = Item.objects.get(id=id)
        auction = Auction.objects.get(item=item)
        
        # Prevent non-sellers from accessing seller view
        if request.user != item.user:
            return redirect('auction_buyer', id=id)
        
        context = {
            'item': item,
            'auction': auction,
        }
        return render(request, 'tartantrade/auctionItemSeller.html', context)
    except (Item.DoesNotExist, Auction.DoesNotExist):
        return redirect('home')
    

@login_required
def edit_item(request, id):
    """View for editing an item"""
    try:
        item = Item.objects.get(id=id)

        # Only owner can edit
        if request.user != item.user:
            return redirect('item_detail', id=id)
            
        if request.method == 'POST':
            form = ItemForm(request.POST, request.FILES, instance=item)
            if form.is_valid():
                form.save()
                return redirect('item_detail', id=id)
        else:
            form = ItemForm(instance=item)
            
        context = {
            'form': form,
            'item': item
        }
        return render(request, 'tartantrade/edit_item.html', context)
    except Item.DoesNotExist:
        return redirect('home')

@login_required
def delete_item(request, id):
    """View for deleting an item"""
    try:
        item = Item.objects.get(id=id)
        
        # Only owner can delete
        if request.user != item.user:
            return redirect('item_detail', id=id)
            
        if request.method == 'POST':
            item.delete()
            return redirect('my_products')
        
        context = {'item': item}
        return render(request, 'tartantrade/confirm_delete.html', context)
    except Item.DoesNotExist:
        return redirect('home')

@login_required
def convert_to_auction(request, id):
    """View for converting a regular item to an auction"""
    try:
        item = Item.objects.get(id=id)
        
        # Only owner can convert
        if request.user != item.user:
            return redirect('item_detail', id=id)
            
        # Check if already an auction
        try:
            auction = Auction.objects.get(item=item)
            return redirect('auction_seller', id=id)
        except Auction.DoesNotExist:
            pass
            
        if request.method == 'POST':
            start_price = float(request.POST.get('start_price'))
            buy_now_price = float(request.POST.get('buy_now_price'))
            end_time = request.POST.get('end_time')
            
            # Update item price to buy_now_price
            item.price = buy_now_price
            item.save()
            
            # Create auction
            auction = Auction(
                curr_price=start_price,
                start_price=start_price,
                creation_time=timezone.now(),
                end_time=end_time,
                total_bids=0,
                item=item
            )
            auction.save()
            
            return redirect('auction_seller', id=id)
        
        # If GET, redirect to item detail where the modal is shown
        return redirect('item_detail', id=id)
    except Item.DoesNotExist:
        return redirect('home')

@login_required
def edit_auction(request, id):
    """View for editing an auction"""
    try:
        auction = Auction.objects.get(id=id)
        item = auction.item
        
        # Only owner can edit
        if request.user != item.user:
            return redirect('auction_buyer', id=item.id)
            
        if request.method == 'POST':
            form = AuctionForm(request.POST, instance=auction)
            if form.is_valid():
                form.save()
                return redirect('auction_seller', id=item.id)
        else:
            form = AuctionForm(instance=auction)
            
        context = {
            'form': form,
            'auction': auction,
            'item': item
        }
        return render(request, 'tartantrade/edit_auction.html', context)
    except Auction.DoesNotExist:
        return redirect('home')

@login_required
def cancel_auction(request, id):
    """View for canceling an auction"""
    try:
        auction = Auction.objects.get(id=id)
        item = auction.item
        
        # Only owner can cancel
        if request.user != item.user:
            return redirect('auction_buyer', id=item.id)
            
        # Cannot cancel if bids exist
        if auction.total_bids > 0:
            messages.error(request, "Cannot cancel auction with existing bids.")
            return redirect('auction_seller', id=item.id)
            
        if request.method == 'POST':
            auction.delete()
            return redirect('item_detail', id=item.id)
        
        context = {'auction': auction, 'item': item}
        return render(request, 'tartantrade/confirm_cancel_auction.html', context)
    except Auction.DoesNotExist:
        return redirect('home')

@login_required
def place_bid(request, id):
    """View for placing a bid on an auction"""
    try:
        auction = Auction.objects.get(id=id)
        item = auction.item
        
        # Owner cannot bid on own item
        if request.user == item.user:
            return redirect('auction_seller', id=item.id)
            
        # Cannot bid if auction ended
        if auction.end_time < timezone.now():
            messages.error(request, "This auction has ended.")
            return redirect('auction_buyer', id=item.id)
            
        if request.method == 'POST':
            bid_amount = float(request.POST.get('bid_amount'))
            
            # Validate bid amount
            if bid_amount <= auction.curr_price:
                messages.error(request, "Bid must be higher than current price.")
                return redirect('auction_buyer', id=item.id)
                
            # Update auction
            auction.curr_price = bid_amount
            auction.buyer = request.user
            auction.total_bids += 1
            auction.save()
            
            messages.success(request, "Your bid has been placed successfully!")
            return redirect('auction_buyer', id=item.id)
        
        return redirect('auction_buyer', id=item.id)
    except Auction.DoesNotExist:
        return redirect('home')

@login_required
def buy_now(request, id):
    """View for buying an item immediately"""
    try:
        item = Item.objects.get(id=id)
        
        # Owner cannot buy own item
        if request.user == item.user:
            return redirect('item_detail', id=id)
            
        if request.method == 'POST':
            # Create order
            import time
            import random
            timestamp = int(time.time())
            order_number = f'ORDER{timestamp}_{random.randint(1000, 9999)}'
            
            order = Order.objects.create(
                order_number=order_number,
                status='pending',
                total_price=item.price,
                payment_method='Credit Card',  # Default, can be changed
                buyer=request.user,
                seller=item.user,
                item=item,
                shipping_address='Default Address'  # Should be updated with actual address
            )
            
            messages.success(request, "Purchase successful! The seller will be notified.")
            return redirect('my_orders')
        
        return redirect('item_detail', id=id)
    except Item.DoesNotExist:
        return redirect('home')

@login_required
def add_to_list(request, id):
    """View for adding an item to watchlist"""
    try:
        item = Item.objects.get(id=id)
        
        # Owner cannot add own item to watchlist
        if request.user == item.user:
            return redirect('item_detail', id=id)
            
        if request.method == 'POST':
            # Get or create user profile
            profile, created = Profile.objects.get_or_create(user=request.user)
            
            # Add to watchlist
            profile.items_save.add(item)
            
            messages.success(request, "Item added to your watchlist!")
            return redirect('item_detail', id=id)
        
        return redirect('item_detail', id=id)
    except Item.DoesNotExist:
        return redirect('home')

@login_required
def send_message(request, user_id):
    """View for sending a message to another user"""
    try:
        receiver = User.objects.get(id=user_id)
        
        # Cannot message yourself
        if request.user == receiver:
            return redirect('home')
            
        if request.method == 'POST':
            message_text = request.POST.get('message')
            
            # Create message
            chat_message = ChatMessage.objects.create(
                message=message_text,
                send_from=request.user,
                send_to=receiver,
                is_read=False
            )
            
            messages.success(request, f"Message sent to {receiver.username}!")
            return redirect('chat_view')
        
        return redirect('home')
    except User.DoesNotExist:
        return redirect('home')


@login_required
def post_product(request):
    """View for posting a new product (regular item or auction)"""
    if request.method == 'POST':
        # Handle form submission
        item_form = ItemForm(request.POST, request.FILES)
        
        if item_form.is_valid():
            # Create item instance but don't save to database yet
            item = item_form.save(commit=False)
            item.user = request.user
            item.upload_time = timezone.now()
            
            # Handle content type of the image
            if 'picture' in request.FILES:
                picture = request.FILES['picture']
                item.content_type = picture.content_type
            
            # Save the item
            item.save()
            
            # Check if it's an auction
            is_auction = request.POST.get('is_auction')
            if is_auction:
                try:
                    # Retrieve start price and end time from POST data
                    start_price = float(request.POST.get('start_price'))
                    end_time = request.POST.get('end_time')
                    
                    # Create auction object
                    auction = Auction(
                        curr_price=start_price,
                        start_price=start_price,
                        buyer=None,  # Initially no buyer
                        creation_time=timezone.now(),
                        end_time=end_time,
                        total_bids=0,
                        item=item
                    )
                    auction.save()
                    
                    messages.success(request, 'Your auction has been posted successfully!')
                    return redirect('auction_seller', id=item.id)
                except Exception as e:
                    # If auction creation fails, delete the item
                    item.delete()
                    messages.error(request, f'Error creating auction: {str(e)}')
                    return render(request, 'tartantrade/post_product.html', {'form': item_form})
            else:
                messages.success(request, 'Your product has been posted successfully!')
                return redirect('home')
        else:
            # Form validation failed
            messages.error(request, 'Please correct the errors below.')
    else:
        # Display a blank form
        item_form = ItemForm()
    
    return render(request, 'tartantrade/post_product.html', {
        'form': item_form,
    })