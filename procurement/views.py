"""
CropConnect - Views
"""
from datetime import date, timedelta
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F, Sum, Count
from django.http import HttpResponse
from django.utils import timezone

from .models import (
    User, Farmer, LandDetails, Crop, Slot, SlotBooking,
    Procurement, Bill, Payment, Announcement, BuyerOffer, Buyer
)
from .forms import FarmerRegistrationForm, SlotBookingForm, ProcurementValidationForm, MSPUpdateForm
from .decorators import farmer_required, officer_required, admin_required
from .utils import generate_pdf_invoice


# ============ Public Views ============

def home(request):
    """Root URL.

    Visitors see the public information page FIRST (MSP rates, how it works,
    what needs login, trust & safety). Deal details, buyer names and personal
    data stay behind login. Logged-in users go straight to their dashboard.
    """
    if not request.user.is_authenticated:
        return _public_home(request)
    # Redirect to role-specific dashboard
    role = request.user.role
    if role == User.Role.FARMER:
        return redirect('farmer_dashboard')
    elif role == User.Role.OFFICER:
        return redirect('officer_dashboard')
    elif role == User.Role.ADMIN:
        return redirect('admin_dashboard')
    elif role == User.Role.BUYER:
        return redirect('buyer_dashboard')
    return redirect('login')



def home(request):
    """Display the public homepage to every visitor."""
    today = date.today()

    crops = list(Crop.objects.filter(is_active=True))

    for crop in crops:
        crop.active_offer_count = BuyerOffer.objects.filter(
            crop=crop,
            status=BuyerOffer.Status.ACTIVE,
            valid_from__lte=today,
            valid_until__gte=today,
        ).count()

    announcements = Announcement.objects.filter(
        is_active=True
    )[:3]

    return render(request, 'home.html', {
        'crops': crops,
        'announcements': announcements,
    })


def about(request):
    return render(request, 'about.html')


def contact(request):
    return render(request, 'contact.html')


def login_view(request):
    """Unified login — redirects to role-specific dashboard after login."""
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    crops = Crop.objects.filter(is_active=True)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            if user.role == User.Role.BUYER:
                if hasattr(user, 'buyer_profile'):
                    from .models import Buyer
                    if user.buyer_profile.status == Buyer.Status.PENDING:
                        messages.warning(request, 'Your buyer account is pending admin approval. Please wait 24 hours.')
                        return render(request, 'login.html', {'crops': crops})
                    elif user.buyer_profile.status == Buyer.Status.BLOCKED:
                        messages.error(request, 'Your account has been blocked. Contact admin: 6304629308.')
                        return render(request, 'login.html', {'crops': crops})
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}! 👋')
            return _redirect_by_role(user)
        messages.error(request, 'Invalid username or password. Please try again.')
    return render(request, 'login.html', {'crops': crops})


def _redirect_by_role(user):
    """Return redirect response based on user role."""
    if user.role == User.Role.FARMER:
        return redirect('farmer_dashboard')
    elif user.role == User.Role.OFFICER:
        return redirect('officer_dashboard')
    elif user.role == User.Role.ADMIN:
        return redirect('admin_dashboard')
    elif user.role == User.Role.BUYER:
        return redirect('buyer_dashboard')
    return redirect('login')


def farmer_login(request):
    """Farmer-specific login page."""
    return login_view(request)


def officer_login(request):
    """Officer login - same as unified login."""
    return login_view(request)


def admin_login(request):
    """Admin login - same as unified login."""
    return login_view(request)


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


def farmer_register(request):
    """Farmer registration."""
    if request.user.is_authenticated:
        return redirect('farmer_dashboard')
    if request.method == 'POST':
        form = FarmerRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registration successful! Please login.')
            return redirect('farmer_login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FarmerRegistrationForm()
    return render(request, 'farmer/register.html', {'form': form})


# ============ Farmer Views ============

@farmer_required
@farmer_required
def farmer_dashboard(request):
    """Farmer dashboard with bookings and status."""
    farmer = request.user.farmer_profile
    # Use full queryset for counts, slice only for recent list
    all_bookings = farmer.bookings.select_related('slot', 'slot__crop').order_by('-created_at')
    bookings = all_bookings[:10]
    pending_bookings = all_bookings.filter(status=SlotBooking.Status.PENDING).count()
    approved_bookings = all_bookings.filter(status=SlotBooking.Status.APPROVED).count()
    context = {
        'farmer': farmer,
        'bookings': bookings,
        'pending_bookings': pending_bookings,
        'approved_bookings': approved_bookings,
    }
    return render(request, 'farmer/dashboard.html', context)


@farmer_required
def farmer_book_slot(request):
    """Book a procurement slot."""
    farmer = request.user.farmer_profile
    if not farmer.verified:
        messages.warning(request, 'Your account is pending verification. You cannot book slots yet.')
        return redirect('farmer_dashboard')

    if request.method == 'POST':
        form = SlotBookingForm(request.POST)
        if form.is_valid():
            crop = form.cleaned_data['crop']
            selected_date = form.cleaned_data['date']
            estimated = form.cleaned_data['estimated_quintals']

            # Create or reuse a slot for the selected date and crop
            slot, _ = Slot.objects.get_or_create(
                crop=crop,
                date=selected_date,
                defaults={
                    'total_capacity_quintals': Decimal('500.00'),
                    'booked_capacity': Decimal('0.00'),
                    'is_active': True,
                },
            )
            if not slot.is_active:
                messages.error(request, 'Selected date is not active for procurement.')
                return redirect('farmer_book_slot')

            if SlotBooking.objects.filter(farmer=farmer, slot=slot).exists():
                messages.error(request, 'You have already booked this slot.')
                return redirect('farmer_book_slot')
            remaining = slot.total_capacity_quintals - slot.booked_capacity
            if estimated > remaining:
                messages.error(request, f'Only {remaining} quintals capacity available for this slot.')
                return redirect('farmer_book_slot')
            booking = form.save(commit=False)
            booking.farmer = farmer
            booking.slot = slot
            booking.save()
            Slot.objects.filter(pk=slot.pk).update(booked_capacity=F('booked_capacity') + estimated)
            messages.success(request, 'Slot booked successfully! Pending officer approval.')
            return redirect('farmer_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SlotBookingForm()
    return render(request, 'farmer/book_slot.html', {'form': form, 'farmer': farmer})


@farmer_required
def farmer_booking_status(request):
    """View all booking statuses."""
    farmer = request.user.farmer_profile
    bookings = farmer.bookings.select_related('slot', 'slot__crop').order_by('-created_at')
    return render(request, 'farmer/booking_status.html', {'bookings': bookings})


@farmer_required
def farmer_payment_status(request):
    """View payment status for all procurements."""
    farmer = request.user.farmer_profile
    bookings = farmer.bookings.filter(
        status=SlotBooking.Status.COMPLETED
    ).select_related('slot__crop', 'procurement__bill__payment')
    payments = []
    for b in bookings:
        if hasattr(b, 'procurement') and b.procurement and hasattr(b.procurement, 'bill') and b.procurement.bill:
            payments.append(b.procurement.bill.payment)
    bills = Bill.objects.filter(procurement__booking__farmer=farmer).select_related('procurement__booking__slot__crop', 'payment')
    return render(request, 'farmer/payment_status.html', {'bills': bills})


@farmer_required
def farmer_download_invoice(request, bill_id):
    """Download PDF invoice."""
    farmer = request.user.farmer_profile
    bill = get_object_or_404(Bill, pk=bill_id, procurement__booking__farmer=farmer)
    pdf = generate_pdf_invoice(bill)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{bill.bill_number}.pdf"'
    return response


# ============ Officer Views ============

@officer_required
def officer_dashboard(request):
    """Officer dashboard."""
    pending_verifications = LandDetails.objects.filter(verified=False).count()
    pending_bookings = SlotBooking.objects.filter(status=SlotBooking.Status.PENDING).count()
    pending_procurements = Procurement.objects.filter(status=Procurement.Status.PENDING).count()
    recent_bookings = SlotBooking.objects.filter(status=SlotBooking.Status.PENDING).select_related(
        'farmer__user', 'slot__crop'
    )[:10]
    context = {
        'pending_verifications': pending_verifications,
        'pending_bookings': pending_bookings,
        'pending_procurements': pending_procurements,
        'recent_bookings': recent_bookings,
    }
    return render(request, 'officer/dashboard.html', context)


@officer_required
def officer_verify_land(request):
    """Verify farmer land details."""
    lands = LandDetails.objects.filter(verified=False).select_related('farmer__user')
    return render(request, 'officer/verify_land.html', {'lands': lands})


@officer_required
@officer_required
def officer_verify_land_approve(request, land_id):
    land = get_object_or_404(LandDetails, pk=land_id)
    land.verified = True
    land.verified_by = request.user
    land.verified_at = timezone.now()
    land.save()
    farmer = land.farmer
    if farmer.land_details.filter(verified=True).count() == farmer.land_details.count():
        farmer.verified = True
        farmer.save()
    messages.success(request, 'Land verified successfully.')
    return redirect('officer_verify_land')


@officer_required
def officer_approve_booking(request):
    """Approve slot bookings with inline risk assessment."""
    bookings = SlotBooking.objects.filter(status=SlotBooking.Status.PENDING).select_related(
        'farmer__user', 'slot__crop'
    )

    MAX_QTL_PER_ACRE = 25.0

    bookings_with_risk = []
    for booking in bookings:
        farmer = booking.farmer
        land_list = farmer.land_details.all()
        total_land = float(sum(l.total_area_acres for l in land_list)) or 1.0
        estimated = float(booking.estimated_quintals)
        qty_per_acre = estimated / total_land
        allowed_max_qtl = round(MAX_QTL_PER_ACRE * total_land, 2)
        exceeds_govt_limit = qty_per_acre > MAX_QTL_PER_ACRE

        # Determine risk level
        excess_pct = ((qty_per_acre - MAX_QTL_PER_ACRE) / MAX_QTL_PER_ACRE * 100) if exceeds_govt_limit else 0

        if not exceeds_govt_limit:
            risk_level = 'LOW'
            risk_color = 'success'
            risk_icon = '✅'
            risk_msg = f'Within govt limit ({qty_per_acre:.1f} qtl/acre ≤ 25 qtl/acre). Safe to approve.'
        elif excess_pct <= 40:
            risk_level = 'MEDIUM'
            risk_color = 'warning'
            risk_icon = '⚠️'
            risk_msg = (
                f'Exceeds govt limit by {excess_pct:.0f}%. '
                f'Booked {qty_per_acre:.1f} qtl/acre (max 25 qtl/acre). '
                f'Verify land documents before approving.'
            )
        else:
            risk_level = 'HIGH'
            risk_color = 'danger'
            risk_icon = '🚨'
            risk_msg = (
                f'Seriously exceeds govt limit by {excess_pct:.0f}%. '
                f'Booked {qty_per_acre:.1f} qtl/acre (max 25 qtl/acre). '
                f'Max allowed for {total_land:.1f} acres = {allowed_max_qtl} qtl. '
                f'Do NOT approve without physical land verification.'
            )

        bookings_with_risk.append({
            'booking': booking,
            'total_land': total_land,
            'qty_per_acre': round(qty_per_acre, 2),
            'allowed_max_qtl': allowed_max_qtl,
            'exceeds_govt_limit': exceeds_govt_limit,
            'excess_pct': round(excess_pct, 1),
            'risk_level': risk_level,
            'risk_color': risk_color,
            'risk_icon': risk_icon,
            'risk_msg': risk_msg,
        })

    return render(request, 'officer/approve_booking.html', {
        'bookings_with_risk': bookings_with_risk,
        'max_qtl_per_acre': MAX_QTL_PER_ACRE,
    })


@officer_required
def officer_approve_booking_do(request, booking_id):
    action = request.POST.get('action')
    booking = get_object_or_404(SlotBooking, pk=booking_id)
    if action == 'approve':
        booking.status = SlotBooking.Status.APPROVED
        booking.approved_by = request.user
        booking.approved_at = timezone.now()
        booking.save()
        Procurement.objects.get_or_create(booking=booking, defaults={'status': Procurement.Status.PENDING})
        messages.success(request, 'Booking approved.')
    elif action == 'reject':
        booking.status = SlotBooking.Status.REJECTED
        booking.rejection_reason = request.POST.get('reason', '')
        slot = booking.slot
        Slot.objects.filter(pk=slot.pk).update(booked_capacity=F('booked_capacity') - booking.estimated_quintals)
        booking.save()
        messages.success(request, 'Booking rejected.')
    return redirect('officer_approve_booking')


@officer_required
def officer_validate_procurement(request):
    """Validate crop weight and approve procurement."""
    procurements = Procurement.objects.filter(
        status__in=[Procurement.Status.PENDING, Procurement.Status.WEIGHT_VALIDATED],
        booking__status=SlotBooking.Status.APPROVED
    ).select_related('booking__farmer__user', 'booking__slot__crop')
    return render(request, 'officer/validate_procurement.html', {'procurements': procurements})




from .models import Payment as PaymentModel


@officer_required
def officer_validate_weight(request, procurement_id):
    """Validate weight + quality parameters for a procurement."""
    proc = get_object_or_404(Procurement, pk=procurement_id)
    crop_name = proc.booking.slot.crop.name.lower()
    is_paddy = 'paddy' in crop_name

    # Government quality standards
    PADDY_STANDARDS = {
        'moisture_percent':       {'max': 17.0,  'label': 'Moisture',         'unit': '%'},
        'foreign_matter_percent': {'max': 1.0,   'label': 'Foreign Matter',   'unit': '%'},
        'damaged_grains_percent': {'max': 3.0,   'label': 'Damaged Grains',   'unit': '%'},
        'immature_grains_percent':{'max': 3.0,   'label': 'Immature Grains',  'unit': '%'},
        'chalky_grains_percent':  {'max': 5.0,   'label': 'Chalky Grains',    'unit': '%'},
    }
    GROUNDNUT_STANDARDS = {
        'moisture_percent':       {'max': 8.0,   'label': 'Moisture',         'unit': '%'},
        'foreign_matter_percent': {'max': 1.0,   'label': 'Foreign Matter',   'unit': '%'},
        'shelling_percent':       {'min': 70.0,  'label': 'Shelling Outturn', 'unit': '%'},
        'oil_content_percent':    {'min': 45.0,  'label': 'Oil Content',      'unit': '%'},
    }
    standards = PADDY_STANDARDS if is_paddy else GROUNDNUT_STANDARDS

    if request.method == 'POST':
        action = request.POST.get('action', 'approve')

        # Quality rejection
        if action == 'reject_quality':
            proc.status = Procurement.Status.REJECTED
            proc.rejection_reason = request.POST.get('rejection_reason', 'Quality standards not met')
            proc.validated_by = request.user
            proc.validated_at = timezone.now()
            # Save quality readings even on rejection
            _save_quality_fields(proc, request.POST, is_paddy)
            proc.quality_passed = False
            proc.quality_grade = 'REJECTED'
            proc.save()
            # Update booking status
            proc.booking.status = SlotBooking.Status.REJECTED
            proc.booking.rejection_reason = f"Quality rejected: {proc.rejection_reason}"
            proc.booking.save()
            messages.error(request, f'Procurement REJECTED for quality. Farmer notified.')
            return redirect('officer_validate_procurement')

        # Normal approval
        form = ProcurementValidationForm(request.POST, instance=proc)
        if form.is_valid():
            proc.actual_weight_quintals = form.cleaned_data['actual_weight_quintals']
            proc.remarks = form.cleaned_data.get('remarks', '')
            _save_quality_fields(proc, request.POST, is_paddy)

            # Auto-check quality and determine grade
            failures = _check_quality(request.POST, standards, is_paddy)
            if failures:
                proc.quality_passed = False
                proc.quality_grade = 'BELOW_FAQ'
            else:
                proc.quality_passed = True
                proc.quality_grade = 'FAQ'

            proc.status = Procurement.Status.APPROVED
            proc.validated_by = request.user
            proc.validated_at = timezone.now()
            proc.save()

            crop = proc.booking.slot.crop
            msp = crop.msp_per_quintal

            # Apply deduction if quality below standard
            deduction = 0
            if not proc.quality_passed:
                deduction = int(msp * Decimal('0.05'))  # 5% deduction for below FAQ
                messages.warning(request, f'Quality below FAQ standards. 5% deduction applied (₹{deduction}/qtl).')

            final_msp = msp - deduction
            total = proc.actual_weight_quintals * final_msp
            bill_num = f'BL-{proc.id}-{date.today().strftime("%Y%m%d")}'
            bill = Bill.objects.create(
                procurement=proc,
                bill_number=bill_num,
                total_amount=total,
                msp_per_quintal=final_msp,
                quantity_quintals=proc.actual_weight_quintals
            )
            PaymentModel.objects.create(bill=bill)
            proc.booking.status = SlotBooking.Status.COMPLETED
            proc.booking.save()
            messages.success(request, f'Procurement approved. Bill ₹{total:,.0f} generated for {proc.actual_weight_quintals} qtl @ ₹{final_msp}/qtl.')
            return redirect('officer_validate_procurement')
    else:
        form = ProcurementValidationForm(instance=proc)

    return render(request, 'officer/validate_weight_form.html', {
        'form': form,
        'proc': proc,
        'is_paddy': is_paddy,
        'standards': standards,
        'crop_name': proc.booking.slot.crop.name,
    })


def _save_quality_fields(proc, post, is_paddy):
    """Save quality readings from POST data to procurement instance."""
    def to_decimal(val):
        try:
            from decimal import Decimal
            return Decimal(str(val)) if val else None
        except Exception:
            return None

    proc.moisture_percent       = to_decimal(post.get('moisture_percent'))
    proc.foreign_matter_percent = to_decimal(post.get('foreign_matter_percent'))
    if is_paddy:
        proc.damaged_grains_percent  = to_decimal(post.get('damaged_grains_percent'))
        proc.immature_grains_percent = to_decimal(post.get('immature_grains_percent'))
        proc.chalky_grains_percent   = to_decimal(post.get('chalky_grains_percent'))
    else:
        proc.shelling_percent    = to_decimal(post.get('shelling_percent'))
        proc.oil_content_percent = to_decimal(post.get('oil_content_percent'))
        proc.aflatoxin_present   = post.get('aflatoxin_present') == 'yes'


def _check_quality(post, standards, is_paddy):
    """Return list of quality failures."""
    failures = []
    for field, rule in standards.items():
        val = post.get(field)
        if not val:
            continue
        try:
            v = float(val)
            if 'max' in rule and v > rule['max']:
                failures.append(f"{rule['label']} {v}{rule['unit']} exceeds max {rule['max']}{rule['unit']}")
            if 'min' in rule and v < rule['min']:
                failures.append(f"{rule['label']} {v}{rule['unit']} below min {rule['min']}{rule['unit']}")
        except ValueError:
            pass
    if not is_paddy and post.get('aflatoxin_present') == 'yes':
        failures.append("Aflatoxin contamination detected — automatic rejection")
    return failures


# ============ Admin Views ============

@admin_required
def admin_dashboard(request):
    """Admin dashboard with statistics."""
    total_farmers = Farmer.objects.count()
    total_bookings = SlotBooking.objects.count()
    total_procurements = Procurement.objects.filter(status=Procurement.Status.APPROVED).count()
    total_amount = Bill.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0')
    pending_payments = PaymentModel.objects.filter(status=PaymentModel.Status.PENDING).count()
    crop_stats = []
    for c in Crop.objects.filter(is_active=True):
        bills = Bill.objects.filter(procurement__booking__slot__crop=c)
        tot = bills.aggregate(s=Sum('total_amount'))['s'] or 0
        crop_stats.append({'name': c.name, 'total_amt': tot})
    context = {
        'total_farmers': total_farmers,
        'total_bookings': total_bookings,
        'total_procurements': total_procurements,
        'total_amount': total_amount,
        'pending_payments': pending_payments,
        'pending_buyers': Buyer.objects.filter(status=Buyer.Status.PENDING).count(),
        'pending_land': LandDetails.objects.filter(verified=False).count(),
        'pending_bookings': SlotBooking.objects.filter(status=SlotBooking.Status.PENDING).count(),
        'crop_stats': crop_stats,
    }
    return render(request, 'admin/dashboard.html', context)


@admin_required
def admin_manage_users(request):
    """Manage users (Farmers, Officers, Admins)."""
    users = User.objects.select_related().order_by('-date_joined')
    role_counts = {r: User.objects.filter(role=r).count() for r in ['FARMER', 'OFFICER', 'ADMIN', 'BUYER']}
    return render(request, 'admin/manage_users.html', {'users': users, 'role_counts': role_counts})


@admin_required
def admin_set_msp(request):
    """Set/Update MSP for crops."""
    crops = Crop.objects.filter(is_active=True)
    if request.method == 'POST':
        crop_id = request.POST.get('crop_id')
        msp = request.POST.get('msp_per_quintal')
        if crop_id and msp:
            crop = get_object_or_404(Crop, pk=crop_id)
            crop.msp_per_quintal = msp
            crop.save()
            messages.success(request, f'MSP for {crop.name} updated to ₹{msp}/quintal.')
    return render(request, 'admin/set_msp.html', {'crops': crops})


@admin_required
def admin_reports(request):
    """Reports and analytics."""
    return render(request, 'admin/reports.html')


@admin_required
def admin_approve_payments(request):
    """Approve pending payments."""
    payments = PaymentModel.objects.filter(status=PaymentModel.Status.PENDING).select_related(
        'bill__procurement__booking__farmer__user',
        'bill__procurement__booking__slot__crop',
        'bill__procurement__booking__farmer',
    )
    processed_payments = PaymentModel.objects.filter(
        status__in=[PaymentModel.Status.APPROVED, PaymentModel.Status.TRANSFERRED, PaymentModel.Status.REJECTED]
    ).select_related(
        'bill__procurement__booking__farmer__user',
        'bill__procurement__booking__slot__crop',
        'approved_by',
    ).order_by('-approved_at')[:20]

    return render(request, 'admin/approve_payments.html', {
        'payments': payments,
        'processed_payments': processed_payments,
    })


@admin_required
def admin_approve_payment_do(request, payment_id):
    payment = get_object_or_404(PaymentModel, pk=payment_id)
    action = request.POST.get('action')
    if action == 'approve':
        payment.status = PaymentModel.Status.TRANSFERRED
        payment.approved_by = request.user
        payment.approved_at = timezone.now()
        payment.utr_number = request.POST.get('utr_number', '')
        payment.remarks = request.POST.get('remarks', '')
        payment.save()
        farmer_name = payment.bill.procurement.booking.farmer.user.get_full_name() or \
                      payment.bill.procurement.booking.farmer.user.username
        messages.success(request, f'Payment of ₹{payment.bill.total_amount} approved for {farmer_name}. Status: Transferred.')
    elif action == 'reject':
        remarks = request.POST.get('remarks', '').strip()
        if not remarks:
            messages.error(request, 'Rejection reason is required. Farmer must know why their payment was rejected.')
            return redirect('admin_approve_payments')
        payment.status = PaymentModel.Status.REJECTED
        payment.remarks = remarks
        payment.approved_by = request.user
        payment.approved_at = timezone.now()
        payment.save()
        farmer_name = payment.bill.procurement.booking.farmer.user.get_full_name() or \
                      payment.bill.procurement.booking.farmer.user.username
        messages.warning(request, f'Payment rejected for {farmer_name}. Reason saved and visible to farmer.')
    return redirect('admin_approve_payments')
