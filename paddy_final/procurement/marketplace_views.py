"""
Dual-Channel Buyer Marketplace Views
Farmers can choose: Government MSP  OR  Private Buyer Offer
"""
from datetime import date
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Avg, Sum, Count
from django.utils import timezone

from .models import (
    User, Farmer, Crop, Buyer, BuyerOffer, FarmerDeal, SlotBooking
)
from .decorators import farmer_required, admin_required


# ─────────────────────────────────────────────
# BUYER REGISTRATION & AUTH
# ─────────────────────────────────────────────

def buyer_register(request):
    """Buyer self-registration."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        p = request.POST
        # Basic validation
        if User.objects.filter(username=p.get('username')).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'marketplace/buyer_register.html', {'post': p})
        if p.get('password1') != p.get('password2'):
            messages.error(request, 'Passwords do not match.')
            return render(request, 'marketplace/buyer_register.html', {'post': p})

        user = User.objects.create_user(
            username=p['username'],
            email=p.get('email', ''),
            password=p['password1'],
            first_name=p.get('first_name', ''),
            last_name=p.get('last_name', ''),
            phone=p.get('phone', ''),
            role=User.Role.BUYER,
        )
        Buyer.objects.create(
            user=user,
            company_name=p['company_name'],
            buyer_type=p['buyer_type'],
            license_no=p.get('license_no', ''),
            gst_number=p.get('gst_number', ''),
            address=p['address'],
            district=p['district'],
            state=p.get('state', 'Andhra Pradesh'),
            contact_name=p['contact_name'],
        )
        messages.success(request, 'Registration submitted! Admin will approve your account within 24 hours.')
        return redirect('buyer_login')

    return render(request, 'marketplace/buyer_register.html', {
        'buyer_types': Buyer.BuyerType.choices,
    })


def buyer_login(request):
    from django.contrib.auth import login, authenticate
    if request.user.is_authenticated and request.user.role == User.Role.BUYER:
        return redirect('buyer_dashboard')
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user and user.role == User.Role.BUYER:
            if hasattr(user, 'buyer_profile') and user.buyer_profile.status == Buyer.Status.APPROVED:
                login(request, user)
                return redirect('buyer_dashboard')
            elif hasattr(user, 'buyer_profile') and user.buyer_profile.status == Buyer.Status.PENDING:
                messages.warning(request, 'Your account is pending admin approval.')
            else:
                messages.error(request, 'Your account has been blocked. Contact admin.')
        else:
            messages.error(request, 'Invalid credentials.')
    return render(request, 'marketplace/buyer_login.html')


# ─────────────────────────────────────────────
# BUYER DASHBOARD & OFFER MANAGEMENT
# ─────────────────────────────────────────────

@login_required
def buyer_dashboard(request):
    if request.user.role != User.Role.BUYER:
        return redirect('home')
    buyer = request.user.buyer_profile
    offers = buyer.offers.select_related('crop').order_by('-created_at')
    active_offers = offers.filter(status=BuyerOffer.Status.ACTIVE)
    deals = FarmerDeal.objects.filter(offer__buyer=buyer).select_related(
        'farmer__user', 'offer__crop'
    ).order_by('-created_at')[:10]

    total_deals = FarmerDeal.objects.filter(offer__buyer=buyer).count()
    confirmed_deals = FarmerDeal.objects.filter(offer__buyer=buyer, status__in=['CONFIRMED', 'DELIVERED', 'PAID']).count()
    total_value = FarmerDeal.objects.filter(offer__buyer=buyer, status__in=['DELIVERED', 'PAID']).aggregate(
        s=Sum('total_amount'))['s'] or 0

    return render(request, 'marketplace/buyer_dashboard.html', {
        'buyer': buyer,
        'offers': offers,
        'active_offers': active_offers,
        'deals': deals,
        'total_deals': total_deals,
        'confirmed_deals': confirmed_deals,
        'total_value': total_value,
    })


@login_required
def buyer_create_offer(request):
    if request.user.role != User.Role.BUYER:
        return redirect('home')
    buyer = request.user.buyer_profile
    if buyer.status != Buyer.Status.APPROVED:
        messages.error(request, 'Your account must be approved to post offers.')
        return redirect('buyer_dashboard')

    crops = Crop.objects.filter(is_active=True)
    if request.method == 'POST':
        p = request.POST
        try:
            crop = Crop.objects.get(pk=p['crop_id'])
            offer = BuyerOffer.objects.create(
                buyer=buyer,
                crop=crop,
                price_per_quintal=Decimal(p['price_per_quintal']),
                min_quantity_qtl=Decimal(p.get('min_quantity_qtl', '1')),
                max_quantity_qtl=Decimal(p['max_quantity_qtl']),
                valid_from=p['valid_from'],
                valid_until=p['valid_until'],
                pickup_location=p['pickup_location'],
                description=p.get('description', ''),
                advance_percent=int(p.get('advance_percent', 0)),
                payment_days=int(p.get('payment_days', 7)),
            )
            messages.success(request, f'Offer posted! Farmers can now see your offer for {crop.name} at ₹{offer.price_per_quintal}/qtl.')
            return redirect('buyer_dashboard')
        except Exception as e:
            messages.error(request, f'Error: {e}')

    return render(request, 'marketplace/buyer_create_offer.html', {'crops': crops})


@login_required
def buyer_offer_deals(request, offer_id):
    """Buyer sees all farmer deals for a specific offer."""
    if request.user.role != User.Role.BUYER:
        return redirect('home')
    offer = get_object_or_404(BuyerOffer, pk=offer_id, buyer=request.user.buyer_profile)
    deals = offer.deals.select_related('farmer__user').order_by('-created_at')
    return render(request, 'marketplace/buyer_offer_deals.html', {'offer': offer, 'deals': deals})


@login_required
@require_POST
def buyer_confirm_deal(request, deal_id):
    """Buyer confirms or rejects a farmer's deal request."""
    if request.user.role != User.Role.BUYER:
        return redirect('home')
    deal = get_object_or_404(FarmerDeal, pk=deal_id, offer__buyer=request.user.buyer_profile)
    action = request.POST.get('action')
    if action == 'confirm':
        deal.status = FarmerDeal.Status.CONFIRMED
        deal.buyer_notes = request.POST.get('buyer_notes', '')
        deal.delivery_date = request.POST.get('delivery_date') or None
        deal.delivery_address = request.POST.get('delivery_address', deal.offer.pickup_location)
        deal.save()
        messages.success(request, f'Deal confirmed with {deal.farmer.user.get_full_name()}!')
    elif action == 'cancel':
        deal.status = FarmerDeal.Status.CANCELLED
        deal.buyer_notes = request.POST.get('buyer_notes', '')
        deal.save()
        messages.warning(request, 'Deal cancelled.')
    elif action == 'mark_paid':
        deal.status = FarmerDeal.Status.PAID
        deal.save()
        BuyerOffer.objects.filter(pk=deal.offer.pk).update()
        buyer = request.user.buyer_profile
        buyer.total_deals = FarmerDeal.objects.filter(offer__buyer=buyer, status='PAID').count()
        buyer.save()
        messages.success(request, 'Deal marked as paid!')
    return redirect('buyer_offer_deals', offer_id=deal.offer.pk)


# ─────────────────────────────────────────────
# FARMER — MARKETPLACE (choose channel)
# ─────────────────────────────────────────────

@farmer_required
def farmer_marketplace(request):
    """
    Main marketplace page — farmer sees all active buyer offers
    side-by-side with government MSP. Chooses best channel.
    """
    farmer = request.user.farmer_profile
    crops  = Crop.objects.filter(is_active=True)
    today  = date.today()

    # Active offers grouped by crop
    offers = BuyerOffer.objects.filter(
        status=BuyerOffer.Status.ACTIVE,
        valid_until__gte=today,
        valid_from__lte=today,
    ).select_related('buyer', 'crop').order_by('-price_per_quintal')

    # Farmer's existing deals
    my_deals = FarmerDeal.objects.filter(farmer=farmer).select_related(
        'offer__buyer', 'offer__crop'
    ).order_by('-created_at')[:5]

    # Per-crop comparison data
    crop_comparison = []
    for crop in crops:
        crop_offers = [o for o in offers if o.crop_id == crop.pk]
        best_private = crop_offers[0] if crop_offers else None
        crop_comparison.append({
            'crop':         crop,
            'msp':          crop.msp_per_quintal,
            'best_private': best_private,
            'all_offers':   crop_offers,
            'premium':      (best_private.price_per_quintal - crop.msp_per_quintal) if best_private else None,
        })

    return render(request, 'marketplace/farmer_marketplace.html', {
        'farmer':          farmer,
        'crop_comparison': crop_comparison,
        'my_deals':        my_deals,
        'all_offers':      offers,
    })


@farmer_required
def farmer_offer_detail(request, offer_id):
    """Farmer views full details of a buyer offer + AI recommendation."""
    farmer = request.user.farmer_profile
    offer  = get_object_or_404(BuyerOffer, pk=offer_id, status=BuyerOffer.Status.ACTIVE)

    # AI recommendation
    ai_advice = _get_ai_deal_advice(farmer, offer)

    # Check if already has a deal for this offer
    existing_deal = FarmerDeal.objects.filter(farmer=farmer, offer=offer).first()

    if request.method == 'POST' and not existing_deal:
        qty = Decimal(request.POST.get('quantity_qtl', '0'))
        if qty < offer.min_quantity_qtl:
            messages.error(request, f'Minimum quantity is {offer.min_quantity_qtl} quintals.')
        elif qty > offer.max_quantity_qtl:
            messages.error(request, f'Maximum quantity is {offer.max_quantity_qtl} quintals.')
        else:
            total = qty * offer.price_per_quintal
            deal  = FarmerDeal.objects.create(
                farmer=farmer,
                offer=offer,
                quantity_qtl=qty,
                agreed_price=offer.price_per_quintal,
                total_amount=total,
                farmer_notes=request.POST.get('farmer_notes', ''),
                ai_recommendation=ai_advice,
            )
            messages.success(
                request,
                f'Deal request sent to {offer.buyer.company_name}! '
                f'They will confirm within 24 hours. Expected: ₹{total:,.0f}'
            )
            return redirect('farmer_my_deals')

    return render(request, 'marketplace/farmer_offer_detail.html', {
        'offer':         offer,
        'farmer':        farmer,
        'ai_advice':     ai_advice,
        'existing_deal': existing_deal,
    })


@farmer_required
def farmer_my_deals(request):
    """Farmer sees all their private deals."""
    farmer = request.user.farmer_profile
    deals  = FarmerDeal.objects.filter(farmer=farmer).select_related(
        'offer__buyer', 'offer__crop'
    ).order_by('-created_at')
    return render(request, 'marketplace/farmer_my_deals.html', {
        'farmer': farmer,
        'deals':  deals,
    })


@farmer_required
@require_POST
def farmer_cancel_deal(request, deal_id):
    deal = get_object_or_404(FarmerDeal, pk=deal_id, farmer=request.user.farmer_profile)
    if deal.status == FarmerDeal.Status.PENDING:
        deal.status = FarmerDeal.Status.CANCELLED
        deal.farmer_notes = request.POST.get('reason', '')
        deal.save()
        messages.success(request, 'Deal cancelled.')
    else:
        messages.error(request, 'Cannot cancel a confirmed deal. Contact helpdesk.')
    return redirect('farmer_my_deals')


# ─────────────────────────────────────────────
# ADMIN — BUYER MANAGEMENT
# ─────────────────────────────────────────────

@admin_required
def admin_manage_buyers(request):
    buyers = Buyer.objects.select_related('user').order_by('-created_at')
    return render(request, 'marketplace/admin_manage_buyers.html', {'buyers': buyers})


@admin_required
@require_POST
def admin_approve_buyer(request, buyer_id):
    buyer  = get_object_or_404(Buyer, pk=buyer_id)
    action = request.POST.get('action')
    if action == 'approve':
        buyer.status = Buyer.Status.APPROVED
        buyer.save()
        messages.success(request, f'{buyer.company_name} approved.')
    elif action == 'block':
        buyer.status = Buyer.Status.BLOCKED
        buyer.save()
        messages.warning(request, f'{buyer.company_name} blocked.')
    return redirect('admin_manage_buyers')


@admin_required
def admin_marketplace_overview(request):
    """Admin sees full marketplace stats."""
    total_buyers   = Buyer.objects.filter(status=Buyer.Status.APPROVED).count()
    active_offers  = BuyerOffer.objects.filter(status=BuyerOffer.Status.ACTIVE).count()
    total_deals    = FarmerDeal.objects.count()
    completed_val  = FarmerDeal.objects.filter(status__in=['DELIVERED','PAID']).aggregate(s=Sum('total_amount'))['s'] or 0
    recent_deals   = FarmerDeal.objects.select_related(
        'farmer__user', 'offer__buyer', 'offer__crop'
    ).order_by('-created_at')[:20]
    buyers_by_type = Buyer.objects.filter(status=Buyer.Status.APPROVED).values('buyer_type').annotate(c=Count('id'))

    return render(request, 'marketplace/admin_marketplace_overview.html', {
        'total_buyers':   total_buyers,
        'active_offers':  active_offers,
        'total_deals':    total_deals,
        'completed_val':  completed_val,
        'recent_deals':   recent_deals,
        'buyers_by_type': buyers_by_type,
    })


# ─────────────────────────────────────────────
# AI DEAL ADVISOR (helper)
# ─────────────────────────────────────────────

def _get_ai_deal_advice(farmer, offer):
    """Generate AI recommendation comparing govt MSP vs private offer."""
    import os
    try:
        import anthropic
        from django.conf import settings
        api_key = getattr(settings, 'ANTHROPIC_API_KEY', '').strip() or os.environ.get('ANTHROPIC_API_KEY', '').strip()
        if not api_key or api_key in ('', 'PASTE_YOUR_KEY_HERE'):
            raise ValueError("No API key")
        client = anthropic.Anthropic(api_key=api_key)
    except Exception:
        # Smart fallback without AI
        msp     = offer.crop.msp_per_quintal
        private = offer.price_per_quintal
        diff    = private - msp
        pct     = (diff / msp * 100) if msp else 0
        buyer   = offer.buyer

        if diff > 0:
            return (
                f"✅ GOOD DEAL: {buyer.company_name} is offering ₹{private}/qtl — "
                f"that is ₹{diff:.0f} MORE than government MSP (₹{msp}/qtl). "
                f"That is {pct:.1f}% extra income for you!\n\n"
                f"⚠️ CHECK: Payment within {offer.payment_days} days. "
                f"Advance: {offer.advance_percent}%. "
                f"Make sure you are comfortable with the payment terms before accepting.\n\n"
                f"📌 GOVERNMENT MSP is always the safe backup option if you are unsure."
            )
        elif diff == 0:
            return (
                f"⚖️ EQUAL PRICE: This offer matches government MSP exactly (₹{msp}/qtl). "
                f"The government option is safer as payment is guaranteed. "
                f"Choose private only if pickup location is more convenient."
            )
        else:
            return (
                f"⚠️ CAUTION: This offer (₹{private}/qtl) is ₹{abs(diff):.0f} LESS than "
                f"government MSP (₹{msp}/qtl). "
                f"It is recommended to sell to the government instead unless you have a specific reason."
            )

    msp     = offer.crop.msp_per_quintal
    private = offer.price_per_quintal
    land    = sum(l.total_area_acres for l in farmer.land_details.all())

    prompt = f"""A farmer in Andhra Pradesh is deciding whether to sell their {offer.crop.name} to a private buyer or the government.

FARMER INFO:
- Name: {farmer.user.get_full_name() or farmer.user.username}
- District: {farmer.district}
- Land: {land} acres
- Crop: {offer.crop.name}

OPTION 1 — GOVERNMENT MSP:
- Price: ₹{msp}/quintal
- Payment: Directly to bank account within 7-10 days
- Guaranteed price, no risk
- Go to procurement centre on booked date

OPTION 2 — PRIVATE BUYER: {offer.buyer.company_name} ({offer.buyer.get_buyer_type_display()})
- Price offered: ₹{private}/quintal
- Difference from MSP: ₹{private - msp:+.0f}/quintal ({((private-msp)/msp*100):+.1f}%)
- Pickup: {offer.pickup_location}
- Payment within: {offer.payment_days} days
- Advance payment: {offer.advance_percent}%
- Buyer rating: {offer.buyer.rating}/5.0 ({offer.buyer.total_deals} completed deals)
- Valid until: {offer.valid_until}

Give the farmer a short, clear recommendation in 3 sections:
1. Is this a good deal? (compare prices, highlight if above/below MSP)
2. Things to check before accepting (payment terms, buyer reliability)
3. Final recommendation (which option to choose and why)

Keep it simple. Use ₹ amounts. Be honest. Write in English."""

    try:
        resp   = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text
    except Exception as e:
        return f"AI advice unavailable: {e}. Compare prices manually: MSP=₹{msp}, Offer=₹{private}."


# ─────────────────────────────────────────────
# API endpoint — live offer comparison
# ─────────────────────────────────────────────

@login_required
def api_crop_offers(request, crop_id):
    """JSON: all active offers for a crop + MSP for comparison widget."""
    crop  = get_object_or_404(Crop, pk=crop_id)
    today = date.today()
    offers = BuyerOffer.objects.filter(
        crop=crop, status=BuyerOffer.Status.ACTIVE,
        valid_from__lte=today, valid_until__gte=today,
    ).select_related('buyer').order_by('-price_per_quintal')

    return JsonResponse({
        'crop':     crop.name,
        'msp':      str(crop.msp_per_quintal),
        'offers': [{
            'id':              o.pk,
            'buyer':           o.buyer.company_name,
            'buyer_type':      o.buyer.get_buyer_type_display(),
            'price':           str(o.price_per_quintal),
            'premium_over_msp':str(o.premium_over_msp),
            'is_above_msp':    o.is_above_msp,
            'max_qty':         str(o.max_quantity_qtl),
            'payment_days':    o.payment_days,
            'advance_percent': o.advance_percent,
            'valid_until':     str(o.valid_until),
            'location':        o.pickup_location,
            'rating':          str(o.buyer.rating),
        } for o in offers],
    })
