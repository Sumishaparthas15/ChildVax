from django.db import models
from django.contrib.auth.models import AbstractUser


class Profile(AbstractUser):
    email = models.EmailField(unique=True, null=False, blank=False)  # Email is required and unique
    phone_number = models.CharField(max_length=15, null=True, blank=True)  # Optional phone number
    address = models.CharField(max_length=255, null=True, blank=True)
    child_name = models.CharField(max_length=100, null=True, blank=True)
    whatsapp_number = models.CharField(max_length=15, null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    disability = models.BooleanField(default=False)
    disability_description = models.CharField(max_length=255, null=True, blank=True)
    upi_number = models.CharField(max_length=50, null=True, blank=True)
    
   
    
    
    def __str__(self):
        return self.child_name or self.username
class Booking(models.Model):
    STATUS_CHOICES = [
        ('Upcoming', 'Upcoming'),
        ('Cancelled', 'Cancelled'),
        ('Rejected', 'Rejected'),
        ('Refunded', 'Refunded'),
        ('Completed', 'Completed'),
    ]

    # Use 'patient' as the foreign key to Profile
    patient = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='bookings')
    vaccinations = models.CharField(max_length=100)  # You can also use a choice field if needed
    appointment_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    token_number = models.PositiveIntegerField() 
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Upcoming')
    appointment_fee = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.00)
    
    # Fixed payment method to a single value
    payment_method = models.CharField(max_length=10, default='razorpay', editable=False)

    def __str__(self):
        return f"{self.patient.child_name} - {self.vaccinations} on {self.appointment_date}"