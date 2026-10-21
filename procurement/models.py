"""
CropConnect - Database Models
"""
import re
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


# Aadhaar format: 12 digits, can have spaces
AADHAAR_REGEX = re.compile(r'^\d{4}\s?\d{4}\s?\d{4}$|^\d{12}$')


def validate_aadhaar(value):
    """Validate Indian Aadhaar format (12 digits, optional spaces)."""
    clean = ''.join(str(value).split())
    if len(clean) != 12 or not clean.isdigit():
        raise ValueError('Aadhaar must be 12 digits.')
    return value


class User(AbstractUser):
    """Extended User with role-based access."""
    class Role(models.TextChoices):
        FARMER = 'FARMER', 'Farmer'
        OFFICER = 'OFFICER', 'Procurement Officer'
        ADMIN = 'ADMIN', 'Administrator'
        BUYER = 'BUYER', 'Private Buyer'

    role = models.CharField(max_length=10, choices=Role.choices)
    phone = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'procurement_user'


class Farmer(models.Model):
    """Farmer profile linked to User."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='farmer_profile')
    aadhaar = models.CharField(max_length=14, unique=True, validators=[validate_aadhaar])
    bank_name = models.CharField(max_length=100)
    bank_account_no = models.CharField(max_length=30)
    bank_ifsc = models.CharField(max_length=15)
    village = models.CharField(max_length=100)
    mandal = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100, default='Andhra Pradesh')
    pincode = models.CharField(max_length=6)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'procurement_farmer'


class LandDetails(models.Model):
    """Land details for farmer verification."""
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='land_details')
    survey_no = models.CharField(max_length=50)
    total_area_acres = models.DecimalField(max_digits=8, decimal_places=2)
    village = models.CharField(max_length=100)
    mandal = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_lands')
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'procurement_land_details'
        constraints = [
            models.UniqueConstraint(fields=['farmer', 'survey_no'], name='unique_farmer_survey')
        ]


class Crop(models.Model):
    """Crop types with MSP (Minimum Support Price)."""
    name = models.CharField(max_length=50, unique=True)  # Paddy, Groundnut
    msp_per_quintal = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, default='Quintal')
    season = models.CharField(max_length=50, blank=True)  # Kharif, Rabi
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'procurement_crop'


class Slot(models.Model):
    """Available slots for procurement."""
    date = models.DateField()
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='slots')
    total_capacity_quintals = models.DecimalField(max_digits=10, decimal_places=2)
    booked_capacity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'procurement_slot'
        constraints = [
            models.UniqueConstraint(fields=['date', 'crop'], name='unique_slot_date_crop')
        ]
        ordering = ['date']

    def __str__(self):
        return f"{self.date} - {self.crop.name}"


class SlotBooking(models.Model):
    """Farmer's slot booking."""
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Approval'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='bookings')
    slot = models.ForeignKey(Slot, on_delete=models.CASCADE, related_name='bookings')
    estimated_quintals = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_bookings')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'procurement_slot_booking'
        constraints = [
            models.UniqueConstraint(fields=['farmer', 'slot'], name='unique_farmer_slot_booking')
        ]


class Procurement(models.Model):
    """Actual procurement record after farmer brings produce."""
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        WEIGHT_VALIDATED = 'WEIGHT_VALIDATED', 'Weight Validated'
        APPROVED = 'APPROVED', 'Procurement Approved'
        REJECTED = 'REJECTED', 'Rejected'

    booking = models.OneToOneField(SlotBooking, on_delete=models.CASCADE, related_name='procurement')
    actual_weight_quintals = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    validated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='validated_procurements')
    validated_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    # ── Quality Parameters (officer fills on procurement day) ──
    # Common for both Paddy & Groundnut
    moisture_percent      = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Moisture content %")
    foreign_matter_percent= models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Foreign matter %")
    quality_grade         = models.CharField(max_length=10, blank=True, help_text="FAQ / Grade A / Grade B / Rejected")
    quality_passed        = models.BooleanField(default=True, help_text="Overall quality passed or failed")
    rejection_reason      = models.TextField(blank=True, help_text="Quality rejection reason if failed")

    # Paddy-specific
    damaged_grains_percent= models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    immature_grains_percent= models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    chalky_grains_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Groundnut-specific
    shelling_percent      = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Shelling outturn %")
    oil_content_percent   = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    aflatoxin_present     = models.BooleanField(default=False, help_text="Aflatoxin contamination detected")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'procurement_procurement'


class Bill(models.Model):
    """Generated bill for procurement."""
    procurement = models.OneToOneField(Procurement, on_delete=models.CASCADE, related_name='bill')
    bill_number = models.CharField(max_length=50, unique=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    msp_per_quintal = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_quintals = models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'procurement_bill'


class Payment(models.Model):
    """Payment record for bills."""
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        TRANSFERRED = 'TRANSFERRED', 'Transferred to Bank'
        REJECTED = 'REJECTED', 'Rejected'

    bill = models.OneToOneField(Bill, on_delete=models.CASCADE, related_name='payment')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_payments')
    approved_at = models.DateTimeField(null=True, blank=True)
    utr_number = models.CharField(max_length=50, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'procurement_payment'


class Announcement(models.Model):
    """News/Announcements for the portal."""
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'procurement_announcement'
        ordering = ['-created_at']


# ═══════════════════════════════════════════════════════════
# DUAL CHANNEL PROCUREMENT — BUYER MARKETPLACE
# ═══════════════════════════════════════════════════════════

class Buyer(models.Model):
    """Private buyer — rice mill, wholesaler, exporter."""
    class BuyerType(models.TextChoices):
        RICE_MILL    = 'RICE_MILL',   'Rice Mill'
        WHOLESALER   = 'WHOLESALER',  'Wholesaler'
        EXPORTER     = 'EXPORTER',    'Exporter'
        PROCESSOR    = 'PROCESSOR',   'Food Processor'

    class Status(models.TextChoices):
        PENDING  = 'PENDING',  'Pending Approval'
        APPROVED = 'APPROVED', 'Approved'
        BLOCKED  = 'BLOCKED',  'Blocked'

    user         = models.OneToOneField(User, on_delete=models.CASCADE, related_name='buyer_profile')
    company_name = models.CharField(max_length=200)
    buyer_type   = models.CharField(max_length=20, choices=BuyerType.choices)
    license_no   = models.CharField(max_length=100, blank=True)
    gst_number   = models.CharField(max_length=20, blank=True)
    address      = models.TextField()
    district     = models.CharField(max_length=100)
    state        = models.CharField(max_length=100, default='Andhra Pradesh')
    contact_name = models.CharField(max_length=100)
    status       = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    rating       = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    total_deals  = models.IntegerField(default=0)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company_name} ({self.get_buyer_type_display()})"

    class Meta:
        db_table = 'marketplace_buyer'


class BuyerOffer(models.Model):
    """A private buyer posts an offer to buy a crop at a certain price."""
    class Status(models.TextChoices):
        ACTIVE   = 'ACTIVE',   'Active'
        CLOSED   = 'CLOSED',   'Closed'
        EXPIRED  = 'EXPIRED',  'Expired'
        PAUSED   = 'PAUSED',   'Paused'

    buyer              = models.ForeignKey(Buyer, on_delete=models.CASCADE, related_name='offers')
    crop               = models.ForeignKey(Crop,  on_delete=models.CASCADE, related_name='buyer_offers')
    price_per_quintal  = models.DecimalField(max_digits=10, decimal_places=2)
    min_quantity_qtl   = models.DecimalField(max_digits=8,  decimal_places=2, default=1)
    max_quantity_qtl   = models.DecimalField(max_digits=8,  decimal_places=2)
    valid_from         = models.DateField()
    valid_until        = models.DateField()
    pickup_location    = models.CharField(max_length=200)
    description        = models.TextField(blank=True)
    status             = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    advance_percent    = models.IntegerField(default=0, help_text="Advance payment % at time of deal")
    payment_days       = models.IntegerField(default=7,  help_text="Payment within N days of delivery")
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.buyer.company_name} — {self.crop.name} @ ₹{self.price_per_quintal}/qtl"

    @property
    def is_above_msp(self):
        return self.price_per_quintal >= self.crop.msp_per_quintal

    @property
    def premium_over_msp(self):
        return self.price_per_quintal - self.crop.msp_per_quintal

    class Meta:
        db_table = 'marketplace_buyer_offer'
        ordering = ['-price_per_quintal']


class FarmerDeal(models.Model):
    """Farmer accepts a private buyer offer — creates a deal."""
    class Status(models.TextChoices):
        PENDING   = 'PENDING',   'Pending Confirmation'
        CONFIRMED = 'CONFIRMED', 'Confirmed by Buyer'
        DELIVERED = 'DELIVERED', 'Crop Delivered'
        PAID      = 'PAID',      'Payment Done'
        CANCELLED = 'CANCELLED', 'Cancelled'
        DISPUTED  = 'DISPUTED',  'Disputed'

    farmer            = models.ForeignKey(Farmer,     on_delete=models.CASCADE, related_name='deals')
    offer             = models.ForeignKey(BuyerOffer, on_delete=models.CASCADE, related_name='deals')
    quantity_qtl      = models.DecimalField(max_digits=8, decimal_places=2)
    agreed_price      = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount      = models.DecimalField(max_digits=12, decimal_places=2)
    status            = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    delivery_date     = models.DateField(null=True, blank=True)
    delivery_address  = models.CharField(max_length=300, blank=True)
    farmer_notes      = models.TextField(blank=True)
    buyer_notes       = models.TextField(blank=True)
    dispute_reason    = models.TextField(blank=True)
    ai_recommendation = models.TextField(blank=True, help_text="AI advice given when deal was created")
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Deal#{self.pk} — {self.farmer} → {self.offer.buyer.company_name}"

    class Meta:
        db_table = 'marketplace_farmer_deal'
        ordering = ['-created_at']
