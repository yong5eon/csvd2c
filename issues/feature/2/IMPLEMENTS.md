# 구현 종합

## 결과

[R1~R3](./REQUIREMENTS.md)에 따라 [CSV](../../src/CSV.py)의 `__iter__()`가 같은 인스턴스를 반환하고 `__next__()`가 `next(self.rows())`로 다음 검증 레코드를 반환하도록 했다. 기존 `rows()`의 `read_record()`·Validator 흐름을 사용하므로 `row()`·`rows()`·iterator가 동일한 reader, offset 및 limit을 공유한다. generator 동작 재사용으로 EOF의 `StopIteration`과 Validator에서 발생한 `StopIteration`의 `RuntimeError` 처리를 일치시킨다.

닫힌 파일에서 `next(csv)`는 기존 읽기 호출과 같이 `RuntimeError`를 발생시킨다. 다시 열린 인스턴스는 `open()`이 설정한 새 reader를 사용한다. 행·컬럼 검증 실패는 레코드를 소비한 뒤 전파하며 후속 호출에서 이어 읽는다. 디코딩·파싱 오류 이후 재개 보장은 추가하지 않았다.

## 변경 및 검증

- [구현 세부 기록](./implements/1794065037626.md): API, 테스트와 문서 변경
- [작업·검증 기록](./TASKS.md): 실제 테스트 명령과 범위
- 기존 `row()`·`rows()` 사용법과 이름은 변경하지 않았다.
