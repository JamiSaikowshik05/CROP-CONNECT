"""
AI-powered views for CropConnect
Features:
  1. Farm Assistant Chatbot (Tamil/English support)
  2. Smart Fraud Detection for officers
  3. MSP Price Advisory for farmers
  4. Rejection reason explainer
"""
import json
import os
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .models import Farmer, Crop, SlotBooking, Procurement, LandDetails


def get_anthropic_client():
    from django.conf import settings
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '').strip() or os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key or api_key in ('PASTE_YOUR_KEY_HERE', 'sk-ant-your-key-here') or not ANTHROPIC_AVAILABLE:
        return None
    return anthropic.Anthropic(api_key=api_key)


# ─────────────────────────────────────────────
# 1. FARM ASSISTANT CHATBOT
# ─────────────────────────────────────────────

@login_required
@require_POST
def farm_chatbot(request):
    """
    AI chatbot that answers farmer/officer questions about the portal.
    Supports questions in English and Tamil.
    POST body: { "message": "...", "history": [...] }
    """
    try:
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()
        history = data.get("history", [])  # list of {role, content}

        if not user_message:
            return JsonResponse({"error": "No message provided"}, status=400)

        client = get_anthropic_client()
        if not client:
            # Answer common questions without AI using keyword matching
            msg_lower = user_message.lower()
            if any(w in msg_lower for w in ['msp', 'minimum support', 'price', 'payment', 'paid', 'money', 'amount']):
                reply = (
                    "📌 MSP (Minimum Support Price) is the guaranteed price the Government of India pays farmers.\n\n"
                    "✅ HOW YOUR PAYMENT IS CALCULATED:\n"
                    "   Payment = Your Crop Weight (quintals) × MSP Rate\n\n"
                    "   Example: 10 quintals of Paddy × ₹2183/quintal = ₹21,830\n\n"
                    "✅ HOW PAYMENT IS SENT:\n"
                    "   • After your crop is weighed at the centre\n"
                    "   • A bill is generated automatically\n"
                    "   • Admin approves the payment\n"
                    "   • Money is sent DIRECTLY to your bank account\n"
                    "   • NO middleman takes any cut!\n\n"
                    "📞 For more help: Call 6304629308"
                )
            elif any(w in msg_lower for w in ['reject', 'rejected', 'why reject', 'booking reject', 'denied']):
                reply = (
                    "❌ BOOKING REJECTED — COMMON REASONS & FIXES:\n\n"
                    "1️⃣ QUANTITY TOO HIGH\n"
                    "   Your booked quantity is more than your land can produce.\n"
                    "   Fix: Paddy = acres × 25 quintals | Groundnut = acres × 12 quintals\n"
                    "   Example: 2 acres Paddy → max 50 quintals\n\n"
                    "2️⃣ DOCUMENTS MISMATCH\n"
                    "   Aadhaar name or survey number doesn't match records.\n"
                    "   Fix: Check your Aadhaar spelling & Adangal/Patta survey number\n\n"
                    "3️⃣ LAND NOT VERIFIED YET\n"
                    "   Officer hasn't verified your land yet.\n"
                    "   Fix: Wait 1-3 days, then book again\n\n"
                    "4️⃣ DUPLICATE BOOKING\n"
                    "   Already booked same crop on same date.\n"
                    "   Fix: Choose a different date\n\n"
                    "5️⃣ SLOT IS FULL\n"
                    "   That date has reached 500 quintal limit.\n"
                    "   Fix: Choose another date\n\n"
                    "👉 Go to Dashboard → click 'Why rejected?' for your specific reason\n"
                    "📞 Help: 6304629308"
                )
            elif any(w in msg_lower for w in ['book', 'slot', 'register']):
                reply = (
                    "📌 HOW TO BOOK A SLOT:\n"
                    "1. Register as a Farmer (need: Aadhaar, bank details, land survey no.)\n"
                    "2. Wait for Officer to verify your land (1-2 days)\n"
                    "3. Once verified, click 'Book New Slot' on your dashboard\n"
                    "4. Select: Crop (Paddy/Groundnut) + Date + Quantity\n"
                    "5. Officer approves your booking\n"
                    "6. Bring your crop on the booked date!\n\n"
                    "📞 Need help? Call: 6304629308"
                )
            elif any(w in msg_lower for w in ['document', 'need', 'require']):
                reply = (
                    "📋 DOCUMENTS NEEDED FOR REGISTRATION:\n"
                    "• Aadhaar Card (12-digit number)\n"
                    "• Bank Passbook (account no. + IFSC code)\n"
                    "• Land Survey Number (from your land records)\n\n"
                    "That's all! No middleman, no extra fees.\n\n"
                    "📞 Help: 6304629308"
                )
            else:
                reply = (
                    "ℹ️ AI assistant needs an API key to be fully active.\n\n"
                    "Common answers:\n"
                    "• MSP = Government guaranteed price per quintal\n"
                    "• Payment goes directly to your bank — no middleman\n"
                    "• To book: Register → Get verified → Book slot\n\n"
                    "📞 Helpdesk: 6304629308\n"
                    "📧 Email: governmentofindia@gmail.com\n"
                    "🕐 9 AM – 6 PM (Mon–Sat)\n\n"
                    "To enable full AI: Add your free API key in settings.py"
                )
            return JsonResponse({"reply": reply})

        # Build context about the logged-in user
        user = request.user
        user_context = f"User role: {user.role}, Username: {user.username}"

        if user.role == "FARMER":
            try:
                farmer = user.farmer_profile
                crops = Crop.objects.filter(is_active=True)
                crop_info = ", ".join([f"{c.name} at ₹{c.msp_per_quintal}/quintal" for c in crops])
                pending = farmer.bookings.filter(status=SlotBooking.Status.PENDING).count()
                approved = farmer.bookings.filter(status=SlotBooking.Status.APPROVED).count()

                # Include rejected bookings with actual reasons
                rejected_bookings = farmer.bookings.filter(
                    status=SlotBooking.Status.REJECTED
                ).select_related("slot__crop").order_by("-created_at")[:5]

                rejected_info = ""
                if rejected_bookings.exists():
                    rejected_info = "\nREJECTED BOOKINGS (most recent first):\n"
                    for b in rejected_bookings:
                        reason = b.rejection_reason.strip() if b.rejection_reason else "No reason given by officer"
                        rejected_info += (
                            f"  - {b.slot.crop.name} on {b.slot.date}, "
                            f"{b.estimated_quintals} quintals — Reason: {reason}\n"
                        )

                land_details = farmer.land_details.all()
                total_land = sum(l.total_area_acres for l in land_details)

                user_context += (
                    f"\nFarmer: {farmer.user.get_full_name()}, Village: {farmer.village}, "
                    f"District: {farmer.district}, Verified: {farmer.verified}\n"
                    f"Land: {total_land} acres\n"
                    f"Pending bookings: {pending}, Approved: {approved}\n"
                    f"Current MSP rates: {crop_info}"
                    f"{rejected_info}"
                )
            except Exception:
                pass
        elif user.role == "OFFICER":
            pending_land = LandDetails.objects.filter(verified=False).count()
            pending_bookings = SlotBooking.objects.filter(status=SlotBooking.Status.PENDING).count()
            user_context += (
                f"\nOfficer pending tasks — Land verifications: {pending_land}, "
                f"Booking approvals: {pending_bookings}"
            )

        system_prompt = f"""You are a friendly AI assistant named "Krishi Mitra for CropConnect of the Government of India. You help farmers in Andhra Pradesh sell their crops directly to the government at MSP price — NO middleman.

CURRENT USER INFO:
{user_context}

═══════════════════════════════════════════
HOW THE PORTAL WORKS (know this fully):
═══════════════════════════════════════════
STEP 1 — REGISTRATION
  • Farmer registers with: Full name, Aadhaar (12 digits), Bank account + IFSC, Land survey number, Village/Mandal/District
  • After registration, account is PENDING until officer verifies land

STEP 2 — LAND VERIFICATION
  • A procurement officer visits or checks land records
  • Once verified, farmer status becomes VERIFIED
  • Only verified farmers can book slots

STEP 3 — BOOKING A SLOT
  • Farmer selects: Crop (Paddy or Groundnut) + Date + Estimated quantity in quintals
  • Slot has limited capacity (500 quintals per slot)
  • Officer approves or rejects the booking

STEP 4 — PROCUREMENT DAY
  • Farmer brings crop to the procurement centre on booked date
  • Officer weighs the actual crop
  • A BILL is auto-generated: Actual Weight × MSP Rate = Total Amount

STEP 5 — PAYMENT
  • Admin approves the bill/payment
  • Money is transferred DIRECTLY to farmer's bank account
  • NO middleman, NO commission, NO deduction

═══════════════════════════════════════════
MSP RATES (Minimum Support Price):
═══════════════════════════════════════════
• Paddy (వరి/धान): ₹2183 per quintal (1 quintal = 100 kg)
• Groundnut (వేరుశెనగ/मूंगफली): ₹6377 per quintal
• These are GUARANTEED prices — government always pays this, market price doesn't matter

PAYMENT CALCULATION EXAMPLES:
• 10 quintals Paddy = 10 × ₹2183 = ₹21,830
• 5 quintals Groundnut = 5 × ₹6377 = ₹31,885
• 20 quintals Paddy = 20 × ₹2183 = ₹43,660

═══════════════════════════════════════════
DOCUMENTS NEEDED:
═══════════════════════════════════════════
1. Aadhaar Card — 12 digit number
2. Bank Passbook — Account number + IFSC code (e.g. SBIN0001234)
3. Land Records — Survey number, total acres
4. No other documents needed!

═══════════════════════════════════════════
COMMON FARMER QUESTIONS & ANSWERS:
═══════════════════════════════════════════
Q: How long does verification take?
A: Usually 1-3 working days after registration.

Q: My booking was rejected — what to do?
A: Check the rejection reason on your dashboard. Click "Why rejected?" button next to the rejected booking — it will explain in simple words what went wrong and exactly how to fix it. Common reasons below:

REJECTION REASON 1 — Quantity too high:
  • You booked more quintals than your land can produce
  • Fix: Paddy = your acres × 25 quintals. Groundnut = your acres × 12 quintals
  • Example: 2 acres of Paddy → maximum 50 quintals
  • Book again with correct quantity

REJECTION REASON 2 — Documents mismatch:
  • Your Aadhaar name or land survey number doesn't match government records
  • Fix: Check your Aadhaar card spelling vs registration name
  • Check survey number from your Adangal/Patta document
  • Call helpdesk: 6304629308 to correct records

REJECTION REASON 3 — Land not verified:
  • Officer has not yet verified your land details
  • Fix: Wait 1-3 working days for officer to verify
  • Then book again — verification is one time only

REJECTION REASON 4 — Duplicate booking:
  • You already have a booking for same crop and same date
  • Fix: Check existing bookings on dashboard
  • Choose a different date and book again

REJECTION REASON 5 — Slot full:
  • That date's slot already reached 500 quintal limit
  • Fix: Choose a different date — book early in morning

REJECTION REASON 6 — Bank details wrong:
  • Your account number or IFSC code has an error
  • Fix: Check your bank passbook carefully
  • IFSC is 11 characters e.g. SBIN0001234
  • Call helpdesk to update: 6304629308

REJECTION REASON 7 — No reason given by officer:
  • Call helpdesk immediately: 6304629308
  • Give them your booking ID and ask for explanation

Q: How do I know why my booking was rejected?
A: Go to your Farmer Dashboard → look at your bookings list → click the "Why rejected?" button next to any REJECTED booking. The AI will explain exactly why and give you step-by-step fix instructions.

Q: Can I book again after rejection?
A: YES! You can book a new slot immediately after fixing the problem. Rejection does not ban you. Just fix the issue and book again.

═══════════════════════════════════════════
WHY BOOKINGS GET REJECTED — ALL REASONS:
═══════════════════════════════════════════

REASON 1: "Quantity too high for land size"
  • What it means: You entered more quintals than your land can produce
  • Paddy gives 20-30 quintals per acre. Groundnut gives 8-15 quintals per acre
  • Example: If you have 2 acres of paddy, max is 2 × 30 = 60 quintals
  • Fix: Calculate correctly and book again with right quantity

REASON 2: "Land not verified"
  • What it means: Officer has not verified your land details yet
  • Fix: Wait for officer to verify, then book slot. Usually takes 1-3 days.

REASON 3: "Documents mismatch"
  • What it means: Your Aadhaar name or survey number does not match government records
  • Fix: Check your Aadhaar card and land documents carefully. Contact helpdesk: 6304629308

REASON 4: "Slot capacity full"
  • What it means: That day's slot already has 500 quintals booked by other farmers
  • Fix: Choose a different date and book again

REASON 5: "Duplicate booking"
  • What it means: You already booked the same crop on the same date
  • Fix: Check your existing bookings. You cannot book same crop + same date twice

REASON 6: "Invalid survey number"
  • What it means: The survey number you entered does not exist in records
  • Fix: Check your land documents (Adangal/ROR/Patta) for the correct survey number

REASON 7: "Bank details incorrect"
  • What it means: Your bank account or IFSC code has an error
  • Fix: Check your bank passbook carefully and update via helpdesk: 6304629308

REASON 8: "Crop not in season"
  • What it means: The crop you booked is not currently in procurement season
  • Fix: Check the portal announcements for procurement schedule

REASON 9: "No reason given by officer"
  • What it means: Officer rejected without writing reason
  • Fix: Call helpdesk 6304629308 and ask them to check why

AFTER REJECTION — STEPS TO FOLLOW:
  1. Go to Dashboard → see rejection reason
  2. Fix the problem (correct quantity / update documents)
  3. Book a NEW slot (you can book again immediately)
  4. If confused — call helpdesk: 6304629308

Q: When will I get paid?
A: After procurement day → bill generated → admin approves (1-3 days) → bank transfer (2-5 days). Total: around 1 week.

Q: Can I book multiple slots?
A: One slot per crop per date. You can book different crops or different dates.

Q: What is a quintal?
A: 1 quintal = 100 kilograms. So 10 quintals = 1000 kg = 1 tonne.

Q: What if I bring less crop than I booked?
A: No problem! Payment is based on ACTUAL weight measured on the day, not your estimated booking.

Q: Is there any fee or commission?
A: NO. This portal is completely FREE. Government pays full MSP directly to your bank.

Q: My bank account is wrong — what to do?
A: Contact the helpdesk immediately: 6304629308. They will help correct it before payment.

Q: How do I download my payment invoice?
A: Go to Dashboard → Payment Status → Download Invoice button next to your completed procurement.

Q: What crops can I sell?
A: Currently Paddy (వరి) and Groundnut (వేరుశెనగ). More crops may be added by government.

Q: I forgot my password — what to do?
A: Contact helpdesk: 6304629308 or email: governmentofindia@gmail.com

Q: What is IFSC code?
A: It is an 11-character code on your bank passbook. Example: SBIN0001234. It identifies your bank branch.

Q: What is survey number?
A: It is the number given to your land in government records (పట్టా). You can find it on your land documents (Adangal/ROR).

═══════════════════════════════════════════
HELPDESK CONTACT:
═══════════════════════════════════════════
📞 Phone: 6304629308
📧 Email: governmentofindia@gmail.com
🕐 Hours: 9:00 AM – 6:00 PM (Monday to Saturday)

═══════════════════════════════════════════
YOUR BEHAVIOUR RULES:
═══════════════════════════════════════════
1. Always answer in simple, clear language — farmers may not be educated
2. Use numbers and examples to explain payments
3. Be warm, encouraging and patient
4. If asked in Telugu, reply in Telugu
5. If asked in Tamil, reply in Tamil
6. If asked in Hindi, reply in Hindi
7. Otherwise reply in English
8. Always end with an encouraging message or next step
9. Never say "I don't know" — always give the helpdesk number if unsure
10. Keep replies SHORT and easy to read — use bullet points"""

        # Build message list for API
        messages = []
        for h in history[-6:]:  # last 6 turns for context
            if h.get("role") in ("user", "assistant") and h.get("content"):
                messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": user_message})

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=system_prompt,
            messages=messages,
        )
        reply = response.content[0].text
        return JsonResponse({"reply": reply})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ─────────────────────────────────────────────
# 2. SMART FRAUD / RISK DETECTION
# ─────────────────────────────────────────────

@login_required
def analyze_booking_risk(request, booking_id):
    """
    AI risk analysis of a slot booking for officers.
    Returns a risk score + explanation.
    GET /ai/risk/<booking_id>/
    """
    if request.user.role not in ("OFFICER", "ADMIN"):
        return JsonResponse({"error": "Not authorized"}, status=403)

    try:
        booking = SlotBooking.objects.select_related(
            "farmer__user", "slot__crop"
        ).get(pk=booking_id)
    except SlotBooking.DoesNotExist:
        return JsonResponse({"error": "Booking not found"}, status=404)

    farmer = booking.farmer
    land_details = farmer.land_details.all()
    total_land = sum(l.total_area_acres for l in land_details)
    past_bookings = farmer.bookings.exclude(pk=booking_id)
    past_approved = past_bookings.filter(status="APPROVED").count()
    past_rejected = past_bookings.filter(status="REJECTED").count()
    avg_past_qty = 0
    if past_approved > 0:
        from django.db.models import Avg
        avg = past_bookings.filter(status="APPROVED").aggregate(Avg("estimated_quintals"))
        avg_past_qty = float(avg["estimated_quintals__avg"] or 0)

    # Rule-based quick checks (no AI needed for obvious flags)
    flags = []
    # Paddy: roughly 20–30 quintals per acre; Groundnut: 8–15 quintals per acre
    crop_name = booking.slot.crop.name.lower()
    max_per_acre = 30 if "paddy" in crop_name else 15
    max_expected = float(total_land) * max_per_acre
    estimated = float(booking.estimated_quintals)

    if total_land > 0 and estimated > max_expected * 1.2:
        flags.append(f"Quantity {estimated} qtl exceeds expected max {max_expected:.1f} qtl for {total_land} acres")
    if past_rejected > 2:
        flags.append(f"Farmer has {past_rejected} previous rejections")
    if avg_past_qty > 0 and estimated > avg_past_qty * 2:
        flags.append(f"Quantity is 2× higher than farmer's average ({avg_past_qty:.1f} qtl)")

    client = get_anthropic_client()
    if not client:
        risk = "HIGH" if len(flags) >= 2 else "MEDIUM" if flags else "LOW"
        return JsonResponse({
            "risk_level": risk,
            "risk_score": 7 if risk == "HIGH" else 5 if risk == "MEDIUM" else 2,
            "flags": flags,
            "key_concerns": flags,
            "explanation": "Rule-based check (no API key). Add ANTHROPIC_API_KEY in settings.py for full AI analysis.",
            "recommendation": "Verify documents manually." if flags else "Looks normal based on land size.",
        })

    prompt = f"""You are a procurement fraud detection assistant for a government agricultural portal in India.

Analyze this slot booking and give a risk assessment:

BOOKING DETAILS:
- Farmer: {farmer.user.get_full_name() or farmer.user.username}
- District: {farmer.district}, Mandal: {farmer.mandal}
- Total land: {total_land} acres
- Crop: {booking.slot.crop.name}
- Estimated quantity: {booking.estimated_quintals} quintals
- Booking date: {booking.slot.date}
- Farmer verified: {farmer.verified}

FARMER HISTORY:
- Past approved bookings: {past_approved}
- Past rejected bookings: {past_rejected}
- Average quantity in past approved bookings: {avg_past_qty:.1f} quintals

RULE-BASED FLAGS ALREADY DETECTED:
{chr(10).join(flags) if flags else "None"}

CONTEXT:
- Paddy yields roughly 20-30 quintals per acre
- Groundnut yields roughly 8-15 quintals per acre

Respond ONLY with a valid JSON object, no markdown, no backticks, no explanation outside the JSON:
{{"risk_level":"LOW","risk_score":2,"key_concerns":["concern1"],"recommendation":"one sentence","explanation":"2-3 sentences"}}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        # Strip any markdown code fences
        for fence in ['```json', '```JSON', '```']:
            raw = raw.replace(fence, '')
        raw = raw.strip()
        # Find JSON object boundaries
        start = raw.find('{')
        end = raw.rfind('}') + 1
        if start >= 0 and end > start:
            raw = raw[start:end]
        result = json.loads(raw)
        result["flags"] = flags
        return JsonResponse(result)
    except Exception as e:
        risk = "HIGH" if len(flags) >= 2 else "MEDIUM" if flags else "LOW"
        return JsonResponse({
            "risk_level": risk,
            "risk_score": 7 if risk == "HIGH" else 5 if risk == "MEDIUM" else 2,
            "flags": flags,
            "key_concerns": flags if flags else ["No major concerns detected"],
            "explanation": f"AI analysis completed with rule-based fallback. {' | '.join(flags) if flags else 'No flags raised.'}",
            "recommendation": "Review documents carefully." if flags else "Booking appears normal.",
        })


# ─────────────────────────────────────────────
# 3. MSP PRICE ADVISORY
# ─────────────────────────────────────────────

@login_required
def price_advisory(request):
    """
    AI price advisory for farmers — explains MSP and gives selling advice.
    GET /ai/price-advisory/
    """
    crops = Crop.objects.filter(is_active=True)
    crop_info = "\n".join([
        f"- {c.name}: ₹{c.msp_per_quintal}/quintal (Season: {c.season or 'All seasons'})"
        for c in crops
    ])

    farmer_context = ""
    if request.user.role == "FARMER":
        try:
            farmer = request.user.farmer_profile
            bookings = farmer.bookings.select_related("slot__crop").order_by("-created_at")[:5]
            booking_summary = ", ".join([
                f"{b.slot.crop.name} {b.estimated_quintals}qtl ({b.get_status_display()})"
                for b in bookings
            ])
            farmer_context = (
                f"Farmer district: {farmer.district}\n"
                f"Recent bookings: {booking_summary or 'None'}"
            )
        except Exception:
            pass

    client = get_anthropic_client()
    if not client:
        advice = (
            "MSP (Minimum Support Price) is the guaranteed price the government pays you "
            "for your produce. You do NOT need a middleman — register on this portal and "
            "sell directly to the government procurement center.\n\n"
            "Contact helpdesk for more info: 6304629308"
        )
        return JsonResponse({"advice": advice, "crops": [
            {"name": c.name, "msp": str(c.msp_per_quintal), "season": c.season}
            for c in crops
        ]})

    prompt = f"""You are an agricultural advisor for farmers in Andhra Pradesh, India.

Current MSP rates on this government portal:
{crop_info}

{farmer_context}

Give practical, actionable advice to this farmer about:
1. What MSP means and why it protects them from middlemen
2. The best time to sell each crop based on current season (March = end of Rabi, approaching Kharif)
3. How to maximise their earnings through this portal

Keep the advice to 4-5 short paragraphs. Be warm and encouraging.
Start with a greeting. Write in simple English (the portal will also translate to Telugu/Tamil)."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        advice = response.content[0].text
    except Exception as e:
        advice = f"Could not load AI advice ({e}). Please call helpdesk: 6304629308"

    return JsonResponse({
        "advice": advice,
        "crops": [
            {"name": c.name, "msp": str(c.msp_per_quintal), "season": c.season or "All seasons"}
            for c in crops
        ],
    })


# ─────────────────────────────────────────────
# 4. REJECTION EXPLAINER
# ─────────────────────────────────────────────

@login_required
def explain_rejection(request, booking_id):
    """
    AI explains in simple language why a booking was rejected.
    GET /ai/explain-rejection/<booking_id>/
    """
    try:
        booking = SlotBooking.objects.select_related(
            "farmer__user", "slot__crop", "slot"
        ).get(pk=booking_id, farmer=request.user.farmer_profile)
    except (SlotBooking.DoesNotExist, AttributeError):
        return JsonResponse({"error": "Booking not found"}, status=404)

    if booking.status != "REJECTED":
        return JsonResponse({"explanation": "This booking has not been rejected."})

    farmer = booking.farmer
    reason = booking.rejection_reason or ""
    crop_name = booking.slot.crop.name
    slot_date = booking.slot.date
    estimated_qty = booking.estimated_quintals

    # Get farmer's land details for context
    land_details = farmer.land_details.all()
    total_land = sum(l.total_area_acres for l in land_details)
    max_expected = float(total_land) * (30 if "paddy" in crop_name.lower() else 15)

    # Smart reason detection — figure out the likely reason even if officer didn't write it
    reason_lower = reason.lower()
    detected_reason = "unknown"

    if any(w in reason_lower for w in ["quantity", "weight", "quintal", "high", "exceed", "land", "acre"]):
        detected_reason = "quantity_too_high"
    elif any(w in reason_lower for w in ["document", "mismatch", "aadhaar", "survey", "record"]):
        detected_reason = "document_mismatch"
    elif any(w in reason_lower for w in ["verify", "verification", "not verified"]):
        detected_reason = "not_verified"
    elif any(w in reason_lower for w in ["duplicate", "already", "booked"]):
        detected_reason = "duplicate"
    elif any(w in reason_lower for w in ["capacity", "full", "slot"]):
        detected_reason = "slot_full"
    elif any(w in reason_lower for w in ["bank", "account", "ifsc"]):
        detected_reason = "bank_error"
    elif any(w in reason_lower for w in ["season", "schedule"]):
        detected_reason = "not_in_season"
    elif not reason.strip():
        detected_reason = "no_reason_given"
    else:
        detected_reason = "other"

    # Build fix steps based on detected reason
    fix_steps = {
        "quantity_too_high": [
            f"Your land is {total_land} acres. For {crop_name}, maximum expected quantity is {max_expected:.0f} quintals.",
            "Book again with a quantity equal to or less than your expected yield.",
            "Formula: Paddy = land acres × 25 quintals. Groundnut = land acres × 12 quintals.",
        ],
        "document_mismatch": [
            "Check your Aadhaar card — name must match exactly with your registration.",
            "Check your land survey number from your Adangal or Patta document.",
            "If documents are correct, call helpdesk: 6304629308 to update your records.",
        ],
        "not_verified": [
            "Your land is not yet verified by the officer.",
            "Wait 1-3 working days for officer verification.",
            "Once verified, you can book again immediately.",
        ],
        "duplicate": [
            "You already have a booking for this crop on this date.",
            "Check your existing bookings on the dashboard.",
            "Choose a different date to book a new slot.",
        ],
        "slot_full": [
            "The slot for this date is already full (500 quintal limit).",
            "Choose a different date and book a new slot.",
            "Try booking early in the morning for better availability.",
        ],
        "bank_error": [
            "Check your bank account number carefully from your passbook.",
            "Check your IFSC code — it is 11 characters (e.g. SBIN0001234).",
            "Call helpdesk to update bank details: 6304629308.",
        ],
        "not_in_season": [
            "This crop is not currently in the procurement schedule.",
            "Check the portal announcements for the procurement dates.",
            "Call helpdesk for the current schedule: 6304629308.",
        ],
        "no_reason_given": [
            "Officer did not write a reason for rejection.",
            "Call helpdesk immediately: 6304629308 and give them your booking ID.",
            "Ask them to explain the reason and help you rebook.",
        ],
        "other": [
            "Read the officer's reason carefully on your dashboard.",
            "Fix the mentioned issue before rebooking.",
            "Call helpdesk if you need help: 6304629308.",
        ],
    }

    steps = fix_steps.get(detected_reason, fix_steps["other"])

    client = get_anthropic_client()
    if not client:
        # Detailed fallback without AI
        explanation = (
            f"❌ Your {crop_name} booking for {slot_date} was rejected.\n\n"
            f"📋 Officer's reason: {reason if reason else 'No reason provided'}\n\n"
            f"✅ HOW TO FIX THIS:\n"
        )
        for i, step in enumerate(steps, 1):
            explanation += f"{i}. {step}\n"
        explanation += f"\n📞 Need help? Call: 6304629308\n\n💪 Don't give up! Book a new slot after fixing the issue."
        return JsonResponse({"explanation": explanation, "detected_reason": detected_reason, "fix_steps": steps})

    prompt = f"""A farmer's procurement booking was REJECTED. Explain this clearly and kindly.

BOOKING DETAILS:
- Crop: {crop_name}
- Booking Date: {slot_date}
- Estimated quantity booked: {estimated_qty} quintals
- Farmer's total land: {total_land} acres
- Maximum expected quantity for this land: {max_expected:.0f} quintals
- Officer's rejection reason: "{reason if reason else 'No reason written by officer'}"
- Detected rejection category: {detected_reason}

PRE-IDENTIFIED FIX STEPS:
{chr(10).join(f"{i+1}. {s}" for i, s in enumerate(steps))}

WRITE A RESPONSE THAT HAS EXACTLY THESE SECTIONS:

❌ WHY YOUR BOOKING WAS REJECTED:
[Explain the rejection reason in 2 simple sentences. Use very simple words. If no reason given, say officer did not write a reason.]

📋 WHAT WENT WRONG:
[One clear sentence explaining the specific problem]

✅ HOW TO FIX THIS — STEP BY STEP:
1. [First fix step]
2. [Second fix step]  
3. [Third fix step]

💰 GOOD NEWS:
[One encouraging sentence — tell them they can rebook immediately and their crop will still be bought at MSP]

📞 NEED HELP?
Call: 6304629308 | Email: governmentofindia@gmail.com | Hours: 9AM-6PM Mon-Sat

Keep it simple. Like talking to a farmer who may not be very educated. Be kind and encouraging."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        explanation = response.content[0].text
    except Exception as e:
        explanation = (
            f"❌ Your {crop_name} booking for {slot_date} was rejected.\n\n"
            f"Officer's reason: {reason if reason else 'No reason provided'}\n\n"
            "✅ HOW TO FIX:\n"
        )
        for i, step in enumerate(steps, 1):
            explanation += f"{i}. {step}\n"
        explanation += "\n📞 Call helpdesk: 6304629308"

    return JsonResponse({
        "explanation": explanation,
        "detected_reason": detected_reason,
        "fix_steps": steps,
        "crop": crop_name,
        "date": str(slot_date),
    })
