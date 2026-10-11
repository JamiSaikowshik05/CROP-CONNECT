# Flowcharts
## Paddy and Groundnut Procurement System

---

### 1. Farmer Registration Flow

```
START
  → Enter Name, Aadhaar, Phone, Password
  → Validate Aadhaar (format/length)
  → Submit
  → DB: Check if Aadhaar already exists
  → If exists: Show error "Already registered"
  → If new: Insert Farmer, redirect to Login
END
```

### 2. Farmer Slot Booking Flow

```
START
  → Farmer Login
  → Dashboard → Book Slot
  → Select Date
  → System: Get available slots for date
  → Farmer selects slot time
  → Check slot capacity (max per slot)
  → If available: Create SlotBooking, show success
  → If full: Show "Slot full, choose another"
END
```

### 3. Procurement (Officer) Flow

```
START
  → Officer Login
  → View today's slot bookings
  → Select farmer/booking
  → Validate Aadhaar & Land (if not already)
  → Enter weight (kg), moisture % (optional)
  → System: Validate weight > 0, apply MSP rate
  → Calculate amount = (weight × MSP) - deductions if any
  → Create Procurement record
  → Generate Bill
  → Show invoice to farmer
END
```

### 4. Payment Approval Flow

```
START
  → Officer/Admin views pending payments (bills not paid)
  → Select bill
  → Approve Payment: enter mode (e.g. Bank/UPI), reference
  → Update Payment record, mark Bill as paid
  → Notify farmer (optional)
END
```

### 5. Login Flow

```
START
  → Enter Email, Password
  → Validate format
  → Lookup user in Admin / Officer / Farmer
  → If found and password match: Create session, redirect to role dashboard
  → Else: Show "Invalid credentials"
END
```
