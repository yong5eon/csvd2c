# -*- coding: utf-8 -*-

from abc import (
	ABC,
	abstractmethod,
)


class Error(ABC):
	"""
	Handle rejected column data by returning a replacement or raising an exception.
	"""

	@abstractmethod
	def __call__(self, col: str) -> str:
		raise NotImplementedError('Subclasses must implement this method')
