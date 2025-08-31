from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from listings.models import Listing, Booking, Review
from django.utils import timezone
from datetime import timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = "Seed the database with users, listings, bookings, and reviews"

    def handle(self, *args, **kwargs):
        self.stdout.write("🌱 Seeding the database...")

        # 1. Create Users
        users = []
        for i in range(3):
            username = f"user{i}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@example.com",
                    "phone_number": f"050000000{i}"
                }
            )
            if created:
                user.set_password("password123")
                user.save()
            users.append(user)

        # 2. Create Listings for each User
        listings = []
        for user in users:
            for j in range(2):
                listing = Listing.objects.create(
                    user=user,
                    title=f"{user.username}'s Listing {j+1}",
                    price=random.randint(100, 1000),
                    description="Nice place to stay",
                    location=random.choice(["Accra", "Kumasi", "Tamale", "Takoradi"]),
                )
                listings.append(listing)

        # 3. Create Bookings for Listings
        bookings = []
        for listing in listings:
            start_date = timezone.now().date() + timedelta(days=random.randint(1, 10))
            end_date = start_date + timedelta(days=random.randint(2, 5))
            guest = random.choice(users)
            booking = Booking.objects.create(
                listing=listing,
                host=listing.user,
                status=random.choice(["confirmed", "pending", "cancelled"]),
                start_date=start_date,
                end_date=end_date,
            )
            bookings.append(booking)

        # 4. Create Reviews for Bookings
        for booking in bookings:
            reviewer = random.choice(users)
            Review.objects.create(
                booking=booking,
                listing=booking.listing,
                user=reviewer,
                rating=random.randint(1, 5),
                comment="Great experience!",
            )

        self.stdout.write(self.style.SUCCESS("✅ Successfully seeded users, listings, bookings, and reviews."))
