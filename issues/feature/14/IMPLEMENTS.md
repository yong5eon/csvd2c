# 구현 종합

## 핵심 변경

- `CSV`를 Generic으로 선언하고 `__init__`, `open`, `row`, `rows`에 overload를 추가해 헤더 지정 여부에 따른 반환 타입을 구분했습니다.
- `open()`에서 헤더 Validator가 적용되면 매핑 모드를 고정하고, 헤더 이름 중복/빈 문자열을 `HeaderError`로 즉시 거부하도록 했습니다.
- 행/열 검증 후 `return_record()`에서 매핑 변환을 수행하도록 분리했습니다.
- 매핑 모드에서 검증 후 레코드 길이와 헤더 길이가 다르면 `RowError`를 발생시키고 `RowError.value`는 `List[str]`를 유지했습니다.

## 변경 파일

- `src/CSV.py`
- `tests/test_csv.py`
- `tests/test_header.py`
- `tests/test_column_patterns.py`
- `tests/test_encoding_recovery.py`
- `tests/test_error_context.py`
- `tests/test_range.py`
- `tests/test_raw.py`
- `tests/test_row_patterns.py`
- `samples/read_dictionary.py`
- `samples/custom_patterns.py`
- `samples/reject_records.py`
- `samples/row_padding.py`
- `samples/column_recover_encoding.py`

## 단계별 구현 기록

- [implements/1794071535691.md](./implements/1794071535691.md)
