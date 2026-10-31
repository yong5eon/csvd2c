# -*- coding: utf-8 -*-

from abc import (
	ABC,
	abstractmethod,
)
from typing import List


class Error(ABC):
	"""
	Handle rejected row data by returning a replacement or raising an exception.
	"""

	@abstractmethod
	def __call__(self, row: List[str]) -> List[str]:
		raise NotImplementedError('Subclasses must implement this method')
