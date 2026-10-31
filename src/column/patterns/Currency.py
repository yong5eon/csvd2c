# -*- coding: utf-8 -*-

from re import compile
from typing import (
	Mapping,
	Optional,
)
from ..Pattern import Pattern
from ..Error import Error
from .CurrencyData import (
	CURRENCY_ALIASES,
	CURRENCY_CODES,
)

__all__ = (
	'Currency',
	'CURRENCY_CODES',
	'CURRENCY_ALIASES',
)


class Currency(Pattern):
	"""
	Normalize currency prefixes to current ISO 4217 alphabetic codes.

	Use the SIX List One snapshot published on 2026-09-17, including fund,
	metal, testing, and no-currency codes. No network access is performed.
	Bare dollar and yen signs explicitly mean USD and JPY.
	CA/AU/JP/CN followed only by replacement characters or surrogate code
	points are interpreted as CAD/AUD/JPY/CNY respectively.
	Amount text is trimmed but not numerically validated or reformatted.
	Custom prefix mappings override built-in aliases and are copied.
	Default aliases include unambiguous CLDR names and symbols in ten locales.
	CURRENCY_CODES and CURRENCY_ALIASES are immutable module constants.
	"""

	codes = CURRENCY_CODES

	def __init__(
		self,
		mapping: Optional[Mapping[str, str]] = None,
		*,
		error: Optional[Error] = None,
	) -> None:
		if error is not None and not isinstance(error, Error):
			raise TypeError('error must be a column Error instance or None')
		aliases: dict[str, str] = dict(CURRENCY_ALIASES)
		if mapping is not None:
			for prefix, code in mapping.items():
				if not isinstance(prefix, str) or not prefix or prefix != prefix.strip():
					raise ValueError('Currency prefixes must be nonempty strings without surrounding whitespace')
				if not isinstance(code, str) or code not in self.codes:
					raise ValueError('Currency mapping values must be current ISO 4217 codes')
				if prefix in self.codes and prefix != code:
					raise ValueError('An ISO 4217 code cannot be mapped to a different code')
			aliases.update(mapping)
		self.aliases = sorted(aliases.items(), key=lambda item: len(item[0]), reverse=True)
		self.prefixes: dict[str, list[tuple[str, str]]] = {}
		for prefix, code in self.aliases:
			self.prefixes.setdefault(prefix[0], []).append((prefix, code))
		self.damaged = compile(r'^(CA|AU|JP|CN)[\ufffd\ud800-\udfff]+')
		self.countries = {
			'CA': 'CAD',
			'AU': 'AUD',
			'JP': 'JPY',
			'CN': 'CNY',
		}
		self.error = error
		return

	def __call__(self, col: str) -> str:
		text: str = col.strip()
		code: Optional[str] = None
		amount: str = ''
		for prefix, candidate in self.prefixes.get(text[:1], []):
			if text.startswith(prefix):
				code = candidate
				amount = text[len(prefix):].strip()
				break
		if code is None:
			match = self.damaged.match(text)
			if match is not None:
				code = self.countries[match.group(1)]
				amount = text[match.end():].strip()
		if (
			code is None
			or not amount
			or amount[0] not in '0123456789+-.,('
			or '\ufffd' in amount
			or any('\ud800' <= char <= '\udfff' for char in amount)
		):
			if self.error is not None:
				return self.error(col)
			raise ValueError('Value has an unknown currency prefix, missing amount, or damaged amount')
		return '{} {}'.format(code, amount)
