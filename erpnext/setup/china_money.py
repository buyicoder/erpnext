from decimal import Decimal, ROUND_HALF_UP

import frappe
from frappe.utils import fmt_money as frappe_format_money
from frappe.utils import money_in_words as frappe_money_in_words

_DIGITS = "零壹贰叁肆伍陆柒捌玖"
_SMALL_UNITS = ("", "拾", "佰", "仟")
_SECTION_UNITS = ("", "万", "亿", "兆")
_DERIVED_WORD_FIELDS = ("in_words", "base_in_words", "total_amount_in_words")
_SUPPORTED_DOCTYPES = (
	"Quotation",
	"Sales Order",
	"Delivery Note",
	"Sales Invoice",
	"POS Invoice",
	"Supplier Quotation",
	"Purchase Order",
	"Purchase Receipt",
	"Purchase Invoice",
	"Payment Entry",
	"Journal Entry",
)


def _section_in_words(section: int) -> str:
	result = ""
	zero_pending = False
	position = 0
	while section:
		digit = section % 10
		if digit:
			if zero_pending:
				result = _DIGITS[0] + result
				zero_pending = False
			result = _DIGITS[digit] + _SMALL_UNITS[position] + result
		elif result:
			zero_pending = True
		section //= 10
		position += 1
	return result


def cny_amount_in_words(amount) -> str:
	"""Format a numeric amount using standard Chinese financial uppercase numerals."""
	value = Decimal(str(amount or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
	prefix = "负" if value < 0 else ""
	value = abs(value)
	total_fen = int(value * 100)
	whole, fraction = divmod(total_fen, 100)
	jiao, fen = divmod(fraction, 10)

	if whole:
		sections = []
		remaining = whole
		while remaining:
			sections.append(remaining % 10_000)
			remaining //= 10_000

		parts = []
		zero_pending = False
		for index in range(len(sections) - 1, -1, -1):
			section = sections[index]
			if not section:
				if parts:
					zero_pending = True
				continue
			if parts and (zero_pending or section < 1_000):
				parts.append(_DIGITS[0])
			parts.append(_section_in_words(section) + _SECTION_UNITS[index])
			zero_pending = False
		whole_text = "".join(parts)
	else:
		whole_text = _DIGITS[0]

	result = f"{prefix}人民币{whole_text}元"
	if not jiao and not fen:
		return result + "整"
	if jiao:
		result += _DIGITS[jiao] + "角"
	elif whole and fen:
		result += _DIGITS[0]
	if fen:
		result += _DIGITS[fen] + "分"
	return result


def money_in_words(amount, currency=None, *args, **kwargs):
	if currency == "CNY":
		return cny_amount_in_words(amount)
	return frappe_money_in_words(amount, currency, *args, **kwargs)


def format_china_money(amount, currency=None, precision=None):
	"""Format exact CNY values for formal documents using the yuan symbol."""
	if currency == "CNY":
		precision = (
			frappe.utils.cint(frappe.db.get_default("currency_precision")) or 2
			if precision is None
			else max(0, int(precision))
		)
		quantum = Decimal(1).scaleb(-precision)
		value = Decimal(str(amount or 0)).quantize(quantum, rounding=ROUND_HALF_UP)
		return f"¥{value:,.{precision}f}"
	return frappe_format_money(amount, currency=currency, precision=precision)


def _get_cny_word_updates(doc):
	"""Return changed Chinese amount-in-words fields without saving the document."""
	before = {field: doc.get(field) for field in _DERIVED_WORD_FIELDS}

	if doc.doctype == "Journal Entry":
		currency = doc.get("total_amount_currency")
		doc.total_amount_in_words = money_in_words(abs(doc.get("total_amount") or 0), currency)
	else:
		doc.set_total_in_words()

	return {
		field: value
		for field in _DERIVED_WORD_FIELDS
		if (value := doc.get(field))
		and value.startswith("人民币")
		and value != before[field]
	}


def _candidate_names(doctype, cny_companies, limit=None, page_length=500):
	meta = frappe.get_meta(doctype)
	or_filters = []

	for field in ("currency", "paid_from_account_currency", "paid_to_account_currency", "total_amount_currency"):
		if meta.get_field(field):
			or_filters.append([doctype, field, "=", "CNY"])

	if meta.get_field("company"):
		if cny_companies:
			or_filters.append([doctype, "company", "in", cny_companies])

	if not or_filters:
		return []

	start = 0
	while limit is None or start < limit:
		batch_size = min(page_length, limit - start) if limit is not None else page_length
		names = frappe.get_all(
			doctype,
			or_filters=or_filters,
			pluck="name",
			order_by="creation asc, name asc",
			limit_start=start,
			limit_page_length=batch_size,
		)
		if not names:
			break
		yield from names
		start += len(names)
		if len(names) < batch_size:
			break


def rebuild_cny_amount_in_words(dry_run=True, doctypes=None, limit=None):
	"""Recalculate historical CNY amount-in-words fields without changing transaction amounts.

	The operation is a dry run unless ``dry_run=False`` is passed explicitly. Applied
	updates write only derived word fields and preserve each document's modified timestamp.
	"""
	if doctypes is None:
		doctypes = list(_SUPPORTED_DOCTYPES)
	elif isinstance(doctypes, str):
		doctypes = frappe.parse_json(doctypes) if doctypes.lstrip().startswith("[") else [doctypes]

	unsupported = sorted(set(doctypes) - set(_SUPPORTED_DOCTYPES))
	if unsupported:
		raise ValueError(f"Unsupported DocTypes: {', '.join(unsupported)}")

	dry_run = frappe.utils.cint(dry_run) != 0
	limit = frappe.utils.cint(limit) or None
	remaining = limit
	cny_companies = frappe.get_all("Company", filters={"default_currency": "CNY"}, pluck="name")
	report = {
		"dry_run": dry_run,
		"documents_scanned": 0,
		"documents_changed": 0,
		"fields_changed": 0,
		"by_doctype": {},
		"changes": [],
		"changes_truncated": False,
	}

	for doctype in doctypes:
		if remaining is not None and remaining <= 0:
			break
		names = _candidate_names(doctype, cny_companies, remaining)
		doctype_report = {"scanned": 0, "changed": 0, "fields_changed": 0}
		report["by_doctype"][doctype] = doctype_report

		for name in names:
			doc = frappe.get_doc(doctype, name)
			updates = _get_cny_word_updates(doc)
			doctype_report["scanned"] += 1
			report["documents_scanned"] += 1
			if remaining is not None:
				remaining -= 1

			if not updates:
				continue
			doctype_report["changed"] += 1
			doctype_report["fields_changed"] += len(updates)
			report["documents_changed"] += 1
			report["fields_changed"] += len(updates)
			if len(report["changes"]) < 100:
				report["changes"].append({"doctype": doctype, "name": name, "fields": sorted(updates)})
			else:
				report["changes_truncated"] = True
			if not dry_run:
				frappe.db.set_value(doctype, name, updates, update_modified=False)

	if not dry_run and report["documents_changed"]:
		frappe.db.commit()

	return report
