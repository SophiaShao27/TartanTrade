from django.db import models
from django.contrib.auth.models import User
    
class Item(models.Model):

    title = models.CharField(max_length=30, default='Untitled')
    description = models.CharField(max_length=200)
    condition = models.CharField(max_length=200)
    categories = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="items") 
    picture = models.FileField(blank=True)
    content_type = models.CharField(max_length=255, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    upload_time = models.DateTimeField(auto_now_add=True)
    delivery_choice = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    pickup_location = models.CharField(max_length=200)

    def __str__(self):
        return f"Item(id={self.id}, seller={self.user.username})"

class Auction(models.Model):
    curr_price = models.DecimalField(max_digits=10, decimal_places=2)
    start_price = models.DecimalField(max_digits=10, decimal_places=2)
    buyer = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    creation_time = models.DateTimeField()
    end_time = models.DateTimeField()
    total_bids = models.IntegerField(default=0)
    # solve unresolved reference
    item = models.OneToOneField(Item, on_delete=models.PROTECT)

    def __str__(self):
        return f"Entry(id={self.id})"


class RatingItem(models.Model):
    rating = models.IntegerField()  
    rating_message = models.CharField(max_length=200)
    sendfrom = models.ForeignKey(User, on_delete=models.PROTECT, related_name="ratings_sent")  
    sendto = models.ForeignKey(User, on_delete=models.PROTECT, related_name="ratings_received") 

    def __str__(self):
        return f"Rating(id={self.id}, from={self.sendfrom.username}, to={self.sendto.username})"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    picture = models.FileField(blank=True)
    content_type = models.CharField(max_length=50)
    itemsSold = models.ManyToManyField(Item, related_name = "selling")
    itemsBought = models.ManyToManyField(Item, related_name = "buying")
    itemsfav = models.ManyToManyField(Item, related_name = "saveforlater")
    rating = models.ManyToManyField(RatingItem, related_name = "ratings")
    cart = models.ManyToManyField(Item, related_name='in_carts', blank=True)



    def __str__(self):
        return 'id=' + str(self.id)


class ReportItem(models.Model):
    reason          = models.CharField(max_length=200)
    report_time = models.DateTimeField()
    send_from          = models.ForeignKey(User, on_delete=models.PROTECT, related_name="report_from")
    send_to          = models.ForeignKey(User, on_delete=models.PROTECT, related_name="report_to")

    def __str__(self):
        return f"Entry(id={self.id})"


class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    order_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    created_time = models.DateTimeField(auto_now_add=True)
    paid_time = models.DateTimeField(null=True, blank=True)
    buyer = models.ForeignKey(User, on_delete=models.PROTECT, related_name='orders_as_buyer')
    seller = models.ForeignKey(User, on_delete=models.PROTECT, related_name='orders_as_seller')
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='orders')
    shipping_address = models.CharField(max_length=200)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_time']

    def __str__(self):
        return f"Order {self.order_number} ({self.get_status_display()})"

class ChatMessage(models.Model):
    message = models.TextField()
    creation_time = models.DateTimeField(auto_now_add=True)
    send_from = models.ForeignKey(User, on_delete=models.PROTECT, related_name="chat_from")
    send_to = models.ForeignKey(User, on_delete=models.PROTECT, related_name="chat_to")
    order_info = models.JSONField(null=True, blank=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['creation_time']

    def __str__(self):
        return f"Entry(id={self.id})"

class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    order_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    created_time = models.DateTimeField(auto_now_add=True)
    paid_time = models.DateTimeField(null=True, blank=True)
    buyer = models.ForeignKey(User, on_delete=models.PROTECT, related_name='orders_as_buyer')
    seller = models.ForeignKey(User, on_delete=models.PROTECT, related_name='orders_as_seller')
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='orders')
    shipping_address = models.CharField(max_length=200)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_time']

    def __str__(self):
        return f"Order {self.order_number} ({self.get_status_display()})"

