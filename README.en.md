# csvd2c

[한국어](./README.md)

csvd2c stands for **CSV Dirty to Clean**, a Python library for streaming reads and cleansing of irregular CSV and TSV data. Use it to validate and transform row structures and column values with explicit rules during ETL (extract, transform, load).

[User guide](./docs/README.en.md) · [Runnable samples](./samples/README.en.md) · [Releases and changelog](https://github.com/yong5eon/csvd2c/releases)

## Features

- Streaming CSV/TSV reads: return list records one at a time with `next(csv)` or a loop
- Header validation: validate the first record as the header on `open()`, including empty, duplicate, listed, and ordered names
- Read range: select the records to read with `offset` and `limit` on the constructor and `open()`
- Raw record access: use `raw()` to get a copy of pre-validation fields and preserve rejected records
- Row cleansing: validate counts, insert, remove, reorder, merge, split, and check empty records or repeated headers
- Column cleansing: normalize whitespace and Unicode, validate and map values, and standardize dates, numbers, and currency prefixes
- Encoding handling: check candidates against an initial file sample and conditionally recover field bytes preserved by `surrogateescape`
- Composable rules: execute Patterns in order with a Validator and implement custom Patterns

## Installation

Requires Python 3.10 or later. The minimum was raised because Python 3.9's standard `csv.writer` does not correctly preserve escape characters within fields during CSV round trips.

```shell
pip install csvd2c
```

## Quick start

Create a UTF-8 file named `input.csv` in your execution directory:

```csv
name,date
 Example ,2026-01-10
 Sample ,2026-02-23
```

Read records incrementally, stripping company names and rejecting empty names:

```python
from csvd2c import CSV
from csvd2c.column import Validator
from csvd2c.column.patterns import (
  Required,
  Strip,
)
from csvd2c.header import Validator as HeaderValidator
from csvd2c.header.patterns import ExactOrder
from csvd2c.row import Validator as RowValidator
from csvd2c.row.patterns import Length

csv = CSV(
  encoding="utf-8",
  header=HeaderValidator(ExactOrder("name", "date")),
  row=RowValidator(Length(2)),
  column={"name": Validator(Strip(), Required())},
)

with csv.open("input.csv"):
  print(csv.header())
  for record in csv:
    print(record)
```

Expected output:

```text
['name', 'date']
['Example', '2026-01-10']
['Sample', '2026-02-23']
```

Because a header Validator is injected, `open()` reads the first record as the header and checks the `name,date` order. `header()` returns the validated header and the loop reads the remaining records. You can also read one record at a time with `next(csv)`. The named `name` column must appear exactly once in the header. Dates remain original strings because no Date Pattern is configured. For TSV, use `CSV(delimiter="\t")`.

## Usage rules

- With a header Validator in `header=`, `open()` reads and validates the first record as the header. Failure raises `csvd2c.header.Error` and closes the file. Without one, `open()` reads no record.
- `header()` reads no record and returns a copy of the validated header, or `None` without header validation.
- `raw()` returns a copy of the last data record's pre-validation fields. It returns `None` initially, after a read produces no record, and after closing. See [raw record access](./docs/README.en.md#raw-record-access) for update rules and a dump example.
- `next(csv)` and `row()` return the next record; `rows()` streams the remainder, all as lists. All three share the read position and constructor Validators. Without a header Validator, the first result of a file with a header is the header record.
- Row validation runs before column validation. Dictionary `column` uses names from the validated header; tuple `column` applies to the specified leading columns.
- Method-level `row=` and `column=` override settings for that call; `open()`'s `header=` applies only to that file. Omitted arguments or `None` retain constructor settings.
- `next(csv)` and `row()` raise `StopIteration` at EOF; `rows()` and a `for` loop end normally.
- `offset` and `limit` on the constructor and `open()` select the records read by `next(csv)`, `row()`, and `rows()`. Positions start at 0, and a header read by a header Validator is not counted. Records that fail validation count toward the limit; once it is reached, `next(csv)` and `row()` raise `StopIteration` and `rows()` ends.
- Calling `next(csv)` after `close()` or context exit raises `RuntimeError`. Reopening the same `CSV` instance starts at the new file's read position. A `rows()` generator created before closing cannot be reused.

See [header validation](./docs/README.en.md#header-validation) for header Patterns, renaming, and migration from previous usage, [read range](./docs/README.en.md#read-range) for range counting rules, and [detailed usage rules](./docs/README.en.md#usage-rules) for configuration constraints and complete behavior.

### Reading options and output

Constructor `field_size_limit=None` preserves the current standard CSV field limit. Specify an integer from `0` through the public `MAX_FIELD_SIZE` constant (`2_147_483_647`). Out-of-range settings raise `ValueError`, invalid types raise `TypeError`, and oversized input fields raise `csv.Error`. Changes affect other readers, are not restored on closing, and do not guarantee memory safety. See [field size limit](./docs/README.en.md#field-size-limit) for examples and constraints.

CSV defaults to `encoding="utf-8"`, `errors="strict"`, `newline=""`, `delimiter=","`, and `strict=True`. `open(path, mode="rb", header=None, offset=None, limit=None)` accepts only `rb`, `r`, and `rt`. Binary mode decodes through TextIOWrapper; text modes use the same encoding, errors, and newline settings. Write, append, and update modes are rejected before opening.

`next(csv)`, `row()`, and `rows()` always return list records. Combine them with the validated header when you need dictionaries.

```python
from csvd2c import CSV
from csvd2c.header import Validator as HeaderValidator

with CSV(header=HeaderValidator()).open("input.csv") as csv:
  header = csv.header() or []
  for record in csv.rows():
    print(dict(zip(header, record)))
```

Missing or duplicate selected `column` names are errors. Tuple settings validate only the specified leading columns. Pass method-level `column={}` or `column=()` to disable constructor column settings.

`close()` clears the stream, header, and reading state and is safe to repeat. `rows()` selects validators and header mapping at call time. Closing or reopening invalidates existing generators.

## Row structure Patterns

Import from `csvd2c.row.patterns`. Row Patterns accept and return `list[str]`. Transformations create new lists; validation-only Patterns preserve the input on success.

| Pattern | Behavior |
| --- | --- |
| `Length(count)` | Require exactly count columns |
| `Insert(index, value)` | Insert using Python list.insert semantics |
| `Remove(index)` | Remove one column, supporting negative indices |
| `Reorder(*indices)` | Specify every column exactly once |
| `Slice(start=None, stop=None, step=None)` | Python slicing; reject zero step |
| `Truncate(count)` | Remove trailing excess columns |
| `Pad(count, value="")` | Fill only missing trailing columns |
| `Merge(start, stop, sep=",")` | Merge a contiguous slice with exclusive stop |
| `Split(index, sep=",", maxsplit=-1)` | Split one field using str.split |
| `Replace(index, value)` | Replace one column explicitly |
| `IfLength(count, *patterns)` | Apply nested rules only for matching counts |
| `RejectEmpty()` | Reject empty records or all-empty-string records |
| `RejectHeader(*names)` | Reject exact header repetitions |

If the provider confirms that an unquoted comma splits its address into two columns, apply an explicit structural rule:

```python
from csvd2c.row import Validator
from csvd2c.row.patterns import (
  IfLength,
  Length,
  Merge,
)

validator = Validator(
  IfLength(4, Merge(1, 3, sep=",")),
  Length(3),
)
result: list[str] = validator([
  "Example",
  "Seoul",
  "Gangnam",
  "2026-01-10",
], 1)
assert result == ["Example", "Seoul,Gangnam", "2026-01-10"]
```

IfLength preserves nonmatching rows. Merge rejects empty or out-of-range slices; positions are never inferred.

For confirmed trailing-only excess or missing columns, compose `Validator(Truncate(2), Pad(2), Length(2))`. This does not repair missing middle columns. Truncate discards values from the result, so preserve originals separately. RejectEmpty does not treat whitespace-only strings as empty.

## Column Patterns

Import from `csvd2c.column.patterns`. Inputs and outputs are strings, including normalized dates and numbers, not date objects or floats.

| Pattern | Behavior |
| --- | --- |
| `Strip`, `CollapseWhitespace` | Trim boundaries or collapse whitespace runs |
| `Replace`, `RegexReplace` | Literal and regex substitution |
| `Lower`, `Upper`, `CaseFold` | Case transformations |
| `UnicodeNormalize` | NFC, NFD, NFKC, or NFKD normalization |
| `Required`, `Length`, `Regex`, `Choices` | Required values, code point length, fullmatch, allowed values |
| `RejectCharacters` | Reject specified characters |
| `RejectSurrogates`, `RejectReplacementCharacter` | Check surrogate code points and U+FFFD |
| `Map`, `Default` | Exact string mapping or explicit empty-string default |
| `Date` | Validate complete dates and normalize output |
| `Number`, `Range` | Normalize numeric text and check inclusive bounds |
| `Currency` | Convert currency prefixes to ISO 4217 codes |
| `Recode` | Reverse a confirmed misdecoding path |
| `IfEmpty`, `IfMatch`, `IfUndecodable` | Apply nested rules only on matching conditions |
| `RecoverEncoding`, `TryRecoverEncoding` | Recover preserved field bytes using known or candidate codecs |

### Dates and numbers

```python
from csvd2c.column import Validator
from csvd2c.column.patterns import (
  Date,
  Number,
  Range,
  Strip,
)

date = Validator(Strip(), Date("%Y-%m-%d", "%d/%m/%Y"))
amount = Validator(
  Strip(),
  Number(thousands=","),
  Range(minimum=0, maximum=1000000),
)
assert date(" 29/02/2024 ", 1, "date") == "2024-02-29"
assert amount(" 1,234.500 ", 1, "amount") == "1234.5"
```

- Date requires a year, month, and day. It does not infer years for values such as `1-10` or `Feb-23`. Distinct interpretations across formats are errors.
- Text month names `%b` and `%B` depend on the process locale. The library does not change it.
- `Number(decimal=".", thousands=None)` never guesses separators. It checks three-digit grouping and rejects `.5`, `1.`, exponents, NaN, Infinity, and surrounding whitespace.
- Number removes trailing fractional zeros without float rounding and normalizes negative zero to `0`.
- Range supports finite Decimal, integer, or numeric-string bounds, not floats or dates. Normalize grouped values with Number first.

### Currencies

```python
from csvd2c.column.patterns import (
  CURRENCY_ALIASES,
  CURRENCY_CODES,
  Currency,
  Number,
)

currency = Currency({"VN$": "VND"})
assert currency("CA$1,000", 1, "amount") == "CAD 1,000"
code, amount = currency("VN$ 10,000,000", 1, "amount").split(" ", 1)
assert code == "VND"
assert Number(thousands=",")(amount, 1, "amount") == "10000000"
assert "VND" in CURRENCY_CODES
assert CURRENCY_ALIASES["VND"] == "VND"
```

Currency uses bundled ISO 4217 codes and CLDR multilingual names and symbols without runtime network access. CURRENCY_CODES and CURRENCY_ALIASES are read-only. Sources and notices are described in the [detailed guide](./docs/README.en.md#important-constraints).

Bare `$` means USD and bare `¥` means JPY by explicit policy. Override aliases when the provider confirms different meanings. Custom mappings are copied and cannot redirect ISO codes themselves. Add VN$ as above only when the provider confirms VND.

Only the prefix is converted; amount formatting is preserved. Currency does not validate numeric syntax and rejects missing or damaged amounts. Do not pass its entire output to Number. For intervals such as `VN$ amount - VN$ amount`, split endpoints as in the [interval sample](./samples/column_currency_interval.py).

### Encoding recovery

For a uniformly encoded file, check candidates with `detect_encoding("input.csv", "utf-8-sig", "cp949")` and read using the selected codec. BOMs do not automatically take precedence. Missing candidates, empty input, and failure of all candidates are errors.

Use `errors="surrogateescape"` to preserve bytes that fail UTF-8 decoding. Recover those fields with explicit candidate codecs:

```python
from csvd2c.column import Validator
from csvd2c.column.patterns import (
  RejectReplacementCharacter,
  RejectSurrogates,
  TryRecoverEncoding,
)

validator = Validator(
  TryRecoverEncoding("ascii"),
  TryRecoverEncoding("cp949"),
  RejectSurrogates(),
  RejectReplacementCharacter(),
)
raw: bytes = "홍길동".encode("cp949")
preserved: str = raw.decode("utf-8", errors="surrogateescape")
assert validator(preserved, 1, "name") == "홍길동"
```

TryRecoverEncoding tries only values with U+DC80 through U+DCFF markers. Failure preserves input for the next candidate; successful results without markers are left unchanged by later candidates. ASCII fails in this example, allowing cp949 to handle it. Choose real candidates in provider-defined order. A permissive codec such as cp1258 can succeed even when it is incorrect.

When the original encoding is known, use `IfUndecodable(RecoverEncoding("cp1258"))`. RecoverEncoding reports failures as errors; TryRecoverEncoding preserves originals only on codec failure. Apply recovery before stripping, replacement, or Unicode normalization.

Results are Unicode str, not UTF-8 bytes; encode at output. Already replaced characters, mixed encodings inside a field, or information removed by BOM/newline processing are not automatically restored. `Recode(stored_encoding, original_encoding)` is a separate strict encode/decode rule for reversing a confirmed misdecoding path.

## Custom rules and error handling

Row Pattern and Validator use `__call__(value: List[str], row: int) -> List[str]`; column implementations use `__call__(value: str, row: int, column: Union[int, str]) -> str`. Direct calls and existing custom Patterns must supply the new position arguments. CSV supplies them automatically for injected Validators. A line is the record's final physical line; a column identifier is a numeric index or configured name.

Validation failures raise `csvd2c.row.Error(message, row, value)` or `csvd2c.column.Error(message, row, column, value)`, both subclasses of `csvd2c.Error(Exception)`. `value` is the failing Pattern's input: a failure after `Strip → Required` carries `""`, not the earlier whitespace. The per-Pattern `error=` arguments have been removed, and data failures are no longer `ValueError`; handle them with `try`/`except`. Configuration errors remain immediate `TypeError` or `ValueError`. See [validation positions and error contracts](./docs/README.en.md#validation-positions-and-error-contracts) for migration.

See complete [custom Pattern](./samples/custom_patterns.py) and [error handling](./samples/custom_errors.py) examples. To log and continue, inject Validators directly into CSV, catch validation errors, and call `next(csv)` again as in the [rejection sample](./samples/reject_records.py). The same `rows()` generator cannot resume after an exception. Do not guess record boundaries and continue after parsing or decoding failures.

## Important constraints

- Decoding defaults to `errors="strict"`. Decoding, parsing, and validation errors propagate; records are not skipped automatically.
- `detect_encoding()` checks an initial sample of up to 1MiB in candidate order. The first success guarantees neither the actual encoding nor whole-file validity.
- `TryRecoverEncoding` does not detect languages either. It uses the first successful candidate decoding and cannot restore information already replaced by `�`.
- Do not collect the entire file in a list. Record and batch sizes also affect memory usage. Performance on actual 200GB files has not been validated.
- CSV is currently read-only. Callers implement output storage and rejection logging.

## Guide and samples

The [user guide](./docs/README.en.md) describes usage rules, row/column Patterns, and error handling in detail.

The [samples index](./samples/README.en.md) provides 22 standalone scripts with English code explanations. Small synthetic inputs demonstrate CSV/TSV reads, dates, numbers, currencies, encoding recovery, custom rules, rejection logging, streaming export, and bounded batches with result checks.

## License

Distributed under the [GNU General Public License v3.0](./LICENSE). Unicode-3.0 notices for the included currency alias data are retained in [CurrencyData.py](./src/column/patterns/CurrencyData.py).
