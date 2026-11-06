@echo off
echo Starting Cloudflare deploy...
node "%~dp0node_modules\wrangler\bin\wrangler.js" deploy -c "%~dp0wrangler.jsonc"
pause
