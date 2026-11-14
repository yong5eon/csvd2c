# 헤더 Validator 사용 시 row()/rows() Mapping 반환 지원

## 변경 내용

- `header` Validator가 적용된 open 컨텍스트에서 `row()`·`rows()`·`next(csv)`가 `Mapping[str, str]`를 반환하도록 변경
- 행/열 검증은 기존 `List[str]` 기반 흐름을 유지하고, 검증 완료 후 매핑 변환하도록 분리
- 헤더 이름 중복/빈 문자열을 `open()` 단계에서 `HeaderError`로 거부
- 매핑 모드에서 검증 후 레코드 길이가 헤더 길이와 다르면 `RowError` 발생
- Generic/overload 타입 힌트를 추가해 헤더 지정 여부에 따른 정적 반환 타입 분기 제공

## 검증

- `python -m unittest tests.test_header tests.test_csv tests.test_column_patterns tests.test_encoding_recovery tests.test_error_context tests.test_range tests.test_raw tests.test_row_patterns -v`
- `python samples/read_dictionary.py`
- `python samples/custom_patterns.py`
- `python samples/reject_records.py`
- `python samples/row_padding.py`
- `python samples/column_recover_encoding.py`

## 호환성 영향

- 브레이킹 변경: 헤더 Validator 사용 시 `row()`·`rows()` 결과를 `List[str]`로 처리하던 호출 코드는 `Mapping[str, str]` 접근으로 수정 필요

## 관련 이슈 및 변경 로그

- Closes #14
- Changes: issues/feature/14/CHANGELOG.md
