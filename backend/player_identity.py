"""玩家識別：把暱稱轉成不可逆的雜湊鍵。

隱私權政策承諾不永久儲存玩家暱稱，但 `users` 表需要一個穩定的鍵，
才能讓同一個人跨場次累積統計數據。解法是只存暱稱的雜湊值 —— 查得到、
對得上，但資料庫裡不再有明文暱稱。

暱稱是低熵資料（多半是人名或常見詞），單純的 SHA-256 用字典檔就能反推，
因此改用帶 pepper 的 HMAC。pepper 存在環境變數，不進版控也不進資料庫，
拿到資料庫檔案的人沒有 pepper 就無法反推。

⚠️ pepper 一旦更換或遺失，既有統計就再也對不上（等同全體歸零）。
   正式環境請用 `flyctl secrets set PLAYER_NAME_PEPPER=...` 設定並妥善備份。
"""

import hashlib
import hmac
import os

_PEPPER = os.getenv("PLAYER_NAME_PEPPER", "")

if not _PEPPER:
    print(
        "[PlayerIdentity] WARNING: PLAYER_NAME_PEPPER 未設定，"
        "雜湊將不帶 pepper，可被字典攻擊反推。正式環境請設定此環境變數。"
    )


def player_key(player_name: str) -> str:
    """把暱稱轉成資料庫用的雜湊鍵（64 字元 hex）。

    不對輸入做正規化（不 strip、不轉小寫），以維持與原本
    `User.name == player_name` 完全一致的比對語意：
    「小明」與「小明 」在改動前後都視為不同玩家。
    """
    return hmac.new(
        _PEPPER.encode("utf-8"),
        player_name.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
