"""
CropConnect — ML Prediction Views
Uses models trained on your actual CSV datasets.
"""
import os, json
import numpy as np
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from datetime import date

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, '..', 'ml_models')

_cache = {}

def _load(name):
    if name not in _cache:
        try:
            import joblib
            _cache[name] = joblib.load(os.path.join(MODELS_DIR, f'{name}.pkl'))
        except Exception:
            _cache[name] = None
    return _cache[name]


# ─────────────────────────────────────────────
# 1. CROP YIELD PREDICTOR
# ─────────────────────────────────────────────
@login_required
@require_POST
def predict_yield(request):
    try:
        data     = json.loads(request.body)
        crop     = data.get('crop', 'Paddy')
        district = data.get('district', 'Guntur')
        season   = data.get('season', 'Kharif')
        soil     = data.get('soil', 'Alluvial')
        land     = float(data.get('land_acres', 1))
        rainfall = float(data.get('rainfall_mm', 900))
        temp     = float(data.get('avg_temp', 28))

        model    = _load('yield_model')
        crop_enc = _load('crop_enc')
        dist_enc = _load('district_enc')
        seas_enc = _load('season_enc')
        soil_enc = _load('soil_enc')

        if not all([model, crop_enc, dist_enc, seas_enc, soil_enc]):
            # Rule-based fallback
            per_acre = 22 if crop == 'Paddy' else 10
            total    = round(land * per_acre, 2)
            return JsonResponse({
                'predicted_yield': total, 'per_acre': per_acre,
                'range_low': round(total*0.85,2), 'range_high': round(total*1.15,2),
                'recommended_booking': round(total*0.95,2),
                'tip': f'Standard estimate ({per_acre} qtl/acre). Train model for ML prediction.',
            })

        # Encode — use 0 for unknown values
        cv = crop_enc.get(crop, 0)
        dv = dist_enc.get(district, list(dist_enc.values())[0])
        sv = seas_enc.get(season, 0)
        ov = soil_enc.get(soil, 0)

        X    = np.array([[cv, dv, sv, ov, land, rainfall, temp]])
        pred = float(model.predict(X)[0])
        pred = round(max(0.5, pred), 2)

        per_acre = round(pred / land, 2) if land > 0 else 0
        low      = round(pred * 0.85, 2)
        high     = round(pred * 1.15, 2)

        std = land * (22 if crop == 'Paddy' else 10)
        if pred >= std * 1.1:
            tip = '🌟 Excellent yield expected! Your land conditions are great.'
        elif pred >= std * 0.85:
            tip = '✅ Good yield expected. Close to district average.'
        else:
            tip = '⚠️ Below average yield. Consider improving irrigation or soil health.'

        return JsonResponse({
            'predicted_yield': pred,
            'per_acre': per_acre,
            'range_low': low,
            'range_high': high,
            'recommended_booking': round(pred * 0.95, 2),
            'tip': tip,
            'crop': crop,
            'land_acres': land,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ─────────────────────────────────────────────
# 2. FRAUD DETECTOR
# ─────────────────────────────────────────────
@login_required
def ml_fraud_score(request, booking_id):
    if request.user.role not in ('OFFICER', 'ADMIN'):
        return JsonResponse({'error': 'Not authorized'}, status=403)

    try:
        from .models import SlotBooking
        from django.db.models import Avg

        booking   = SlotBooking.objects.select_related(
            'farmer__user', 'slot__crop').get(pk=booking_id)
        farmer    = booking.farmer
        land_list = farmer.land_details.all()
        total_land= float(sum(l.total_area_acres for l in land_list)) or 1
        estimated = float(booking.estimated_quintals)
        crop_name = booking.slot.crop.name

        past          = farmer.bookings.exclude(pk=booking_id)
        past_total    = past.count()
        past_approved = past.filter(status='APPROVED').count()
        past_rejected = past.filter(status='REJECTED').count()

        avg_qty = float(past.filter(status='APPROVED').aggregate(
            a=Avg('estimated_quintals'))['a'] or estimated)
        qty_vs_avg = estimated / avg_qty if avg_qty > 0 else 1.0

        last = past.order_by('-created_at').first()
        days_since = (date.today() - last.created_at.date()).days if last else 365

        qty_per_acre = estimated / total_land

        model = _load('fraud_model')

        if not model:
            # Rule-based fallback
            MAX_QTL_PER_ACRE = 25.0
            exceeds_govt_limit = qty_per_acre > MAX_QTL_PER_ACRE
            allowed_max_qtl = round(MAX_QTL_PER_ACRE * total_land, 2)
            std = 30 if 'paddy' in crop_name.lower() else 15
            flags = []
            if exceeds_govt_limit:
                flags.append(
                    f'🚫 Govt limit breached: {qty_per_acre:.1f} qtl/acre '
                    f'(limit 25 qtl/acre). Max allowed = {allowed_max_qtl} qtl for {total_land:.1f} acres.'
                )
            elif qty_per_acre > std * 1.2:
                flags.append(f'Qty {estimated:.0f} qtl high for {total_land:.1f} acres')
            if past_rejected >= 2:        flags.append(f'{past_rejected} past rejections')
            if qty_vs_avg > 2.0:          flags.append(f'Qty is {qty_vs_avg:.1f}× usual average')
            level = 'HIGH' if (exceeds_govt_limit or len(flags) >= 2) else 'MEDIUM' if flags else 'LOW'
            rec = (
                f'⛔ Govt limit exceeded: max {allowed_max_qtl} qtl for {total_land:.1f} acres. Do NOT approve.'
                if exceeds_govt_limit else 'Rule-based check (model not loaded)'
            )
            return JsonResponse({
                'risk_level': level, 'factors': flags,
                'recommendation': rec,
                'model_used': 'Rule-based fallback',
                'exceeds_govt_limit': exceeds_govt_limit,
                'max_allowed_qtl': allowed_max_qtl,
                'govt_limit_per_acre': MAX_QTL_PER_ACRE,
                'qty_per_acre': round(qty_per_acre, 2),
            })

        # Features match fraud_data.csv columns exactly
        X = np.array([[
            total_land,        # farmer_land_acres
            estimated,         # booked_quantity_qtl
            qty_per_acre,      # quantity_per_acre
            past_total,        # past_total_bookings
            past_approved,     # past_approved_bookings
            past_rejected,     # past_rejected_bookings
            qty_vs_avg,        # qty_vs_avg_ratio
            int(farmer.verified),  # farmer_verified
            days_since,        # days_since_last_booking
            1,                 # aadhaar_bank_linked (assume linked)
            0,                 # multiple_accounts_flag
        ]])

        fraud_prob  = float(model.predict_proba(X)[0][1])
        fraud_pct   = round(fraud_prob * 100, 1)
        risk_score  = round(fraud_prob * 10, 1)

        # ── GOVERNMENT RULE: Max 25 quintals per acre ──────────────────────
        MAX_QTL_PER_ACRE = 25.0
        exceeds_govt_limit = qty_per_acre > MAX_QTL_PER_ACRE
        excess_amount = round(qty_per_acre - MAX_QTL_PER_ACRE, 2) if exceeds_govt_limit else 0
        allowed_max_qtl = round(MAX_QTL_PER_ACRE * total_land, 2)

        if exceeds_govt_limit:
            # Hard override: always HIGH RISK when govt limit is breached
            risk_level = 'HIGH'; color = 'danger'; icon = '🚨'
            risk_score = max(risk_score, 8.5)  # floor the score at 8.5/10
            rec = (
                f'⛔ GOVERNMENT LIMIT EXCEEDED: Farmer booked {estimated:.0f} qtl '
                f'({qty_per_acre:.1f} qtl/acre) but the maximum allowed is 25 qtl/acre. '
                f'Maximum permissible quantity for {total_land:.1f} acres = {allowed_max_qtl} qtl. '
                f'Do NOT approve without verifying physical land records.'
            )
        elif fraud_pct < 25:
            risk_level = 'LOW';    color = 'success'; icon = '✅'
            rec = 'Booking looks genuine. Safe to approve.'
        elif fraud_pct < 60:
            risk_level = 'MEDIUM'; color = 'warning'; icon = '⚠️'
            rec = 'Some unusual patterns. Verify documents before approving.'
        else:
            risk_level = 'HIGH';   color = 'danger';  icon = '🚨'
            rec = 'High fraud probability. Request physical verification of land.'

        # Explain factors
        factors = []
        # Government limit check — always first if breached
        if exceeds_govt_limit:
            factors.append(
                f'🚫 Govt limit breached: {qty_per_acre:.1f} qtl/acre booked '
                f'(limit is 25 qtl/acre — excess of {excess_amount} qtl/acre). '
                f'Allowed max for {total_land:.1f} acres = {allowed_max_qtl} qtl, '
                f'but farmer booked {estimated:.0f} qtl.'
            )
        std = 30 if 'paddy' in crop_name.lower() else 15
        if qty_per_acre > std * 1.2 and not exceeds_govt_limit:
            factors.append(f'Quantity {estimated:.0f} qtl high for {total_land:.1f} acres (max ~{std*total_land:.0f} qtl)')
        if past_rejected >= 2:          factors.append(f'Farmer has {past_rejected} previous rejections')
        if qty_vs_avg > 2.0:            factors.append(f'Quantity is {qty_vs_avg:.1f}× their usual average')
        if days_since < 3 and past_total > 0: factors.append(f'Booking made only {days_since} day(s) after previous booking')
        if not farmer.verified:         factors.append('Farmer land is not yet verified')

        return JsonResponse({
            'risk_level': risk_level, 'risk_score': risk_score,
            'fraud_percent': fraud_pct, 'color': color, 'icon': icon,
            'recommendation': rec, 'factors': factors,
            'model_used': 'GradientBoosting — trained on procurement_booking_fraud.csv',
            'farmer': farmer.user.get_full_name() or farmer.user.username,
            'land_acres': total_land, 'qty_per_acre': round(qty_per_acre, 2),
            'max_allowed_qtl': allowed_max_qtl,
            'exceeds_govt_limit': exceeds_govt_limit,
            'govt_limit_per_acre': MAX_QTL_PER_ACRE,
        })

    except SlotBooking.DoesNotExist:
        return JsonResponse({'error': 'Booking not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ─────────────────────────────────────────────
# 3. QUALITY GRADE PREDICTOR
# ─────────────────────────────────────────────
@login_required
@require_POST
def predict_quality(request):
    try:
        data        = json.loads(request.body)
        crop        = data.get('crop', 'Paddy')
        crop_val    = 0 if crop == 'Paddy' else 1
        moisture    = float(data.get('moisture', 14))
        foreign     = float(data.get('foreign', 0.5))
        damaged     = float(data.get('damaged', 1))
        immature    = float(data.get('immature', 1))
        chalky      = float(data.get('chalky', 2))
        shelling    = float(data.get('shelling', 72))
        oil_content = float(data.get('oil_content', 47))
        aflatoxin   = int(data.get('aflatoxin', 0))

        model      = _load('quality_model')
        grade_lbls = _load('grade_labels')
        GRADES     = grade_lbls if grade_lbls else {0: 'FAQ', 1: 'Below_FAQ', 2: 'Rejected'}

        if not model:
            # Rule-based fallback
            failures = []
            if crop == 'Paddy':
                if moisture > 17: failures.append(f'Moisture {moisture}% > 17%')
                if foreign  > 1:  failures.append(f'Foreign {foreign}% > 1%')
                if damaged  > 3:  failures.append(f'Damaged {damaged}% > 3%')
                if immature > 3:  failures.append(f'Immature {immature}% > 3%')
                if chalky   > 5:  failures.append(f'Chalky {chalky}% > 5%')
            else:
                if moisture    > 8:  failures.append(f'Moisture {moisture}% > 8%')
                if foreign     > 1:  failures.append(f'Foreign {foreign}% > 1%')
                if shelling    < 70: failures.append(f'Shelling {shelling}% < 70%')
                if oil_content < 45: failures.append(f'Oil {oil_content}% < 45%')
                if aflatoxin   == 1: failures.append('Aflatoxin detected')
            grade = 'Rejected' if aflatoxin==1 or len(failures)>2 else 'Below_FAQ' if failures else 'FAQ'
            colors = {'FAQ': 'success', 'Below_FAQ': 'warning', 'Rejected': 'danger'}
            msgs   = {'FAQ': 'Excellent quality. Full MSP will be paid.',
                      'Below_FAQ': 'Below standard. 5% deduction applies.',
                      'Rejected': 'Does not meet minimum standards.'}
            return JsonResponse({'grade': grade, 'failures': failures,
                                  'color': colors[grade], 'message': msgs[grade],
                                  'passes': grade == 'FAQ', 'confidence': 0,
                                  'note': 'Rule-based fallback'})

        # Feature order matches quality_data.csv training
        X    = np.array([[crop_val, moisture, foreign, damaged, immature,
                           chalky, shelling, oil_content, aflatoxin]])
        pred = int(model.predict(X)[0])
        prob = model.predict_proba(X)[0]
        grade      = GRADES.get(pred, 'Unknown')
        confidence = round(float(prob[pred]) * 100, 1)

        grade_info = {
            'FAQ':       {'color': 'success', 'icon': '✅', 'msg': 'Excellent quality. Full MSP will be paid.'},
            'Below_FAQ': {'color': 'warning', 'icon': '⚠️', 'msg': 'Below standard. 5% price deduction will apply.'},
            'Rejected':  {'color': 'danger',  'icon': '❌', 'msg': 'Does not meet minimum standards. Cannot be procured.'},
        }
        info = grade_info.get(grade, grade_info['Rejected'])

        # Which parameters failed
        failures = []
        if crop == 'Paddy':
            if moisture > 17: failures.append(f'Moisture {moisture}% exceeds 17% limit')
            if foreign  > 1:  failures.append(f'Foreign matter {foreign}% exceeds 1% limit')
            if damaged  > 3:  failures.append(f'Damaged grains {damaged}% exceeds 3% limit')
            if immature > 3:  failures.append(f'Immature grains {immature}% exceeds 3% limit')
            if chalky   > 5:  failures.append(f'Chalky grains {chalky}% exceeds 5% limit')
        else:
            if moisture    > 8:  failures.append(f'Moisture {moisture}% exceeds 8% limit')
            if foreign     > 1:  failures.append(f'Foreign matter {foreign}% exceeds 1% limit')
            if shelling    < 70: failures.append(f'Shelling outturn {shelling}% below 70% minimum')
            if oil_content < 45: failures.append(f'Oil content {oil_content}% below 45% minimum')
            if aflatoxin   == 1: failures.append('Aflatoxin contamination detected')

        return JsonResponse({
            'grade': grade, 'confidence': confidence,
            'color': info['color'], 'icon': info['icon'], 'message': info['msg'],
            'failures': failures, 'passes': len(failures) == 0,
            'proba_faq':      round(float(prob[0]) * 100, 1),
            'proba_below':    round(float(prob[1]) * 100, 1),
            'proba_rejected': round(float(prob[2]) * 100, 1),
            'model_used': 'DecisionTree — trained on crop_quality_inspection.csv',
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ─────────────────────────────────────────────
# 4. ML ADMIN DASHBOARD
# ─────────────────────────────────────────────
@login_required
def ml_dashboard(request):
    if request.user.role != 'ADMIN':
        from django.shortcuts import redirect
        return redirect('admin_dashboard')

    from .models import SlotBooking, Procurement, Farmer
    from django.db.models import Avg

    total_farmers    = Farmer.objects.count()
    total_bookings   = SlotBooking.objects.count()
    rejected_bookings= SlotBooking.objects.filter(status='REJECTED').count()
    rejection_rate   = round(rejected_bookings / total_bookings * 100, 1) if total_bookings else 0
    approved         = SlotBooking.objects.filter(status='APPROVED').count()
    approval_rate    = round(approved / total_bookings * 100, 1) if total_bookings else 0
    quality_approved = Procurement.objects.filter(status='APPROVED').count()
    quality_rejected = Procurement.objects.filter(status='REJECTED').count()
    avg_moisture     = Procurement.objects.filter(
        moisture_percent__isnull=False).aggregate(a=Avg('moisture_percent'))['a']

    models_status = []
    for m, label, dataset in [
        ('yield_model',   'Crop Yield Predictor',    'crop_yield_andhra_pradesh.csv'),
        ('fraud_model',   'Fraud Detector',           'procurement_booking_fraud.csv'),
        ('quality_model', 'Quality Grade Predictor', 'crop_quality_inspection.csv'),
    ]:
        path   = os.path.join(MODELS_DIR, f'{m}.pkl')
        loaded = os.path.exists(path)
        size   = round(os.path.getsize(path)/1024, 1) if loaded else 0
        models_status.append({
            'name': label, 'file': f'{m}.pkl',
            'loaded': loaded, 'size_kb': size, 'dataset': dataset
        })

    return render(request, 'ml/dashboard.html', {
        'total_farmers': total_farmers, 'total_bookings': total_bookings,
        'rejection_rate': rejection_rate, 'approval_rate': approval_rate,
        'quality_approved': quality_approved, 'quality_rejected': quality_rejected,
        'avg_moisture': round(avg_moisture, 2) if avg_moisture else 'N/A',
        'models_status': models_status,
    })
