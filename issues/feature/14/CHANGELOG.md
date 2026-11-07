# 변경 로그

## 변경 사항

- `header` Validator가 적용된 읽기에서 `row()`·`rows()`·`next(csv)` 반환을 `Mapping[str, str]`로 변경
- 행/열 검증 이후 매핑 변환을 적용하고, 검증 후 헤더 길이 불일치를 `RowError`로 처리
- 헤더 이름 중복/빈 문자열을 `open()` 단계에서 `HeaderError`로 거부
- 반환 타입 분기를 Generic/overload로 제공하도록 타입 힌트 확장
- 매핑 반환 동작에 맞춰 테스트, 샘플, README, docs(한/영) 동기화

## 호환성

- 브레이킹 변경: 기존에 헤더 Validator를 사용하면서 `row()`·`rows()` 결과를 `List[str]`로 가정하던 코드는 `Mapping[str, str]`에 맞게 수정이 필요함
