# 작업 계획

1. `src/CSV.py`에 매핑 반환 모드 상태, 헤더 유효성 검사, 검증 후 매핑 변환, 길이 불일치 오류를 구현한다.
2. `CSV` 타입 힌트를 Generic/overload로 확장해 헤더 지정 여부에 따른 반환 타입을 표현한다.
3. `tests/test_csv.py`, `tests/test_header.py` 중심으로 반환값 기대를 갱신하고, 타입 overload 검증 테스트를 추가한다.
4. 매핑 반환 영향이 있는 기존 테스트(`test_range`, `test_raw`, `test_row_patterns`, `test_column_patterns`, `test_encoding_recovery`, `test_error_context`)를 최소 수정해 회귀를 맞춘다.
5. 샘플 코드와 README/docs(한/영)의 반환 형태 설명을 새 계약으로 동기화한다.
6. 변경 범위 대상 테스트와 샘플 실행으로 검증한다.
7. 고객용 변경 로그와 PR 문서(IR)에서 브레이킹 변경을 명시한다.
