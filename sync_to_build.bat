@echo off
chcp 65001 >nul
echo 🔄 正在將最新程式碼同步到建置資料夾 (C:\FriendAndMe_Build)...
echo.

:: 使用 robocopy 進行鏡像同步 (MIR)
:: /XD 排除 .godot (編輯器暫存) 以及 android\build (Android 建置暫存)
:: /XF 排除已經匯出的 .apk 檔案
robocopy "C:\Friend&Me\friend&me" "C:\FriendAndMe_Build" /MIR /XD .godot android\build /XF *.apk /NDL /NJH /NJS /NP

echo.
echo ✅ 同步完成！
echo 👉 現在你可以開啟 Godot 並從 C:\FriendAndMe_Build 專案執行「匯出 Android」。
echo.
pause
