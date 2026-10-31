# -*- coding: utf-8 -*-

from unicodedata import normalize
from ..Pattern import Pattern


class UnicodeNormalize(Pattern):
	"""
	Apply the explicitly selected Unicode normalization form.
	"""

	def __init__(self, form: str = 'NFC') -> None:
		if form not in ('NFC', 'NFD', 'NFKC', 'NFKD'):
			raise ValueError('form must be NFC, NFD, NFKC, or NFKD')
		self.form = form
		return

	def __call__(self, col: str) -> str:
		return normalize(self.form, col)
