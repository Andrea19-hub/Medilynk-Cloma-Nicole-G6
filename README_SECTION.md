## Core Feature: Medicine Availability Management and Search

Medilynk helps people find which participating pharmacies currently have the medicine they need. Pharmacists keep their medicine availability up to date; medicine seekers search and filter it. (Reservations, online payments, purchases and delivery are out of scope per the SDD.)

### Flow
1. A **Pharmacist** sets up their pharmacy profile (name, general location, contact number).
2. The pharmacist lists medicines and sets each one's availability: **Available**, **Low Stock** or **Out of Stock**. Every status change records the date and time of the last availability update.
3. A **Medicine Seeker** searches by medicine name and filters by availability, pharmacy and location. Each result shows the pharmacy name, general location, availability status and when it was last updated.
4. An **Admin** manages users, participating pharmacies (activate/deactivate) and medicine information.

### Roles
| Role | Can do |
|---|---|
| Medicine Seeker | Search and filter medicine availability (read-only) |
| Pharmacist | Create/update their pharmacy; add, edit, delete their own medicines; quickly update availability |
| Admin | Activate/deactivate pharmacies; edit or delete any medicine listing; manage users |

### Models and relationships
- `User` 1 -- 1 `Pharmacy` (OneToOne, a pharmacist owns one pharmacy)
- `Pharmacy` 1 -- * `Medicine` (ForeignKey)

### Validation
Pharmacy name unique and at least 3 characters; location required; contact number format checked; medicine name at least 2 characters; no duplicate medicine + strength within a pharmacy; availability limited to the allowed statuses; pharmacists can only modify their own listings; unique email and matching passwords at registration.

## Setup
```bash
git clone <repo-url>
cd <repo>
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```
Create a `.env` file in the project root (never commit it):
```
SECRET_KEY=
DEBUG=True
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=5432
```
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
After creating the superuser, set its **Role** to *Admin* in the Django admin (Users).

## Test Accounts
| Role | Username | Password |
|---|---|---|
| Admin | (fill in) | (fill in) |
| Pharmacist | (fill in) | (fill in) |
| Medicine Seeker | (fill in) | (fill in) |
