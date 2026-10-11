# Software Requirements Specification (SRS)
## Paddy and Groundnut Procurement System

**Version:** 1.0  
**Date:** March 2025

---

### 1. Introduction

#### 1.1 Purpose
This SRS describes the functional and non-functional requirements for the **Paddy and Groundnut Procurement System** used by government procurement centers to register farmers, validate land and identity, manage slot bookings, record procurement (paddy and groundnut — weight, MSP), generate bills, and process payments.

#### 1.2 Scope
- Farmer registration with Aadhaar and land validation
- Slot booking for procurement dates
- Procurement recording (weight, moisture, MSP calculation)
- Bill generation and payment approval workflow
- Admin and officer dashboards

#### 1.3 Definitions
- **MSP**: Minimum Support Price
- **Procurement**: Purchase of paddy from farmer at MSP by the center

---

### 2. Stakeholders

| Stakeholder | Role | Key Actions |
|-------------|------|-------------|
| **Farmer** | Supplier | Register, book slot, bring paddy, view bills/payments |
| **Officer** | Procurement staff | Validate farmer/land, record weight, create procurement, approve payments |
| **Admin** | System administrator | Manage users, view reports, configure system |

---

### 3. System Objectives

1. **Registration**: Allow farmers to register with Aadhaar and link land details for eligibility.
2. **Slot booking**: Allow farmers to book a time slot for bringing paddy to the center.
3. **Procurement**: Record weight, quality (e.g. moisture), calculate amount at MSP, generate bill.
4. **Payment**: Officer approves payment; system records payment status.
5. **Reporting**: Admin and officers can view procurement and payment reports.

---

### 4. Functional Requirements

#### 4.1 Farmer
- FR1: Register with name, Aadhaar, contact, password.
- FR2: Add/edit land details (survey no, area, village).
- FR3: Book a slot for a chosen date (subject to availability).
- FR4: View own slot bookings and procurement history.
- FR5: View and download invoice/bill for completed procurement.

#### 4.2 Officer
- FR6: Login and view dashboard (today’s slots, pending procurements).
- FR7: Validate farmer (Aadhaar) and land details before procurement.
- FR8: Create procurement record: weight, moisture (if applicable), MSP rate, calculated amount.
- FR9: Generate bill for a procurement.
- FR10: Mark payment as approved and record payment details.

#### 4.3 Admin
- FR11: Login and access admin panel.
- FR12: View list of farmers, officers, procurements, payments.
- FR13: (Optional) Add/edit officers and system parameters (e.g. MSP rates).

---

### 5. Non-Functional Requirements

- **Security**: Passwords stored hashed; session/token for authenticated users.
- **Usability**: Simple, clear UI for low-literacy users where applicable.
- **Performance**: Support at least 100 concurrent users (typical center).
- **Availability**: System available during working hours; data backed up periodically.

---

### 6. Constraints

- Must work on standard browsers (Chrome, Firefox, Edge).
- Initial deployment on localhost/server as per WBS Phase 7.
