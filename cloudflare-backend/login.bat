@echo off
chcp 65001 >nul
echo 正在啟動 Cloudflare 登入流程...
node "%~dp0node_modules\wrangler\bin\wrangler.js" login
pause

