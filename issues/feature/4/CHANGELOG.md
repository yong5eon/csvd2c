# 변경 로그

## 기능 추가

- `CSV` 생성자에서 `escapechar`를 설정할 수 있습니다. 기본값 `None`은 기존 동작을 유지하며, backslash로 escape된 인용부호가 있는 CSV·TSV는 `escapechar="\\"`로 읽을 수 있습니다. 파싱은 Python 표준 `csv.reader`를 사용합니다.
