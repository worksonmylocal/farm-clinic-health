import frappe
from frappe import _
from datetime import date, timedelta


@frappe.whitelist()
def get_clinic_summary():
    today = date.today().isoformat()
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    month_start = date.today().replace(day=1).isoformat()

    today_count = frappe.db.count("Timaflor Patient Encounter", {"date": today})
    week_count = frappe.db.count("Timaflor Patient Encounter", {"date": [">=", week_ago]})
    month_count = frappe.db.count("Timaflor Patient Encounter", {"date": [">=", month_start]})
    total_patients = frappe.db.count("Timaflor Patient")

    pending_sickoff = frappe.db.count("Sick Off Application", {
        "workflow_state": ["in", ["Pending HR Review", "Pending HOD Approval", "Pending FM/GM Approval"]]
    })
    active_referrals = frappe.db.count("External Referral", {"patient_returned": 0})
    month_injuries = frappe.db.count("Accident Injury Report", {"date_of_accident": [">=", month_start]})

    return {
        "today_count": today_count,
        "week_count": week_count,
        "month_count": month_count,
        "total_patients": total_patients,
        "pending_sickoff": pending_sickoff,
        "active_referrals": active_referrals,
        "month_injuries": month_injuries,
    }


@frappe.whitelist()
def get_encounters_by_dept(period="month"):
    start = _get_start_date(period)
    data = frappe.db.sql("""
        SELECT department, COUNT(*) as count
        FROM `tabTimaflor Patient Encounter`
        WHERE date >= %s AND department IS NOT NULL
        GROUP BY department
        ORDER BY count DESC
    """, start, as_dict=True)
    return data


@frappe.whitelist()
def get_week_encounters():
    data = frappe.db.sql("""
        SELECT date, COUNT(*) as count
        FROM `tabTimaflor Patient Encounter`
        WHERE date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY date
        ORDER BY date ASC
    """, as_dict=True)
    return data


@frappe.whitelist()
def get_recent_encounters():
    return frappe.get_all("Timaflor Patient Encounter",
        fields=["name", "patient", "department", "date", "diagnosis"],
        order_by="creation desc",
        limit=10)


@frappe.whitelist()
def get_pending_sickoff():
    return frappe.get_all("Sick Off Application",
        filters={"workflow_state": ["in", ["Pending HR Review", "Pending HOD Approval", "Pending FM/GM Approval"]]},
        fields=["name", "patient", "department", "workflow_state", "sick_off_days_approved"],
        order_by="creation desc",
        limit=10)


@frappe.whitelist()
def get_active_referrals():
    return frappe.get_all("External Referral",
        filters={"patient_returned": 0},
        fields=["name", "patient", "facility_referred_to", "referral_type", "date_of_referral"],
        order_by="creation desc",
        limit=10)


@frappe.whitelist()
def get_recent_accidents():
    return frappe.get_all("Accident Injury Report",
        fields=["name", "patient", "department", "nature_of_accident", "date_of_accident"],
        order_by="creation desc",
        limit=10)


@frappe.whitelist()
def get_manager_summary(period="month"):
    start = _get_start_date(period)

    total_visits = frappe.db.count("Timaflor Patient Encounter", {"date": [">=", start]})

    sickoff_data = frappe.db.sql("""
        SELECT COALESCE(SUM(sick_off_days_approved), 0) as total
        FROM `tabSick Off Application`
        WHERE creation >= %s
    """, start, as_dict=True)
    total_sickoff_days = sickoff_data[0].total if sickoff_data else 0

    total_injuries = frappe.db.count("Accident Injury Report", {"date_of_accident": [">=", start]})
    total_referrals = frappe.db.count("External Referral", {"date_of_referral": [">=", start]})

    return {
        "total_visits": total_visits,
        "total_sickoff_days": int(total_sickoff_days or 0),
        "total_injuries": total_injuries,
        "total_referrals": total_referrals,
    }


@frappe.whitelist()
def get_sickoff_by_dept(period="month"):
    start = _get_start_date(period)
    return frappe.db.sql("""
        SELECT department, COUNT(*) as count,
               COALESCE(SUM(sick_off_days_approved), 0) as total_days
        FROM `tabSick Off Application`
        WHERE creation >= %s AND department IS NOT NULL
        GROUP BY department
        ORDER BY total_days DESC
    """, start, as_dict=True)


@frappe.whitelist()
def get_sickoff_by_type(period="month"):
    start = _get_start_date(period)
    return frappe.db.sql("""
        SELECT classification, COUNT(*) as count
        FROM `tabSick Off Application`
        WHERE creation >= %s AND classification IS NOT NULL
        GROUP BY classification
    """, start, as_dict=True)


@frappe.whitelist()
def get_injuries_by_dept(period="month"):
    start = _get_start_date(period)
    return frappe.db.sql("""
        SELECT department, COUNT(*) as count
        FROM `tabAccident Injury Report`
        WHERE date_of_accident >= %s AND department IS NOT NULL
        GROUP BY department
        ORDER BY count DESC
    """, start, as_dict=True)


@frappe.whitelist()
def get_injuries_by_severity(period="month"):
    start = _get_start_date(period)
    return frappe.db.sql("""
        SELECT nature_of_accident, COUNT(*) as count
        FROM `tabAccident Injury Report`
        WHERE date_of_accident >= %s AND nature_of_accident IS NOT NULL
        GROUP BY nature_of_accident
    """, start, as_dict=True)


@frappe.whitelist()
def get_referrals_by_type(period="month"):
    start = _get_start_date(period)
    return frappe.db.sql("""
        SELECT referral_type, COUNT(*) as count
        FROM `tabExternal Referral`
        WHERE date_of_referral >= %s AND referral_type IS NOT NULL
        GROUP BY referral_type
        ORDER BY count DESC
    """, start, as_dict=True)


@frappe.whitelist()
def get_referrals_by_facility(period="month"):
    start = _get_start_date(period)
    return frappe.db.sql("""
        SELECT facility_referred_to, COUNT(*) as count
        FROM `tabExternal Referral`
        WHERE date_of_referral >= %s AND facility_referred_to IS NOT NULL
        GROUP BY facility_referred_to
        ORDER BY count DESC
        LIMIT 8
    """, start, as_dict=True)


@frappe.whitelist()
def get_top_diagnoses(period="month"):
    start = _get_start_date(period)
    return frappe.db.sql("""
        SELECT diagnosis, COUNT(*) as count
        FROM `tabTimaflor Patient Encounter`
        WHERE date >= %s AND diagnosis IS NOT NULL AND diagnosis != ''
        GROUP BY diagnosis
        ORDER BY count DESC
        LIMIT 8
    """, start, as_dict=True)


@frappe.whitelist()
def get_procedures(period="month"):
    start = _get_start_date(period)
    return frappe.db.sql("""
        SELECT procedure_performed, COUNT(*) as count
        FROM `tabTimaflor Patient Encounter`
        WHERE date >= %s AND procedure_performed IS NOT NULL
        AND procedure_performed != '' AND procedure_performed != 'None'
        GROUP BY procedure_performed
        ORDER BY count DESC
    """, start, as_dict=True)


@frappe.whitelist()
def get_recent_injuries():
    return frappe.get_all("Accident Injury Report",
        fields=["name", "patient", "department", "nature_of_accident", "date_of_accident"],
        order_by="creation desc",
        limit=8)


def _get_start_date(period):
    today = date.today()
    if period == "month":
        return today.replace(day=1).isoformat()
    elif period == "quarter":
        quarter_month = (today.month - 1) // 3 * 3 + 1
        return today.replace(month=quarter_month, day=1).isoformat()
    else:
        return today.replace(month=1, day=1).isoformat()