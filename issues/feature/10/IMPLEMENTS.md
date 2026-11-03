# 구현 종합

## 결과

[요구사항 명세](./REQUIREMENTS.md)의 R1~R9를 구현했다.

- `csvd2c.header` 패키지에 `Validator`, `Pattern`, `Error(message, value)`와 헤더 Pattern 6개(`RejectEmpty`, `RejectDuplicate`, `Length`, `Includes`, `Exact`, `ExactOrder`)를 추가했다. 호출 계약은 `List[str] -> List[str]`이다.
- `CSV` 생성자와 `open()`이 `header`로 헤더 Validator를 받는다. `open()` 값은 그 파일에만 적용된다.
- 헤더 Validator가 있으면 `open()`이 첫 레코드를 헤더로 읽어 검증한다. 실패나 빈 파일이면 `csvd2c.header.Error`를 전파하고 파일을 닫는다.
- `header()`는 레코드를 읽지 않고 검증된 헤더의 복사본 또는 `None`을 반환한다. 이름 기반 열 매핑은 검증된 헤더를 사용한다.
- `cols`를 `column`으로 바꾸고, `row()`·`rows()`의 출력 `header` 인자와 dict 반환을 제거했다.

## 영향 범위

- 호환성 변경: `header()`의 레코드 소비, `cols` 인자, `row()`·`rows()`의 출력 `header` 인자를 쓰던 코드는 수정해야 한다. 호환 계층은 두지 않았다.
- 테스트·샘플·한국어/영어 매뉴얼·루트 README를 새 API로 갱신했다.

## 검증

일반 wheel 설치 환경에서 전체 테스트 147개가 통과했고, 신규 타입 진단은 없다. 상세 결과는 [구현 검증 기록](./tasks/1793691383142.md)을 따른다.

## 단계별 기록

- [헤더 검증기와 CSV API 변경 구현](./implements/1793691383141.md)
