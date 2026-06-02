// PM2 ecosystem cho local worker.
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
//   pm2 logs kinkin-cron-worker
//   pm2 monit
//
// Update sau khi sửa script:
//   pm2 reload kinkin-cron-worker
//
// Tắt:
//   pm2 stop kinkin-cron-worker
//   pm2 delete kinkin-cron-worker

module.exports = {
  apps: [
    {
      name: "kinkin-cron-worker",
      script: ".venv/Scripts/python.exe",
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
      out_file: "./logs/cron-worker.out.log",
      error_file: "./logs/cron-worker.err.log",
      merge_logs: true,
      time: true,
    },
  ],
};
