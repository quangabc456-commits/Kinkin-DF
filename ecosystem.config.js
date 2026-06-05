// PM2 ecosystem cho local worker của project Kinkin-DF.
//
// Tên PM2 process: kkdf-cron (đặt riêng để phân biệt với worker của project
// Kinkinwarehouse — `kk-cron-local` — đang chạy cùng máy).
//
// Cài PM2 1 lần:
//   npm i -g pm2 pm2-windows-startup
//   pm2-startup install
//
// Khởi động worker:
//   pm2 start ecosystem.config.js
//   pm2 save
//
// Theo dõi:
//   pm2 status
//   pm2 logs kkdf-cron
//   pm2 monit
//
// Update sau khi sửa script:
//   pm2 reload kkdf-cron
//
// Tắt:
//   pm2 stop kkdf-cron
//   pm2 delete kkdf-cron
//
// Migrate từ tên cũ (kinkin-cron-worker):
//   pm2 delete kinkin-cron-worker
//   pm2 start ecosystem.config.js
//   pm2 save

module.exports = {
  apps: [
    {
      // Web dev server (uvicorn --reload) chạy ngầm qua PM2.
      // ⚠️ DÙNG python.exe (KHÔNG pythonw.exe) vì uvicorn --reload reloader
      //    cần IPC stdin/stdout với subprocess server — pythonw.exe không có
      //    handle stdio → subprocess chết im lặng, server không bao giờ lên.
      // PM2 spawn process với `windowsHide: true` mặc định → KHÔNG có cửa sổ
      // console nào hiện ra dù dùng python.exe. Log đẩy ra ./logs/kkdf-web.*.log.
      // Reload giới hạn trong thư mục `app/` để tránh restart vô tận khi
      // worker/IDE ghi file khác.
      name: "kkdf-web",
      script: ".venv/Scripts/python.exe",
      args: "-m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir app",
      cwd: __dirname,
      interpreter: "none",
      autorestart: true,
      windowsHide: true,
      max_memory_restart: "512M",
      env: {
        PYTHONIOENCODING: "utf-8",
        PYTHONUNBUFFERED: "1",
      },
      out_file: "./logs/kkdf-web.out.log",
      error_file: "./logs/kkdf-web.err.log",
      merge_logs: true,
      time: true,
    },
    {
      name: "kkdf-cron",
      // pythonw.exe = Python KHÔNG cửa sổ console → tránh bật terminal mỗi 5'
      // (cron_restart spawn lại process; python.exe là console app nên nhảy cửa sổ).
      script: ".venv/Scripts/pythonw.exe",
      args: "-m app.workers.cron_worker",
      cwd: __dirname,
      interpreter: "none",
      autorestart: false,
      cron_restart: "*/5 * * * *",
      max_memory_restart: "512M",
      env: {
        PYTHONIOENCODING: "utf-8",
        PYTHONUNBUFFERED: "1",
      },
      out_file: "./logs/kkdf-cron.out.log",
      error_file: "./logs/kkdf-cron.err.log",
      merge_logs: true,
      time: true,
    },
    {
      // Kéo dữ liệu tra cứu (khách hàng / địa chỉ / địa danh / kho) về DB mỗi 10'
      // → màn hình tạo phiếu đọc thẳng từ DB (tức thì), không phải gọi API chờ lâu.
      name: "kkdf-sync",
      script: ".venv/Scripts/pythonw.exe",
      args: "-m app.cli.sync_kho_den --all",
      cwd: __dirname,
      interpreter: "none",
      autorestart: false,
      cron_restart: "*/10 * * * *",
      max_memory_restart: "512M",
      env: {
        PYTHONIOENCODING: "utf-8",
        PYTHONUNBUFFERED: "1",
      },
      out_file: "./logs/kkdf-sync.out.log",
      error_file: "./logs/kkdf-sync.err.log",
      merge_logs: true,
      time: true,
    },
  ],
};
