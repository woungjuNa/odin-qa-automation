// Google Sheets에 붙여넣을 Apps Script 코드
// 사용법: 시트 메뉴 > 확장 프로그램 > Apps Script > 아래 코드로 교체 > 저장
// > 배포 > 새 배포 > 유형: 웹 앱 > 실행: 나 > 액세스 권한: 모든 사용자 > 배포
// > 생성된 웹 앱 URL을 복사해서 sheets_config.py의 WEBHOOK_URL에 붙여넣기

function doPost(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var data = JSON.parse(e.postData.contents);

  // 첫 실행이면 헤더 행 추가
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(["실행 시각", "결과", "소요시간(초)", "실패 사유"]);
  }

  sheet.appendRow([
    data.timestamp,
    data.result,
    data.duration,
    data.error || ""
  ]);

  return ContentService.createTextOutput(JSON.stringify({ status: "ok" }))
    .setMimeType(ContentService.MimeType.JSON);
}
