# Work Breakdown Structure (WBS)
## Paddy and Groundnut Procurement System

---

### Phase 1: Requirement Analysis (Week 1)
- Study procurement system
- Identify stakeholders (Farmer, Officer, Admin)
- Define system objectives
- Prepare SRS document ✅ (`docs/SRS.md`)

### Phase 2: System Design (Week 2)
- Create Flowchart ✅ (`docs/Flowchart.md`)
- Create DFD (Level 0 & Level 1) ✅ (`docs/DFD.md`)
- Design ER Diagram ✅ (`docs/ER-Diagram.md`)
- Design Database Schema ✅ (in `server/scripts/initDb.js` and `database/schema.sql`)
- UI Wireframes ✅ (implemented in `public/`)

### Phase 3: Database Development (Week 3)
- Create Tables: Farmer, LandDetails, Crop, SlotBooking, Procurement, Bill, Payment, Admin ✅
- Insert sample data ✅ (`server/scripts/seed.js`)
- Write stored procedures / server-side logic ✅ (in Express routes)

### Phase 4: Backend Development (Week 4–5)
- Farmer Registration Module ✅
- Aadhaar & Land Validation ✅
- Slot Booking Module ✅
- Weight Validation Logic ✅
- MSP Calculation ✅
- Payment Approval Module ✅

### Phase 5: Frontend Development (Week 6)
- Login Page ✅
- Registration Form ✅
- Dashboard ✅
- Slot Booking UI ✅
- Admin Panel UI ✅
- Invoice Page ✅

### Phase 6: Integration & Testing (Week 7)
- Connect frontend with backend ✅
- Unit / integration testing (manual + API)
- Bug fixing
- Security (basic auth, validation)

### Phase 7: Deployment & Documentation (Week 8)
- Deploy on Localhost / Server ✅ (`npm start`)
- Documentation ✅ (README, SRS, docs)
