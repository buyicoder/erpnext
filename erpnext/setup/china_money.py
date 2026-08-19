from decimal import Decimal, ROUND_HALF_UP

from frappe.utils import money_in_words as frappe_money_in_words


_DIGITS = "零壹贰叁肆伍陆柒捌玖"
_SMALL_UNITS = ("", "拾", "佰", "仟")
_SECTION_UNITS = ("", "万", "亿", "兆")


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
