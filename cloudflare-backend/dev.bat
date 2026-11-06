@echo off
chcp 65001 >nul
echo 正在啟動 Cloudflare Workers 本機測試伺服器...
node "%~dp0node_modules\wrangler\bin\wrangler.js" dev -c "%~dp0wrangler.jsonc" --port 8787
pause

