# listings/views.py
import uuid
import requests
from django.conf import settings
from .models import Payment
from rest_framework.decorators import action

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from .models import Listing, Booking, Review
from .serializers import ListingSerializer, BookingSerializer, ReviewSerializer
from .tasks import send_payment_confirmation_email, send_payment_failure_email



User = get_user_model()


class ListingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Listing objects.
    Provides CRUD operations for listings.
    """
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'listing_id'

    def perform_create(self, serializer):
        """Set the host to the current user when creating a listing."""
        serializer.save(host=self.request.user)

    def get_permissions(self):
        """
        Instantiate and return the list of permissions that this view requires.
        Only the host can update or delete their own listings.
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

    def get_queryset(self):
        """
        Optionally restricts the returned listings to those owned by the user,
        by filtering against a `host` query parameter in the URL.
        """
        queryset = Listing.objects.all()
        host = self.request.query_params.get('host', None)
        if host is not None:
            queryset = queryset.filter(host__username=host)
        return queryset

    def update(self, request, *args, **kwargs):
        """Only allow hosts to update their own listings."""
        listing = self.get_object()
        if listing.host != request.user:
            return Response(
                {"detail": "You can only update your own listings."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Only allow hosts to delete their own listings."""
        listing = self.get_object()
        if listing.host != request.user:
            return Response(
                {"detail": "You can only delete your own listings."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)




class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'booking_id'

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set the user to the current user when creating a booking and trigger email."""
        listing_id = self.request.data.get('listing')
        try:
            listing = Listing.objects.get(listing_id=listing_id)
            booking = serializer.save(user=self.request.user, listing=listing)
            
            # Trigger asynchronous email task
            send_payment_confirmation_email.delay(booking.booking_id)

        except Listing.DoesNotExist:
            return Response(
                {"detail": "Listing not found."},
                status=status.HTTP_404_NOT_FOUND
            )



class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Review objects.
    Provides CRUD operations for reviews with proper filtering.
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'review_id'

    def get_queryset(self):
        """
        Filter reviews by listing if listing_id is provided in query params.
        """
        queryset = Review.objects.all()
        listing_id = self.request.query_params.get('listing_id', None)
        if listing_id is not None:
            queryset = queryset.filter(listing__listing_id=listing_id)
        return queryset

    def perform_create(self, serializer):
        """Set the user to the current user when creating a review."""
        listing_id = self.request.data.get('listing')
        try:
            listing = Listing.objects.get(listing_id=listing_id)
            serializer.save(user=self.request.user, listing=listing)
        except Listing.DoesNotExist:
            return Response(
                {"detail": "Listing not found."},
                status=status.HTTP_404_NOT_FOUND
            )

    def create(self, request, *args, **kwargs):
        """Override create to handle listing lookup and validation."""
        listing_id = request.data.get('listing')
        if not listing_id:
            return Response(
                {"detail": "Listing ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            listing = Listing.objects.get(listing_id=listing_id)
        except Listing.DoesNotExist:
            return Response(
                {"detail": "Listing not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user already reviewed this listing
        if Review.objects.filter(user=request.user, listing=listing).exists():
            return Response(
                {"detail": "You have already reviewed this listing."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, listing=listing)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """Only allow users to update their own reviews."""
        review = self.get_object()
        if review.user != request.user:
            return Response(
                {"detail": "You can only update your own reviews."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Only allow users to delete their own reviews."""
        review = self.get_object()
        if review.user != request.user:
            return Response(
                {"detail": "You can only delete your own reviews."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """Get all reviews by the current user."""
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        reviews = Review.objects.filter(user=request.user)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)
    



class PaymentViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=["post"])
    def initiate_payment(self, request):
        """
        Initiate a payment with Chapa for a booking.
        """
        booking_id = request.data.get("booking_id")
        try:
            booking = Booking.objects.get(booking_id=booking_id, user=request.user)
        except Booking.DoesNotExist:
            return Response({"detail": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)

        # Ensure no duplicate payment
        if hasattr(booking, "payment"):
            return Response({"detail": "Payment already initiated for this booking."}, status=status.HTTP_400_BAD_REQUEST)

        tx_ref = str(uuid.uuid4())
        amount = str(booking.total_price)

        payload = {
            "amount": amount,
            "currency": settings.CHAPA_CURRENCY,
            "email": request.user.email,
            "first_name": request.user.first_name or "Guest",
            "last_name": request.user.last_name or "",
            "tx_ref": tx_ref,
            "callback_url": settings.CHAPA_CALLBACK_URL,
            "return_url": settings.CHAPA_CALLBACK_URL,  # fallback
        }

        headers = {
            "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            f"{settings.CHAPA_BASE_URL}/transaction/initialize",
            json=payload,
            headers=headers,
        )

        if response.status_code != 200:
            return Response({"detail": "Chapa initialization failed", "error": response.json()}, status=status.HTTP_400_BAD_REQUEST)

        data = response.json()

        # Save payment record
        payment = Payment.objects.create(
            booking=booking,
            amount=booking.total_price,
            transaction_reference=tx_ref,
            status=Payment.PENDING
        )

        return Response({
            "payment_id": str(payment.payment_id),
            "checkout_url": data.get("data", {}).get("checkout_url")
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def verify_payment(self, request):
        """
        Verify a payment with Chapa.
        """
        tx_ref = request.query_params.get("tx_ref")
        if not tx_ref:
            return Response({"detail": "tx_ref is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payment = Payment.objects.get(transaction_reference=tx_ref, booking__user=request.user)
        except Payment.DoesNotExist:
            return Response({"detail": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

        headers = {
            "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
        }

        response = requests.get(
            f"{settings.CHAPA_BASE_URL}/transaction/verify/{tx_ref}",
            headers=headers,
        )

        if response.status_code != 200:
            return Response({"detail": "Verification failed", "error": response.json()}, status=status.HTTP_400_BAD_REQUEST)

        data = response.json()
        status_chapa = data.get("data", {}).get("status")

        if status_chapa == "success":
            payment.status = Payment.COMPLETED
            payment.chapa_transaction_id = data["data"].get("id")
            payment.save()

            booking = payment.booking
            booking.status = Booking.CONFIRMED
            booking.save()

            # Trigger async email notification
            send_payment_confirmation_email.delay(booking.booking_id)

            return Response({"detail": "Payment successful", "status": payment.status})

        else:
            payment.status = Payment.FAILED
            payment.save()

            # Trigger failure email asynchronously
            send_payment_failure_email.delay(payment.booking.booking_id)

            return Response(
                {"detail": "Payment failed", "status": payment.status},
                status=status.HTTP_400_BAD_REQUEST
            )