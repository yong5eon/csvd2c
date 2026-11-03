# 구현 종합

## 결과

[요구사항 명세](./REQUIREMENTS.md)의 R1~R6을 구현했다.

- 행 Pattern·Validator는 `__call__(value, row)`, 열 Pattern·Validator는 `__call__(value, row, column)`으로 위치를 받는다. `row`는 라인 번호다.
- CSV는 레코드를 읽은 직후의 `csv.reader.line_num`을 라인 번호로 전달한다. 튜플로 지정한 열은 0부터 시작하는 인덱스, 이름으로 지정한 열은 컬럼명을 전달한다. 열 검증은 행 검증으로 바뀐 행을 기준으로 한다.
- Error는 예외 클래스다. 공통 `csvd2c.Error(Exception)`를 행 Error `(message, row, value)`와 열 Error `(message, row, column, value)`가 상속한다. `value`는 실패한 Pattern의 입력값이다.
- 모든 Pattern의 `error=` 매개변수와 호출형 Error 처리기를 제거했다. 라이브러리 검증 Pattern은 데이터 실패 시 행·열 Error를 직접 발생시키고, 조건 Pattern은 중첩 예외를 그대로 전파한다.
- 생성자 설정 오류의 `TypeError`·`ValueError`, `TryRecoverEncoding`의 후보 실패 시 입력 유지, 정상 입력 반환값과 검증 순서는 유지했다.

## 영향 범위

- 호환성 변경: 한 인자 Pattern·Validator 직접 호출, `error=` 인자와 처리기 구현, 데이터 실패를 `except ValueError`로 처리하던 코드는 수정해야 한다.
- 테스트·샘플·한국어/영어 매뉴얼·루트 README를 새 계약으로 갱신했다.

## 검증

일반 wheel 설치 환경에서 전체 테스트 124개가 통과했고, 신규 타입 진단은 없다. 상세 결과는 [최종 검증 기록](./tasks/1793685462491.md)을 따른다.

## 단계별 기록

- [호출·샘플·사용자 안내 갱신](./implements/1793677881530.md): 초기 구현. Error를 호출형 처리기로 유지한 설계는 이후 정정했다.
- [Error를 예외 클래스로 정정하고 Pattern의 error= 제거](./implements/1793679516850.md)
- [호출 인자 이름을 value·row로 변경](./implements/1793680367003.md)
- [PR #8 리뷰 반영](./implements/1793685462490.md)
