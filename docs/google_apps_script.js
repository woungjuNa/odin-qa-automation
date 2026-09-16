// Google Sheets에 붙여넣을 Apps Script 코드
// 사용법: 시트 메뉴 > 확장 프로그램 > Apps Script > 아래 코드로 교체 > 저장
// > 배포 > 배포 관리 > 수정(연필 아이콘) > 버전: 새 버전 > 배포

var HEADERS = ["실행 시각", "결과", "소요시간(초)", "실패 사유"];
var PASS_COLOR = "#dcfff1";
var FAIL_COLOR = "#ffedeb";

// 웹 앱 URL은 "모든 사용자" 접근으로 배포해야 스크립트에서 호출할 수 있어서, URL만 알면
// 누구나 행을 추가할 수 있다. 아무 문자열이나 넣고 sheets_config.py의 WEBHOOK_TOKEN에
// 같은 값을 넣으면, 토큰이 일치하는 요청만 기록한다. 비워두면 검사하지 않는다.
var TOKEN = "";

// 배포 URL을 브라우저로 열었을 때 배포가 살아있는지 확인하는 용도.
function doGet() {
  return jsonResponse({ status: "ok", message: "odin smoke test webhook is alive" });
}

function doPost(e) {
  var data = JSON.parse(e.postData.contents);
  if (TOKEN && data.token !== TOKEN) {
    return jsonResponse({ status: "error", message: "invalid token" });
  }

  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];

  if (sheet.getLastRow() === 0) {
    setupHeader(sheet);
  }

  var row = [data.timestamp, data.result, data.duration, data.error || ""];
  sheet.appendRow(row);

  var newRow = sheet.getLastRow();
  colorResultCell(sheet, newRow, data.result);

  // 실행 시각, 소요시간, 실패 사유는 가운데 맞춤
  sheet.getRange(newRow, 1).setHorizontalAlignment("center");
  sheet.getRange(newRow, 3).setHorizontalAlignment("center");
  sheet.getRange(newRow, 4).setHorizontalAlignment("center");

  return jsonResponse({ status: "ok" });
}

function jsonResponse(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function setupHeader(sheet) {
  var headerRange = sheet.getRange(1, 1, 1, HEADERS.length);
  headerRange.setValues([HEADERS]);
  headerRange.setFontWeight("bold");
  headerRange.setBackground("#0c66e4");
  headerRange.setFontColor("#ffffff");
  headerRange.setHorizontalAlignment("center");

  sheet.setFrozenRows(1);
  sheet.setColumnWidth(1, 160); // 실행 시각
  sheet.setColumnWidth(2, 80);  // 결과
  sheet.setColumnWidth(3, 110); // 소요시간
  sheet.setColumnWidth(4, 320); // 실패 사유
}

function colorResultCell(sheet, rowNum, result) {
  var cell = sheet.getRange(rowNum, 2);
  cell.setFontWeight("bold");
  cell.setHorizontalAlignment("center");
  cell.setBackground(result === "PASS" ? PASS_COLOR : FAIL_COLOR);
}
