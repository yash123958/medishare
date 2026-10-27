from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import date


# 👤 CUSTOM USER
class User(AbstractUser):
    ROLE_CHOICES = (
        ('DONOR', 'Donor'),
        ('NGO', 'NGO'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='DONOR')

    # optional fields (safe)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    ngo_name = models.CharField(max_length=200, blank=True, null=True)

    # 🏛️ Institutional NGO Verification & Regulatory Credentials
    NGO_STATUS_CHOICES = (
        ('PENDING', 'Pending Verification'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    ngo_reg_number = models.CharField(max_length=100, blank=True, null=True)
    ngo_document = models.FileField(upload_to='ngo_documents/', blank=True, null=True)
    is_verified_ngo = models.BooleanField(default=False)
    ngo_verification_status = models.CharField(max_length=20, choices=NGO_STATUS_CHOICES, default='PENDING')


# 💊 MEDICINE DONATION
class MedicineDonation(models.Model):

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    PACKAGING_CHOICES = [
        ('SEALED_BLISTER', 'Original Sealed Blister/Strip'),
        ('INTACT_BOTTLE', 'Unopened Bottle with Intact Seal'),
        ('ORIGINAL_BOX', 'Original Intact Box/Vial Pack'),
        ('OPENED_DAMAGED', 'Opened or Damaged Packaging (Ineligible)'),
    ]

    STORAGE_CHOICES = [
        ('ROOM_TEMPERATURE', 'Room Temperature (< 25°C)'),
        ('COLD_CHAIN', 'Refrigerated / Cold Chain (2°C - 8°C)'),
        ('COOL_DRY', 'Cool & Dry Place (< 30°C)'),
    ]

    donor = models.ForeignKey(User, on_delete=models.CASCADE)

    medicine_name = models.CharField(max_length=100)
    quantity = models.IntegerField()

    expiry_date = models.DateField()
    city = models.CharField(max_length=100)

    # 🔬 Clinical Verification & Authenticity
    batch_number = models.CharField(max_length=50, blank=True, null=True, default='')
    manufacturer = models.CharField(max_length=100, blank=True, null=True, default='')
    packaging_condition = models.CharField(max_length=30, choices=PACKAGING_CHOICES, default='SEALED_BLISTER')
    is_opened = models.BooleanField(default=False)
    storage_conditions = models.CharField(max_length=30, choices=STORAGE_CHOICES, default='ROOM_TEMPERATURE')
    prescription_required = models.BooleanField(default=False)
    authenticity_declared = models.BooleanField(default=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

    # optional image
    image = models.ImageField(upload_to='medicine_images/', blank=True, null=True)

    def days_left(self):
        return (self.expiry_date - date.today()).days


# 📦 MEDICINE REQUEST (🔥 TRACKING ADDED HERE)
class MedicineRequest(models.Model):

    STATUS_CHOICES = [
        ('REQUESTED', 'Requested'),
        ('APPROVED', 'Approved'),
        ('PACKED', 'Packed'),
        ('SHIPPED', 'Shipped'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),
        ('REJECTED', 'Rejected'),
    ]

    ngo = models.ForeignKey(User, on_delete=models.CASCADE)
    donation = models.ForeignKey(MedicineDonation, on_delete=models.CASCADE)

    quantity = models.IntegerField(default=1)

    reason = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='REQUESTED'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ngo.username} - {self.donation.medicine_name} ({self.status})"