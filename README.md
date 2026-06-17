# Farm Clinic Health Module

A customized ERPNext Healthcare module for farm clinic management, built on 
top of [Frappe Health](https://github.com/frappe/health).

Designed for flower farms and agricultural operations with on-site clinics,
this module extends ERPNext Healthcare with occupational health tracking,
farm-specific workflows, and HR integration.

---

## What This Module Provides

### Custom Doctypes
- **Occupational Exposure Log** — Record pesticide/chemical exposure incidents
- **Work Related Injury Form** — Structured injury capture with cause classification
- **Referral Tracking** — Track worker referrals to external facilities
- **Wellness Programme Tracker** — Record participation in farm wellness activities

### Custom Fields
- **Patient** — Employee ID (linked to HR), Farm Department, Employment Type
- **Patient Encounter** — Is Work Related, Referred From Department, 
  Medical Certificate Issued, Certificate Valid From/To

### Workflows
- **Clinic Patient Encounter Flow** — Draft → In Progress → Awaiting Lab 
  Results → Awaiting Pharmacy → Closed

### Automated Notifications
- Doctor notified when new appointment is created
- Lab Technician notified when lab test is requested
- Doctor notified when lab results are ready
- Pharmacist notified when prescription is ready
- Clinic In-Charge notified when patient is referred
- HR Manager notified when medical certificate is issued

### HR Integration
- Medical certificate issuance automatically creates a Leave Application
- Sick leave linked directly to patient encounter

### Roles
- Clinic Receptionist
- Clinical Officer
- Pharmacist
- Lab Technician
- Clinic In-Charge
- Farm Director

### Item Groups
- Medical Supplies
  - Medicines & Drugs
  - Dressings & Consumables
  - Lab Supplies
  - PPE & Safety

---

## Requirements

- ERPNext v15
- HRMS v15
- Frappe v15

---

## Installation

### Step 1 — Get the app
```bash
bench get-app healthcare https://github.com/worksonmylocal/farm-clinic-health --branch version-15
```

### Step 2 — Install on your site
```bash
bench --site your-site-name install-app healthcare
bench --site your-site-name migrate
bench restart
```

---

## Post Installation Setup

These steps must be done manually after installation as they are farm-specific:

### 1. Company Setup
- Go to **Company** and set up your farm company details

### 2. Create Departments
- Go to **Department** and create your farm sections
- Examples: Greenhouse A, Packing, Cold Room, Irrigation, Administration

### 3. Create Employees
- Go to **Employee** and import or create all farm worker records
- Ensure each employee has **Employment Type** and **Department** filled

### 4. Create Healthcare Practitioners
- Go to **Healthcare Practitioner** and create records for all clinic staff
- Link each practitioner to their User account
- Add a Practitioner Schedule for appointment booking

### 5. Create Users and Assign Roles
Create a user for each clinic staff member and assign the appropriate role:

| Staff | Role |
|---|---|
| Doctor / Clinical Officer | Clinical Officer |
| Nurse | Nursing User + Clinic Receptionist |
| Pharmacist | Pharmacist |
| Lab Technician | Lab Technician |
| Clinic In-Charge | Clinic In-Charge |
| HR Manager | HR Manager |
| Farm Director | Farm Director |

### 6. Leave Allocation
- Go to **Leave Allocation** and allocate **Sick Leave** for all employees
- This is required for the medical certificate → leave application automation to work

### 7. Drug Formulary
- Go to **Item** and create all medicines stocked in the clinic
- Set **Item Group** to `Medicines & Drugs` for all medicines
- Set **Item Group** to `Dressings & Consumables` for dressings and supplies

### 8. Medical Certificate → Leave Application (Server Script)
The automatic leave application creation requires a Server Script.
Go to **Server Script → New** and create:

- **Script Name:** `Auto Create Leave Application on Medical Certificate`
- **Script Type:** `DocType Event`
- **Reference Document Type:** `Patient Encounter`
- **DocType Event:** `After Save`
- **Enabled:** ✅

Paste the following script:

```python
if doc.custom_medical_certificate_issued and doc.custom_certificate_valid_from \
        and doc.custom_certificate_valid_to:

    patient = frappe.get_doc("Patient", doc.patient)

    if not patient.custom_employee_id:
        frappe.msgprint("Patient has no Employee ID linked.", alert=True)
    else:
        existing = frappe.db.exists("Leave Application", {
            "employee": patient.custom_employee_id,
            "from_date": doc.custom_certificate_valid_from,
            "to_date": doc.custom_certificate_valid_to,
        })

        if not existing:
            allocation = frappe.db.exists("Leave Allocation", {
                "employee": patient.custom_employee_id,
                "leave_type": "Sick Leave",
                "from_date": ["<=", doc.custom_certificate_valid_from],
                "to_date": [">=", doc.custom_certificate_valid_to],
                "docstatus": 1
            })

            if not allocation:
                frappe.msgprint(
                    f"No Sick Leave allocation found for \
                    {patient.custom_employee_id}.",
                    alert=True
                )
            else:
                leave_app = frappe.new_doc("Leave Application")
                leave_app.employee = patient.custom_employee_id
                leave_app.leave_type = "Sick Leave"
                leave_app.from_date = doc.custom_certificate_valid_from
                leave_app.to_date = doc.custom_certificate_valid_to
                leave_app.description = f"Auto-created from {doc.name}"
                leave_app.status = "Open"
                leave_app.insert(ignore_permissions=True)
                frappe.msgprint(
                    f"Leave Application {leave_app.name} created.",
                    alert=True
                )
```

### 9. Enable Server Scripts
```bash
bench --site your-site-name set-config server_script_enabled true
bench --site your-site-name clear-cache
```

---

## Patient Journey

Worker Arrives

↓

Nurse creates appointment + records vitals

↓

Doctor receives notification → opens Patient Encounter

↓

Doctor fills symptoms, diagnosis, prescription, investigations

↓

[Lab Required?]

Yes → Request Lab Test → Lab Tech notified → enters results

→ Doctor notified → reviews results → updates prescription

No  → Close Without Lab

↓

Send to Pharmacy → Pharmacist notified → dispenses medication

↓

Encounter Closed

↓

[Referral Needed?]

Yes → Create Referral Tracking → Clinic In-Charge notified

No  → Done

↓

[Medical Certificate Issued?]

Yes → Leave Application auto-created → HR Manager notified

---

## Known Limitations

- Observation records must be created manually by the Lab Technician 
  and linked to the Patient Encounter
- Drug dispensing stock deduction requires manual stock entry setup
- Email notifications require email configuration per farm

---

## Support

For issues and customization requests, open an issue on this repository.