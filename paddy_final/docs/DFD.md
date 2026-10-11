# Data Flow Diagrams (DFD)
## Paddy Procurement System

---

### Level 0 (Context Diagram)

```
                    +------------------+
                    |                  |
    Farmer ---------->                  ----------> Farmer
    (Register,        |   PADDY         |           (Slots, Bills,
     Book Slot)       |   PROCUREMENT   |            Payments)
                    |   SYSTEM        |
    Officer ---------->                  ----------> Officer
    (Validate,        |                  |           (Dashboard,
     Record, Approve) |                  |            Reports)
                    |                  |
    Admin ---------->                  ----------> Admin
    (Manage)          +------------------+           (Reports, Config)
```

---

### Level 1

**Processes:**
1. **P1: Registration** – Farmer data → Validate → Farmer, LandDetails
2. **P2: Slot Booking** – Farmer + Date → Check availability → SlotBooking
3. **P3: Procurement** – SlotBooking + Weight + MSP → Procurement, Bill
4. **P4: Payment** – Bill → Approve → Payment

**Data Stores:**
- D1: Farmer
- D2: LandDetails
- D3: Crop (crop type / MSP reference)
- D4: SlotBooking
- D5: Procurement
- D6: Bill
- D7: Payment
- D8: Admin

**Flows:**
- Farmer → P1 (Registration data) → D1, D2
- Farmer → P2 (Booking request) → D4
- Officer → P3 (Weight, validation) → D5, D6 ← D4, D1, D3
- Officer → P4 (Approval) → D7 ← D6
