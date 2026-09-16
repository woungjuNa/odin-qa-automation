// Google Sheets에 붙여넣을 Apps Script 코드
// 사용법: 시트 메뉴 > 확장 프로그램 > Apps Script > 아래 코드로 교체 > 저장
// > 배포 > 배포 관리 > 수정(연필 아이콘) > 버전: 새 버전 > 배포

var HEADERS = ["실행 시각", "결과", "소요시간(초)", "실패 사유"];
var PASS_COLOR = "#dcfff1";
var FAIL_COLOR = "#ffedeb";

function doPost(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();

  if (sheet.getLastRow() === 0) {
    setupHeader(sheet);
  }

  var data = JSON.parse(e.postData.contents);
  var row = [data.timestamp, data.result, data.duration, data.error || ""];
  sheet.appendRow(row);

  var newRow = sheet.getLastRow();
  colorResultCell(sheet, newRow, data.result);

  return ContentService.createTextOutput(JSON.stringify({ status: "ok" }))
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
