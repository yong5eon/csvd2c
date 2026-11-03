# -*- coding: utf-8 -*-

__all__ = (
	'Error',
)


class Error(Exception):
	"""
	Base exception for csvd2c validation failures.
	"""

	def __init__(self, message: str) -> None:
		super().__init__(message)
		self.message = message
		return
