# -*- coding: utf-8 -*-

from contextlib import (
	ExitStack,
	contextmanager,
)
from csv import (
	field_size_limit as csv_field_size_limit,
	reader,
)
from io import TextIOWrapper
from typing import (
	Dict,
	Generic,
	Generator,
	List,
	Mapping,
	Optional,
	Tuple,
	TypeVar,
	Union,
	TYPE_CHECKING,
	cast,
	overload,
)

if TYPE_CHECKING:
	from _csv import Reader

from .header import (
	Error as HeaderError,
	Validator as HeaderValidator,
)
from .row import (
	Error as RowError,
	Validator as RowValidator,
)
from .column import Validator as ColumnValidator

__all__ = (
	'CSV',
	'MAX_FIELD_SIZE',
)

MAX_FIELD_SIZE: int = 2_147_483_647

RecordType = TypeVar(
	'RecordType',
	List[str],
	Mapping[str, str],
)


class CSV(Generic[RecordType]):
	"""
	Read CSV records incrementally and apply row and column validators.
	"""

	@overload
	def __init__(
		self: 'CSV[List[str]]',
		*,
		encoding: str = 'utf-8',
		errors: str = 'strict',
		newline: str = '',
		delimiter: str = ',',
		escapechar: Optional[str] = None,
		strict: bool = True,
		header: None = None,
		row: Optional[RowValidator] = None,
		column: Optional[
			Union[
				Dict[str, ColumnValidator],
				Tuple[ColumnValidator, ...],
			]
		] = None,
		offset: int = 0,
		limit: Optional[int] = None,
		field_size_limit: Optional[int] = None,
	) -> None:
		...

	@overload
	def __init__(
		self: 'CSV[Mapping[str, str]]',
		*,
		encoding: str = 'utf-8',
		errors: str = 'strict',
		newline: str = '',
		delimiter: str = ',',
		escapechar: Optional[str] = None,
		strict: bool = True,
		header: HeaderValidator,
		row: Optional[RowValidator] = None,
		column: Optional[
			Union[
				Dict[str, ColumnValidator],
				Tuple[ColumnValidator, ...],
			]
		] = None,
		offset: int = 0,
		limit: Optional[int] = None,
		field_size_limit: Optional[int] = None,
	) -> None:
		...

	def __init__(
		self,
		*,
		encoding: str = 'utf-8',
		errors: str = 'strict',
		newline: str = '',
		delimiter: str = ',',
		escapechar: Optional[str] = None,
		strict: bool = True,
		header: Optional[HeaderValidator] = None,
		row: Optional[RowValidator] = None,
		column: Optional[
			Union[
				Dict[str, ColumnValidator],
				Tuple[ColumnValidator, ...],
			]
		] = None,
		offset: int = 0,
		limit: Optional[int] = None,
		field_size_limit: Optional[int] = None,
	) -> None:
		"""
		Configure decoding, parsing, validators, and the default read range.

		offset is the number of records to skip and limit is the maximum
		number of records to read with row() and rows(); None means no limit.
		A header read by a header Validator is not counted.
		field_size_limit leaves the current global CSV limit unchanged when
		None. Otherwise it must be an integer from 0 to MAX_FIELD_SIZE;
		bool is rejected. It sets the limit in characters for all CSV readers
		in this interpreter, including existing readers. Closing does not
		restore it, and the maximum does not guarantee sufficient memory.
		"""
		self.encoding = encoding
		self.errors = errors
		self.newline = newline
		self.delimiter = delimiter
		self.escapechar = escapechar
		self.strict = strict
		self.check_header(header)
		self.check_validators(row, column)
		if offset is None:
			raise TypeError('offset must be a non-negative integer')
		self.check_range(offset, limit)
		self.header_validator = header
		self.row_validator = row
		self.column_validators = column
		self.offset = offset
		self.limit = limit
		self.reader: Optional['Reader'] = None
		self.text: Optional[TextIOWrapper] = None
		self.header_data: Optional[List[str]] = None
		self.mapping_header: Optional[Tuple[str, ...]] = None
		self.raw_data: Optional[List[str]] = None
		self.skip: int = 0
		self.remaining: Optional[int] = None
		if field_size_limit is not None:
			if isinstance(field_size_limit, bool) or not isinstance(field_size_limit, int):
				raise TypeError('field_size_limit must be an integer or None')
			if field_size_limit < 0 or field_size_limit > MAX_FIELD_SIZE:
				raise ValueError('field_size_limit must be between 0 and {}'.format(MAX_FIELD_SIZE))
			csv_field_size_limit(field_size_limit)
		return

	@overload
	def open(
		self: 'CSV[List[str]]',
		path: str,
		mode: str = 'rb',
		header: HeaderValidator = ...,
		offset: Optional[int] = None,
		limit: Optional[int] = None,
	) -> Generator['CSV[Mapping[str, str]]', None, None]:
		...

	@overload
	def open(
		self: 'CSV[List[str]]',
		path: str,
		mode: str = 'rb',
		header: None = None,
		offset: Optional[int] = None,
		limit: Optional[int] = None,
	) -> Generator['CSV[List[str]]', None, None]:
		...

	@overload
	def open(
		self: 'CSV[Mapping[str, str]]',
		path: str,
		mode: str = 'rb',
		header: Optional[HeaderValidator] = None,
		offset: Optional[int] = None,
		limit: Optional[int] = None,
	) -> Generator['CSV[Mapping[str, str]]', None, None]:
		...

	@contextmanager
	def open(
		self,
		path: str,
		mode: str = 'rb',
		header: Optional[HeaderValidator] = None,
		offset: Optional[int] = None,
		limit: Optional[int] = None,
	) -> Generator['CSV[RecordType]', None, None]:
		"""
		Open a file for reading and close it on context exit.

		Support rb (default), r, and rt. Binary mode uses TextIOWrapper;
		text modes apply the same encoding, errors, and newline settings.
		header overrides the constructor header Validator for this open only;
		None uses the constructor setting. When a header Validator applies,
		the first record is read and validated before the context is entered;
		a header Error closes the file. Otherwise no record is consumed.
		offset and limit override the constructor read range for this open
		only; None uses the constructor setting, so a constructor limit cannot
		be removed here. The range is counted from the first record after the
		validated header, or from the first record without header validation.
		Nested opens on the same CSV instance are rejected. File, decoding,
		and parsing errors propagate.
		"""
		if self.reader is not None:
			raise RuntimeError('This CSV instance is already open')
		if mode not in ('rb', 'r', 'rt'):
			raise ValueError('mode must be rb, r, or rt')
		self.check_header(header)
		self.check_range(offset, limit)
		validator: Optional[HeaderValidator] = self.header_validator if header is None else header
		skip: int = self.offset if offset is None else offset
		remaining: Optional[int] = self.limit if limit is None else limit

		with ExitStack() as stack:
			if mode == 'rb':
				binary = stack.enter_context(open(path, 'rb'))
				text: TextIOWrapper = stack.enter_context(
					TextIOWrapper(
						binary,
						encoding=self.encoding,
						errors=self.errors,
						newline=self.newline,
					)
				)
			else:
				text = stack.enter_context(
					open(
						path,
						mode,
						encoding=self.encoding,
						errors=self.errors,
						newline=self.newline,
					)
				)
			self.reader = reader(
				text,
				delimiter=self.delimiter,
				escapechar=self.escapechar,
				strict=self.strict,
			)
			self.header_data = None
			self.mapping_header = None
			self.raw_data = None
			self.skip = skip
			self.remaining = remaining
			self.text = text
			try:
				if validator is not None:
					self.header_data = self.read_header(self.reader, validator)
					self.mapping_header = self.resolve_mapping_header(self.header_data)
				yield self
			finally:
				if self.text is text:
					self.close()
		return

	def close(self) -> None:
		"""
		Close the stream and invalidate its readers, header, raw record, and range.

		Repeated calls are safe. Stream closing errors propagate, and context
		exit also closes the stream automatically.
		"""
		text: Optional[TextIOWrapper] = self.text
		try:
			if text is not None:
				text.close()
		finally:
			self.text = None
			self.reader = None
			self.header_data = None
			self.mapping_header = None
			self.raw_data = None
			self.skip = 0
			self.remaining = None
		return

	def header(self) -> Optional[List[str]]:
		"""
		Return a copy of the validated header, or None without header validation.

		No record is consumed. The header is read and validated when open()
		applies a header Validator.
		"""
		if self.header_data is None:
			return None
		return self.header_data.copy()

	def raw(self) -> Optional[List[str]]:
		"""
		Return a copy of the last data record before row and column validation.

		The fields are decoded and CSV-parsed, not the original file text.
		Validation failures retain the record. A read attempt that produces no
		record (EOF, limit, parsing or decoding error) clears it. Header reads
		and offset records are excluded. Before reading, after close(), and
		on reopen, return None. Empty records return an empty list.
		"""
		if self.raw_data is None:
			return None
		return self.raw_data.copy()

	def __iter__(self) -> 'CSV[RecordType]':
		"""
		Return this CSV instance as its iterator.
		"""
		return self

	def __next__(self) -> RecordType:
		"""
		Return the next validated record, raising StopIteration at EOF or the read limit.

		Use inside an open context. Validation failures propagate after the
		record has been consumed; decoding and parsing errors also propagate.
		A Validator-raised StopIteration becomes RuntimeError.
		"""
		return next(self.rows())

	@overload
	def row(
		self: 'CSV[List[str]]',
		*,
		row: Optional[RowValidator] = None,
		column: Optional[
			Union[
				Dict[str, ColumnValidator],
				Tuple[ColumnValidator, ...],
			]
		] = None,
	) -> List[str]:
		...

	@overload
	def row(
		self: 'CSV[Mapping[str, str]]',
		*,
		row: Optional[RowValidator] = None,
		column: Optional[
			Union[
				Dict[str, ColumnValidator],
				Tuple[ColumnValidator, ...],
			]
		] = None,
	) -> Mapping[str, str]:
		...

	def row(
		self,
		*,
		row: Optional[RowValidator] = None,
		column: Optional[
			Union[
				Dict[str, ColumnValidator],
				Tuple[ColumnValidator, ...],
			]
		] = None,
	) -> RecordType:
		"""
		Consume and validate one record, raising StopIteration at EOF.

		StopIteration is also raised when the read range limit is reached.
		None uses the constructor setting. Overrides apply only to this call.
		Validation failures propagate after the record has been consumed.
		raw() retains the fields before validation, including on failure.
		"""
		source: 'Reader' = self.require_reader()
		row_validator, column_validators = self.resolve_validators(row, column)
		indices: List[Tuple[int, Union[int, str], ColumnValidator]] = self.column_indices(column_validators)
		record: List[str] = self.read_record(source)
		line: int = source.line_num
		record = self.validate(record, line, row_validator, indices)
		return self.return_record(record, line)

	@overload
	def rows(
		self: 'CSV[List[str]]',
		*,
		row: Optional[RowValidator] = None,
		column: Optional[
			Union[
				Dict[str, ColumnValidator],
				Tuple[ColumnValidator, ...],
			]
		] = None,
	) -> Generator[List[str], None, None]:
		...

	@overload
	def rows(
		self: 'CSV[Mapping[str, str]]',
		*,
		row: Optional[RowValidator] = None,
		column: Optional[
			Union[
				Dict[str, ColumnValidator],
				Tuple[ColumnValidator, ...],
			]
		] = None,
	) -> Generator[Mapping[str, str], None, None]:
		...

	def rows(
		self,
		*,
		row: Optional[RowValidator] = None,
		column: Optional[
			Union[
				Dict[str, ColumnValidator],
				Tuple[ColumnValidator, ...],
			]
		] = None,
	) -> Generator[RecordType, None, None]:
		"""
		Stream remaining records without accumulating results in memory.

		Records in the read range are shared with row() and stop at its limit.

		Overrides are captured when this method is called. The iterator must
		be consumed inside the open context and cannot be reused after the
		file is closed or reopened.

		Read raw() inside the loop for each record. Normal exhaustion clears
		it; a validation exception retains the failed record but terminates
		this generator. Use repeated row() calls to handle failures and continue.
		"""
		source: 'Reader' = self.require_reader()
		row_validator, column_validators = self.resolve_validators(row, column)
		indices: List[Tuple[int, Union[int, str], ColumnValidator]] = self.column_indices(column_validators)
		return self.iterate(source, row_validator, indices)

	def read_header(
		self,
		source: 'Reader',
		validator: HeaderValidator,
	) -> List[str]:
		try:
			record: List[str] = next(source)
		except StopIteration:
			raise HeaderError('The file has no record to use as a header', None) from None
		return list(validator(record))

	def resolve_mapping_header(
		self,
		header: List[str],
	) -> Tuple[str, ...]:
		if '' in header:
			raise HeaderError('Header names cannot be empty when row() and rows() return mappings', header)
		unique: set[str] = set()
		for name in header:
			if name in unique:
				raise HeaderError('Header names must be unique when row() and rows() return mappings', header)
			unique.add(name)
		return tuple(header)

	def read_record(
		self,
		source: 'Reader',
	) -> List[str]:
		"""
		Read the next record in the read range, raising StopIteration outside it.

		The limit is checked before skipping so that limit 0 reads nothing.
		Skipped records are not validated, and decoding or parsing errors
		propagate. A returned record counts toward the limit before validation.
		"""
		self.raw_data = None
		if self.remaining == 0:
			raise StopIteration
		while self.skip > 0:
			next(source)
			self.skip -= 1
		record: List[str] = next(source)
		self.raw_data = record.copy()
		if self.remaining is not None:
			self.remaining -= 1
		return record

	def require_reader(self) -> 'Reader':
		if self.reader is None:
			raise RuntimeError('Open the CSV file before reading records')
		return self.reader

	def check_header(
		self,
		header: Optional[HeaderValidator],
	) -> None:
		if header is not None and not isinstance(header, HeaderValidator):
			raise TypeError('header must be a header Validator or None')
		return

	def check_range(
		self,
		offset: Optional[int],
		limit: Optional[int],
	) -> None:
		for name, value in (
			(
				'offset',
				offset,
			),
			(
				'limit',
				limit,
			),
		):
			if value is None:
				continue
			if isinstance(value, bool) or not isinstance(value, int):
				raise TypeError('{} must be a non-negative integer or None'.format(name))
			if value < 0:
				raise ValueError('{} must be a non-negative integer or None'.format(name))
		return

	def check_validators(
		self,
		row: Optional[RowValidator],
		column: Optional[
			Union[
				Dict[str, ColumnValidator],
				Tuple[ColumnValidator, ...],
			]
		],
	) -> None:
		if row is not None and not isinstance(row, RowValidator):
			raise TypeError('row must be a row Validator or None')
		if column is not None:
			if isinstance(column, dict):
				for name, validator in column.items():
					if not isinstance(name, str):
						raise TypeError('Column names must be strings')
					if not isinstance(validator, ColumnValidator):
						raise TypeError('Column validators must be column Validator instances')
			elif isinstance(column, tuple):
				for validator in column:
					if not isinstance(validator, ColumnValidator):
						raise TypeError('Column validators must be column Validator instances')
			else:
				raise TypeError('column must be a dictionary, a tuple, or None')
		return

	def resolve_validators(
		self,
		row: Optional[RowValidator],
		column: Optional[
			Union[
				Dict[str, ColumnValidator],
				Tuple[ColumnValidator, ...],
			]
		],
	) -> Tuple[
		Optional[RowValidator], Optional[
			Union[
				Dict[str, ColumnValidator],
				Tuple[ColumnValidator, ...],
			]
		]
	]:
		self.check_validators(row, column)
		return (
			self.row_validator if row is None else row,
			self.column_validators if column is None else column,
		)

	def column_indices(
		self,
		column: Optional[
			Union[
				Dict[str, ColumnValidator],
				Tuple[ColumnValidator, ...],
			]
		],
	) -> List[Tuple[int, Union[int, str], ColumnValidator]]:
		if column is None:
			return []
		if isinstance(column, tuple):
			return [
				(
					index,
					index,
					validator,
				)
				for index, validator in enumerate(column)
			]
		if not column:
			return []
		if self.header_data is None:
			raise RuntimeError('Inject a header Validator before using named column validators')
		indices: List[Tuple[int, Union[int, str], ColumnValidator]] = []
		for name, validator in column.items():
			count: int = self.header_data.count(name)
			if count != 1:
				raise ValueError(
					'Column {!r} must occur exactly once in the header; found {}'.format(
						name,
						count,
					)
				)
			indices.append((
				self.header_data.index(name),
				name,
				validator,
			))
		return indices

	def validate(
		self,
		record: List[str],
		line: int,
		row: Optional[RowValidator],
		indices: List[Tuple[int, Union[int, str], ColumnValidator]],
	) -> List[str]:
		if row is not None:
			record = row(record, line)
		for index, column, validator in indices:
			if index >= len(record):
				raise RowError(
					'Column index {} is missing from a record with {} columns'.format(
						index,
						len(record),
					),
					line,
					record,
				)
			record[index] = validator(record[index], line, column)
		return record

	def return_record(
		self,
		record: List[str],
		line: int,
	) -> RecordType:
		header: Optional[Tuple[str, ...]] = self.mapping_header
		if header is None:
			return cast(RecordType, record)
		if len(record) != len(header):
			raise RowError(
				'Record has {} columns after validation but header has {}'.format(
					len(record),
					len(header),
				),
				line,
				record,
			)
		return cast(
			RecordType,
			{
				name: value
				for name, value in zip(header, record)
			},
		)

	def iterate(
		self,
		source: 'Reader',
		row: Optional[RowValidator],
		indices: List[Tuple[int, Union[int, str], ColumnValidator]],
	) -> Generator[RecordType, None, None]:
		while True:
			if self.reader is not source:
				raise RuntimeError('The CSV context has changed')
			try:
				record: List[str] = self.read_record(source)
				line: int = source.line_num
			except StopIteration:
				return
			record = self.validate(record, line, row, indices)
			yield self.return_record(record, line)
