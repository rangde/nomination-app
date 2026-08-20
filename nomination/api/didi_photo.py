import base64
import binascii
import re

import frappe

PHOTO_FIELD = "photo_of_didi"

# the web form posts a data url: data:image/jpeg;base64,....
DATA_URL_RE = re.compile(r"^data:image/(?P<subtype>[\w.+-]+);base64,(?P<data>.+)$", re.S)

EXTENSION_MAP = {
	"jpeg": "jpg",
	"jpg": "jpg",
	"png": "png",
	"webp": "webp",
	"heic": "heic",
	"heif": "heif",
}

MAX_PHOTO_BYTES = 10 * 1024 * 1024


def _parse_photo(photo_base64):
	"""Return (image bytes, file extension) for a data url or bare base64 string."""
	raw = (photo_base64 or "").strip()
	if not raw:
		return None, None

	extension = "jpg"
	match = DATA_URL_RE.match(raw)
	if match:
		extension = EXTENSION_MAP.get(match.group("subtype").lower(), "jpg")
		raw = match.group("data")

	try:
		content = base64.b64decode(raw, validate=True)
	except (binascii.Error, ValueError):
		return None, None

	if not content or len(content) > MAX_PHOTO_BYTES:
		return None, None

	return content, extension


def save_didi_photo(docname, photo_base64):
	"""Store the captured photo as a private attachment and link it on the doc."""
	content, extension = _parse_photo(photo_base64)
	if not content:
		return None

	try:
		file_name = f"Photo of Didi - {docname}.{extension}"

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
				"content": content,
				"attached_to_doctype": "Nomination Form",
				"attached_to_name": docname,
				"attached_to_field": PHOTO_FIELD,
				"is_private": 1,
			}
		)
		_file.insert(ignore_permissions=True)

		frappe.db.set_value("Nomination Form", docname, PHOTO_FIELD, _file.file_url)

		return _file.file_url

	except Exception:
		frappe.log_error(frappe.get_traceback(), "Didi Photo Attachment Error")
		return None
