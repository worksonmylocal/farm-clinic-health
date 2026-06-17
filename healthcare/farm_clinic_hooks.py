import frappe


def auto_create_leave_application(doc, method):
    """
    Triggered after Patient Encounter is saved.
    If a medical certificate is issued, automatically creates
    a Leave Application in HR for the linked employee.
    """

    if not (doc.custom_medical_certificate_issued and
            doc.custom_certificate_valid_from and
            doc.custom_certificate_valid_to):
        return

    patient = frappe.get_doc("Patient", doc.patient)

    if not patient.custom_employee_id:
        frappe.msgprint(
            "Patient has no Employee ID linked. Leave Application not created.",
            alert=True
        )
        return

    existing = frappe.db.exists("Leave Application", {
        "employee": patient.custom_employee_id,
        "from_date": doc.custom_certificate_valid_from,
        "to_date": doc.custom_certificate_valid_to,
    })

    if existing:
        return

    allocation = frappe.db.exists("Leave Allocation", {
        "employee": patient.custom_employee_id,
        "leave_type": "Sick Leave",
        "from_date": ["<=", doc.custom_certificate_valid_from],
        "to_date": [">=", doc.custom_certificate_valid_to],
        "docstatus": 1
    })

    if not allocation:
        frappe.msgprint(
            f"No Sick Leave allocation found for {patient.custom_employee_id}. "
            "Please ask HR to allocate Sick Leave for this employee.",
            alert=True
        )
        return

    try:
        leave_app = frappe.new_doc("Leave Application")
        leave_app.employee = patient.custom_employee_id
        leave_app.leave_type = "Sick Leave"
        leave_app.from_date = doc.custom_certificate_valid_from
        leave_app.to_date = doc.custom_certificate_valid_to
        leave_app.description = (
            f"Auto-created from Patient Encounter {doc.name} "
            f"- Medical Certificate Issued"
        )
        leave_app.status = "Open"
        leave_app.insert(ignore_permissions=True)

        frappe.msgprint(
            f"Leave Application {leave_app.name} created successfully "
            f"for {patient.custom_employee_id}",
            alert=True
        )

    except Exception as e:
        frappe.log_error(
            message=str(e),
            title="Leave Application Auto-Creation Failed"
        )
        frappe.msgprint(
            f"Could not create Leave Application: {str(e)}",
            alert=True
        )