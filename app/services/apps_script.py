from __future__ import annotations


def sinh_apps_script(webhook_url: str, secret: str) -> str:
    """Sinh Apps Script template để paste vào Google Sheet (Extensions → Apps Script)."""
    return f"""// === Kinkin PGH — Sheet → App webhook ===
// Dán toàn bộ file này vào: Sheet → Extensions → Apps Script (xoá nội dung cũ).
// Bước 1: Lưu (Ctrl+S).
// Bước 2: Chạy hàm `setupTrigger` 1 lần (chọn ở dropdown phía trên, bấm Run, cấp quyền).
// Sau đó mọi thay đổi trên sheet sẽ POST tới hệ thống Kinkin PGH gần như tức thì.

const WEBHOOK_URL = "{webhook_url}";
const WEBHOOK_SECRET = "{secret}";

function onChangeHandler(e) {{
  try {{
    const ss = e && e.source ? e.source : SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getActiveSheet();
    const payload = {{
      spreadsheetId: ss.getId(),
      spreadsheetName: ss.getName(),
      sheetName: sheet.getName(),
      changeType: (e && e.changeType) || "EDIT",
      user: (Session.getActiveUser().getEmail && Session.getActiveUser().getEmail()) || "",
      at: new Date().toISOString()
    }};
    UrlFetchApp.fetch(WEBHOOK_URL, {{
      method: 'post',
      contentType: 'application/json',
      headers: {{ 'X-Sheet-Secret': WEBHOOK_SECRET }},
      payload: JSON.stringify(payload),
      muteHttpExceptions: true,
      followRedirects: true
    }});
  }} catch (err) {{
    console.error("Webhook lỗi:", err);
  }}
}}

function setupTrigger() {{
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  ScriptApp.getProjectTriggers().forEach(t => {{
    if (t.getHandlerFunction() === 'onChangeHandler') ScriptApp.deleteTrigger(t);
  }});
  ScriptApp.newTrigger('onChangeHandler')
    .forSpreadsheet(ss)
    .onChange()
    .create();
  console.log("✓ Đã cài trigger onChange cho:", ss.getName());
}}

function testGuiThu() {{
  // Bấm Run hàm này để test ngay 1 lần (không cần đợi thay đổi sheet)
  onChangeHandler({{ source: SpreadsheetApp.getActiveSpreadsheet(), changeType: 'TEST' }});
  console.log("✓ Đã gửi test, kiểm tra log_api_vtp / sync history trong app.");
}}
"""
