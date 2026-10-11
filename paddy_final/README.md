# Paddy and Groundnut Procurement System

A full-stack procurement system for **Paddy** and **Groundnut** — for Farmers, Procurement Officers, and Admins. Natural, farmer-friendly interface. Supports registration, Aadhaar & land validation, slot booking, weight validation, MSP calculation, and payment approval.

## Stakeholders

- **Farmer**: Register, book slots, bring paddy, receive payment
- **Officer**: Validate land, record weight, process procurement, approve payments
- **Admin**: Manage users, view reports, system configuration

## Tech Stack

- **Backend**: Node.js, Express
- **Database**: SQLite (better-sqlite3)
- **Frontend**: HTML, CSS, JavaScript (vanilla)

## Quick Start

### 1. Install dependencies

```bash
npm install
```

### 2. Initialize database (creates tables + sample data)

```bash
npm run setup
```

(Or run `npm run init-db` then `npm run seed` separately.)

### 3. Start the server

```bash
npm start
```

If port 3000 is in use, stop any existing Node process or set `PORT=3001` (e.g. `set PORT=3001 && npm start` on Windows).

### 4. Open in browser

- **App**: http://localhost:3000
- **API**: http://localhost:3000/api

## Default Login

| Role   | Email           | Password |
|--------|-----------------|----------|
| Admin  | admin@procure.gov | admin123 |
| Officer| officer@procure.gov | officer123 |
| Farmer | (register or use seeded farmer) | (your password) |

## Project Structure

```
paddy procurement/
├── docs/           # SRS, WBS, DFD, ER diagram
├── server/         # Express backend + SQLite
├── public/         # Frontend (HTML, CSS, JS)
├── database/       # Schema SQL (reference)
└── package.json
```

## Phases (WBS)

1. Requirement Analysis – SRS in `docs/SRS.md`
2. System Design – Flowchart, DFD, ER in `docs/`
3. Database – Tables in `server/scripts/initDb.js`
4. Backend – APIs in `server/`
5. Frontend – Pages in `public/`
6. Run: `npm install && npm run init-db && npm start`
