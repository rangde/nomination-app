import base64
import os

import frappe
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from frappe.utils.pdf import get_pdf

NONCE_SIZE = 12


def _enc_file_name(docname):
	return f"Credit Report - {docname}.enc"


def _get_aes_key():
	"""Return the 32-byte AES key, generating and persisting one on first use."""
	key_b64 = frappe.conf.get("credit_report_aes_key")
	if not key_b64:
		key = AESGCM.generate_key(bit_length=256)
		key_b64 = base64.b64encode(key).decode()
		from frappe.installer import update_site_config

		update_site_config("credit_report_aes_key", key_b64)
	return base64.b64decode(key_b64)


def _encrypt(plaintext: bytes) -> bytes:
	nonce = os.urandom(NONCE_SIZE)
	ciphertext = AESGCM(_get_aes_key()).encrypt(nonce, plaintext, None)
	return nonce + ciphertext


def _decrypt(blob: bytes) -> bytes:
	nonce, ciphertext = blob[:NONCE_SIZE], blob[NONCE_SIZE:]
	return AESGCM(_get_aes_key()).decrypt(nonce, ciphertext, None)


def generate_credit_report(docname, report_base64):
	"""Encrypt the report HTML with AES and store it as a private file."""
	if not report_base64:
		return None

	try:
		html_bytes = base64.b64decode(report_base64)
		encrypted = _encrypt(html_bytes)
		file_name = _enc_file_name(docname)

		existing = frappe.get_all(
			"File",
			filters={
				"attached_to_doctype": "Nomination Form",
				"attached_to_name": docname,
				"file_name": file_name,
			},
			pluck="name",
		)
		if existing:
			frappe.delete_doc("File", existing[0], force=True)

		_file = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": file_name,
				"content": encrypted,
				"attached_to_doctype": "Nomination Form",
				"attached_to_name": docname,
				"is_private": 1,
			}
		)
		_file.insert(ignore_permissions=True)
		return _file.file_url

	except Exception:
		frappe.log_error(frappe.get_traceback(), "Credit Report Encryption Error")
		return None


def _check_permission():
	if frappe.session.user == "Guest":
		frappe.throw("Not logged in", frappe.PermissionError)
	if "System Manager" not in frappe.get_roles(frappe.session.user):
		frappe.throw("Not permitted to view the credit report", frappe.PermissionError)


def _get_report_html(docname):
	"""Decrypt the stored credit report and return its HTML, or None."""
	file_name = frappe.db.get_value(
		"File",
		{
			"attached_to_doctype": "Nomination Form",
			"attached_to_name": docname,
			"file_name": _enc_file_name(docname),
		},
		"name",
	)
	if not file_name:
		return None

	file_doc = frappe.get_doc("File", file_name)
	with open(file_doc.get_full_path(), "rb") as f:
		encrypted = f.read()

	return _decrypt(encrypted).decode("utf-8")


@frappe.whitelist()
def get_credit_report(docname):
	"""Decrypt the report and return it as a base64-encoded PDF."""
	_check_permission()

	html = _get_report_html(docname)
	if not html:
		return {"pdf_base64": None}

	pdf_content = get_pdf(html)
	return {
		"pdf_base64": base64.b64encode(pdf_content).decode(),
		"file_name": f"Credit Report - {docname}.pdf",
	}


@frappe.whitelist()
def get_credit_report_html(docname):
	"""Decrypt the report and return its raw HTML."""
	_check_permission()

	return {"html": _get_report_html(docname)}
