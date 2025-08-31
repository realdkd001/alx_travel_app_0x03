from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

class User(AbstractUser):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True)
    phone_number = models.CharField(max_length=15, unique=True, null=False)
    
    def __str__(self):
        return self.username

class Listing(models.Model):
    listing_id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True)
    user = models.ForeignKey("User", related_name='listings', on_delete=models.CASCADE)
    title = models.CharField(max_length=300, null=False)
    price = models.DecimalField(max_digits=100, decimal_places=2, null=False)
    description = models.TextField()
    location = models.CharField(max_length=300, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Booking(models.Model):
    booking_id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True)
    listing = models.ForeignKey("Listing", related_name='bookings', on_delete=models.CASCADE)  # Foreign key to Listing
    host = models.ForeignKey("User", related_name='bookings', on_delete=models.CASCADE)  # Foreign key to User (Host)
    status = models.CharField(max_length=50, null=False)
    start_date = models.DateField(null=False)
    end_date = models.DateField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking {self.booking_id} for {self.listing.name}"

class Review(models.Model):
    review_id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True)
    booking = models.ForeignKey("Booking", related_name="reviews", on_delete=models.CASCADE)
    listing = models.ForeignKey("Listing", related_name="reviews", on_delete=models.CASCADE)
    user = models.ForeignKey('User', related_name="reviews", on_delete=models.CASCADE)
    rating = models.IntegerField(null=False)
    comment = models.TextField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} for {self.listing.name}"
