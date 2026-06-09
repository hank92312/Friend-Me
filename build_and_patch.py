import subprocess
import os
import sys
import time

def main():
    # 打包時版本號：同一版本所有使用者共用相同 URL，CDN 可快取；新部署才更新版本。
    # 不能在瀏覽器端用 Date.now()（每次載入都是新 URL → 瀏覽器快取/CDN 快取全無效
    # → 多人同時進入時每人各自重下 47MB → 慢）。
    build_ver = str(int(time.time()))
    print(f"[Build] Version string: {build_ver}")

    godot_path = r"C:\Users\hank9\Downloads\Godot_v4.6.2-stable_win64.exe\Godot_v4.6.2-stable_win64_console.exe"
    project_path = r"C:\FriendAndMe\friendAndme"
    export_output = r"C:\FriendAndMe\build_web_temp\index.html"
    
    # 確保臨時輸出目錄存在
    os.makedirs(os.path.dirname(export_output), exist_ok=True)
    
    print("=== Step 1: Running Godot Web Export ===")
    cmd = [
        godot_path,
        "--path", project_path,
        "--export-release", "Web", export_output
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:")
    print(result.stdout)
    print("STDERR:")
    print(result.stderr)
    
    if not os.path.exists(export_output):
        print("Error: Export failed, index.html not found.")
        sys.exit(1)
        
    print("=== Step 2: Patching index.html for Cache-Busting ===")
    with open(export_output, 'r', encoding='utf-8') as f:
        html = f.read()
        
    # 定義要插入的 fetch 攔截器與 WebGL 2.0 檢測器
    patch_code = """<style>
			/* 行動端輸入與長按優化補丁 */
			input, textarea {
				-webkit-user-select: text !important;
				user-select: text !important;
				touch-action: auto !important;
				pointer-events: auto !important;
			}
		</style>
		<script>
			(function() {
				function patchInputs() {
					const inputs = document.querySelectorAll('input, textarea');
					inputs.forEach(input => {
						if (input.dataset.patched) return;
						input.dataset.patched = "true";
						
						input.style.setProperty('user-select', 'text', 'important');
						input.style.setProperty('-webkit-user-select', 'text', 'important');
						input.style.setProperty('pointer-events', 'auto', 'important');
						
						input.addEventListener('focus', function() {
							console.log("[Input Patch] Input focused:", input);
							// 將 Godot 建立的 HTML 輸入框改為「可見」並固定在螢幕頂端（鍵盤上方），
							// 做成符合遊戲深色風格的輸入列，讓使用者打字時看得到自己輸入的內容，
							// 解決手機虛擬鍵盤遮擋 Godot 文字框、導致盲打的問題。
							input.style.setProperty('opacity', '1', 'important');
							input.style.setProperty('z-index', '99999', 'important');
							input.style.setProperty('position', 'fixed', 'important');
							input.style.setProperty('top', 'env(safe-area-inset-top, 0px)', 'important');
							input.style.setProperty('left', '0', 'important');
							input.style.setProperty('right', '0', 'important');
							input.style.setProperty('width', '100%', 'important');
							input.style.setProperty('height', '58px', 'important');
							input.style.setProperty('box-sizing', 'border-box', 'important');
							input.style.setProperty('margin', '0', 'important');
							input.style.setProperty('padding', '10px 18px', 'important');
							input.style.setProperty('font-size', '22px', 'important');
							input.style.setProperty('font-family', "system-ui, -apple-system, sans-serif", 'important');
							input.style.setProperty('color', '#FFF2CC', 'important');
							input.style.setProperty('background', '#1F1C1A', 'important');
							input.style.setProperty('border', 'none', 'important');
							input.style.setProperty('border-bottom', '3px solid #D0813C', 'important');
							input.style.setProperty('border-radius', '0', 'important');
							input.style.setProperty('outline', 'none', 'important');
							input.style.setProperty('caret-color', '#D0813C', 'important');
							input.style.setProperty('box-shadow', '0 6px 16px rgba(0,0,0,0.5)', 'important');
							// 輸入框需可接收觸控，這樣使用者能點文字中間移動游標、編輯內容。
							// （按鈕被覆蓋層擋住的問題改由下方 visualViewport 在鍵盤收合時主動隱藏輸入框來解決。）
							input.style.setProperty('pointer-events', 'auto', 'important');
						});
						
						input.addEventListener('blur', function() {
							input.style.setProperty('z-index', '-1', 'important');
							input.style.setProperty('opacity', '0', 'important');
							input.style.setProperty('pointer-events', 'none', 'important');
							input.style.setProperty('top', '-1000px', 'important');
						});
					});
				}
				setInterval(patchInputs, 500);

				// 鍵盤收合偵測（狀態機，修正先前「秒關鍵盤」誤判）：
				// 只有當視窗高度「確實掉超過 150px」（代表鍵盤真的開過）之後，
				// 才在高度回升到接近全高時主動 blur，讓 Godot focus_exited 執行、
				// 隱藏輸入框，避免覆蓋層擋住按鈕。鍵盤開啟動畫期間不會誤觸發。
				if (window.visualViewport) {
					var vv = window.visualViewport;
					var fmFullH = vv.height;
					var fmKbWasOpen = false;
					vv.addEventListener('resize', function() {
						var h = vv.height;
						if (h > fmFullH) fmFullH = h;
						if (h < fmFullH - 150) {
							fmKbWasOpen = true;            // 鍵盤已開啟
						} else if (fmKbWasOpen && h >= fmFullH - 60) {
							fmKbWasOpen = false;           // 鍵盤已收合
							var ae = document.activeElement;
							if (ae && (ae.tagName === 'INPUT' || ae.tagName === 'TEXTAREA')) {
								ae.blur();
							}
						}
					});
				}
			})();
		</script>
		<script>
			// WebGL context lost 自動恢復：低記憶體 iOS 裝置（如 iPad 第9代）GPU 吃緊時會丟棄 WebGL context，
			// 造成「WebGL context lost」死當。偵測到時自動重新載入（最多 2 次以避免無限循環），
			// 多數情況重載後 GPU 已釋出即可順利進入；搭配 sessionStorage 的 fm_launched 會直接重啟遊戲。
			(function() {
				function attachGLGuard(canvas) {
					if (!canvas || canvas.dataset.glLossPatched) return;
					canvas.dataset.glLossPatched = "1";
					canvas.addEventListener("webglcontextlost", function(e) {
						var n = parseInt(sessionStorage.getItem("fm_gl_reloads") || "0", 10);
						if (n < 2) {
							sessionStorage.setItem("fm_gl_reloads", String(n + 1));
							console.warn("[WebGL] context lost, auto-reloading (" + (n + 1) + "/2)...");
							setTimeout(function() { window.location.reload(); }, 300);
						} else {
							console.error("[WebGL] context lost again after retries; showing default error.");
						}
					}, false);
				}
				var glIv = setInterval(function() {
					var c = document.getElementById("canvas");
					if (c) { attachGLGuard(c); }
				}, 500);
				// 成功穩定執行 15 秒後清除重試計數，讓日後若再發生 context lost 仍有完整重試額度
				window.addEventListener("load", function() {
					setTimeout(function() { try { sessionStorage.removeItem("fm_gl_reloads"); } catch (e) {} }, 15000);
				});
			})();
		</script>
		<script>
			// 攔截 fetch 以強行對 Godot 的資源請求（如 .wasm 和 .pck 檔案）進行 Cache-Busting
			(function() {
				const originalFetch = window.fetch;
				window.fetch = function (input, init) {
					let url = (typeof input === 'string') ? input : input.url;
					if (url.endsWith('.wasm') || url.endsWith('.pck') || url.indexOf('.wasm?') !== -1 || url.indexOf('.pck?') !== -1) {
						if (url.indexOf('v=') === -1) {
							const separator = url.indexOf('?') !== -1 ? '&' : '?';
							url = url + separator + 'v=__BUILD_VER__';
						}
					}
					if (typeof input === 'string') {
						input = url;
					} else {
						input = new Request(url, input);
					}
					return originalFetch(input, init);
				};
			})();
		</script>
		<script>
			// 全局剪貼簿貼上支援（含 Prompt 備用方案）
			window.requestClipboard = function() {
				if (navigator.clipboard && navigator.clipboard.readText) {
					navigator.clipboard.readText().then(function(text) {
						if (window.godot_on_web_paste_received) {
							window.godot_on_web_paste_received(text);
						}
					}).catch(function(err) {
						console.warn("Clipboard API failed, using prompt fallback:", err);
						var text = prompt("請貼上複製的文字 (Paste text):", "");
						if (text !== null && window.godot_on_web_paste_received) {
							window.godot_on_web_paste_received(text);
						}
					});
				} else {
					var text = prompt("請貼上複製的文字 (Paste text):", "");
					if (text !== null && window.godot_on_web_paste_received) {
						window.godot_on_web_paste_received(text);
					}
				}
			};
		</script>
		<script>
			// WebGL 2.0 相容性檢測與阻斷
			window.hasWebGL2 = (function() {
				try {
					var canvas = document.createElement('canvas');
					return !!(window.WebGL2RenderingContext && canvas.getContext('webgl2'));
				} catch (e) {
					return false;
				}
			})();
			
			if (window.hasWebGL2) {
				document.write('<script src="index.js?v=__BUILD_VER__"><\\/script>');
			} else {
				console.error("WebGL 2.0 is not supported or disabled on this device/browser.");
				window.addEventListener('DOMContentLoaded', function() {
					// 隱藏原本的 status 載入區
					var statusDiv = document.getElementById('status');
					if (statusDiv) statusDiv.style.display = 'none';
					
					// 建立精美的 WebGL2 錯誤提示畫面
					var errDiv = document.createElement('div');
					errDiv.id = 'webgl2-error-overlay';
					errDiv.innerHTML = `
						<div class="err-card">
							<h2>⚠️ 瀏覽器未啟用 WebGL 2.0</h2>
							<p class="subtitle">WebGL 2.0 Disabled / Unsupported</p>
							<div class="desc-box">
								<p>您的裝置或瀏覽器目前未開啟 <strong>WebGL 2.0</strong> 繪圖功能，導致遊戲無法順利載入。這在蘋果 iOS / iPadOS Safari 瀏覽器上非常常見。</p>
								<hr/>
								<h3>🛠️ 解決步驟引導：</h3>
								<ul>
									<li><strong>開啟系統 WebGL 2.0 (iOS 15 以前)</strong>：請前往您 iPad/iPhone 的「設定」➔「Safari」➔「進階」➔「Experimental Features」，尋找並將 <strong>WebGL 2.0</strong> 開啟。</li>
									<li><strong>檢查記憶體，關閉多餘分頁</strong>：Safari 會因為記憶體過高而拒絕提供繪圖環境。請關閉其他所有瀏覽器分頁，並「重新整理」此頁面。</li>
									<li><strong>關閉「低耗電模式」</strong>：部分裝置在低耗電模式下會停用 WebGL，請關閉省電模式後重試。</li>
									<li><strong>更新系統或更換設備</strong>：建議將 iOS 系統更新至最新版本，或嘗試使用電腦版 Chrome / Firefox 瀏覽器進行遊玩。</li>
								</ul>
							</div>
							<button class="retry-btn" onclick="window.location.reload()">重新整理 ➔</button>
						</div>
					`;
					
					// 注入 CSS
					var style = document.createElement('style');
					style.innerHTML = `
						#webgl2-error-overlay {
							position: fixed;
							top: 0;
							left: 0;
							width: 100%;
							height: 100%;
							background: #161413;
							display: flex;
							justify-content: center;
							align-items: center;
							z-index: 100000;
							font-family: system-ui, -apple-system, sans-serif;
							color: #FFF2CC;
							padding: 20px;
							box-sizing: border-box;
							overflow-y: auto;
						}
						.err-card {
							width: 95%;
							max-width: 500px;
							background: #1F1C1A;
							border: 2px solid #D0813C;
							border-radius: 24px;
							padding: 25px;
							box-sizing: border-box;
							box-shadow: 0 16px 40px rgba(0,0,0,0.6);
							text-align: left;
						}
						.err-card h2 {
							color: #E39450;
							margin-top: 0;
							margin-bottom: 5px;
							font-size: 1.5rem;
							text-align: center;
						}
						.err-card .subtitle {
							color: #7C6858;
							font-size: 0.9rem;
							margin-top: 0;
							margin-bottom: 20px;
							text-align: center;
							font-weight: bold;
						}
						.desc-box {
							font-size: 0.95rem;
							line-height: 1.5;
							color: #E0E0E0;
						}
						.desc-box hr {
							border: 0;
							border-top: 1px dashed rgba(208, 129, 60, 0.3);
							margin: 15px 0;
						}
						.desc-box h3 {
							color: #FFF2CC;
							font-size: 1.05rem;
							margin-bottom: 10px;
						}
						.desc-box ul {
							padding-left: 20px;
							margin: 0;
						}
						.desc-box li {
							margin-bottom: 12px;
						}
						.retry-btn {
							background: #D0813C;
							color: #1F1C1A;
							border: none;
							padding: 12px 20px;
							font-size: 1.05rem;
							border-radius: 40px;
							cursor: pointer;
							width: 100%;
							margin-top: 20px;
							font-weight: bold;
							transition: all 0.2s ease;
							box-shadow: 0 4px 10px rgba(0,0,0,0.3);
						}
						.retry-btn:hover {
							background: #E39450;
							box-shadow: 0 6px 15px rgba(227, 148, 80, 0.4);
						}
					`;
					document.head.appendChild(style);
					document.body.appendChild(errDiv);
				});
			}
		</script>"""

    # 將打包時版本號注入 patch_code（取代佔位符），確保同一版本所有人 URL 相同
    patch_code = patch_code.replace('__BUILD_VER__', build_ver)

    # 替換 <script src="index.js"></script>
    target = '<script src="index.js"></script>'
    if target in html:
        html = html.replace(target, patch_code)
        print("Successfully replaced <script src=\"index.js\"></script> with cache-busting and WebGL2 check script.")
    else:
        print("Warning: '<script src=\"index.js\"></script>' not found in index.html. Checking if already patched...")
        if "originalFetch" in html:
            print("index.html is already patched.")
        else:
            print("Error: Could not find target script tag to patch.")
            sys.exit(1)

    # 確保 mainPack 也加上版本號（打包時靜態注入，與 wasm/js 使用相同版本字串）
    if '"mainPack":"index.pck"' in html:
        html = html.replace('"mainPack":"index.pck"', f'"mainPack":"index.pck?v={build_ver}"')
        print(f"Successfully patched mainPack in GODOT_CONFIG with version: {build_ver}")
        
    # 替換 GODOT_CONFIG 啟動區塊以防 WebGL2 不支援時產生 ReferenceError
    if "const GODOT_CONFIG =" in html:
        html = html.replace("const GODOT_CONFIG =", "if (window.hasWebGL2) {\nconst GODOT_CONFIG =")
        if "}());\r\n\t\t</script>" in html:
            html = html.replace("}());\r\n\t\t</script>", "}());\n}\r\n\t\t</script>")
            print("Successfully patched GODOT_CONFIG block with WebGL2 conditional check (CRLF).")
        elif "}());\n\t\t</script>" in html:
            html = html.replace("}());\n\t\t</script>", "}());\n}\n\t\t</script>")
            print("Successfully patched GODOT_CONFIG block with WebGL2 conditional check (LF).")
    
    # 注入網頁端廣告 HTML/CSS/JS 覆蓋層
    ad_overlay_html = """
		<!-- HTML Ad Overlay -->
		<div id="web-ad-overlay">
			<div id="web-ad-card">
				<h2 id="web-ad-title">📢 廣告播放中</h2>
				<div id="web-ad-media">
					<div class="pulsing-ring"></div>
					<div class="pulsing-ring-inner"></div>
					<div class="ad-symbol">Ad</div>
				</div>
				<div id="web-ad-timer">5 秒後可跳過廣告</div>
				<button id="web-ad-btn" onclick="closeWebAd()" disabled>請稍候...</button>
			</div>
		</div>

		<!-- CSS Styling -->
		<style>
		#web-ad-overlay {
			position: fixed;
			top: 0;
			left: 0;
			width: 100%;
			height: 100%;
			background: rgba(13, 10, 10, 0.85);
			backdrop-filter: blur(8px);
			-webkit-backdrop-filter: blur(8px);
			display: none;
			justify-content: center;
			align-items: center;
			z-index: 99999;
			font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
		}
		#web-ad-card {
			width: 90%;
			max-width: 400px;
			background: #1F1C1A;
			border: 2px solid #D0813C;
			border-radius: 24px;
			padding: 30px;
			box-sizing: border-box;
			text-align: center;
			color: #FFF2CC;
			box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6);
			transform: scale(0.9);
			transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
			display: flex;
			flex-direction: column;
			align-items: center;
		}
		#web-ad-overlay.active #web-ad-card {
			transform: scale(1);
		}
		#web-ad-title {
			margin: 0 0 10px 0;
			color: #E39450;
			font-size: 1.6rem;
			font-weight: bold;
			text-shadow: 0 2px 4px rgba(0,0,0,0.5);
		}
		#web-ad-media {
			width: 100%;
			height: 180px;
			margin: 20px 0;
			background: #161413;
			border-radius: 16px;
			display: flex;
			justify-content: center;
			align-items: center;
			border: 1px dashed rgba(208, 129, 60, 0.3);
			overflow: hidden;
			position: relative;
		}
		#web-ad-timer {
			font-size: 1.1rem;
			color: #FFF2CC;
			margin: 10px 0 20px 0;
			font-weight: 300;
		}
		#web-ad-btn {
			background: #D0813C;
			color: #1F1C1A;
			border: none;
			padding: 14px 20px;
			font-size: 1.1rem;
			border-radius: 40px;
			cursor: pointer;
			transition: all 0.2s ease;
			font-weight: bold;
			width: 100%;
			box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
		}
		#web-ad-btn:disabled {
			background: #3A322C;
			color: #7C6858;
			cursor: not-allowed;
			box-shadow: none;
		}
		#web-ad-btn:not(:disabled):hover {
			background: #E39450;
			box-shadow: 0 6px 15px rgba(227, 148, 80, 0.4);
			color: #1F1C1A;
		}
		#web-ad-btn:not(:disabled):active {
			transform: scale(0.98);
		}

		/* Pulse Animation */
		.pulsing-ring {
			position: absolute;
			width: 80px;
			height: 80px;
			border-radius: 50%;
			border: 3px solid #D0813C;
			animation: pulse-ring 2s infinite ease-out;
		}
		.pulsing-ring-inner {
			position: absolute;
			width: 60px;
			height: 60px;
			border-radius: 50%;
			border: 2px solid #E39450;
			animation: pulse-ring-inner 2s infinite ease-out;
		}
		.ad-symbol {
			font-size: 1.8rem;
			color: #FFF2CC;
			font-weight: bold;
			z-index: 10;
			background: #1F1C1A;
			padding: 10px 20px;
			border-radius: 12px;
			border: 1px solid #D0813C;
			box-shadow: 0 4px 10px rgba(0,0,0,0.5);
		}

		@keyframes pulse-ring {
			0% {
				transform: scale(0.8);
				opacity: 0.8;
			}
			100% {
				transform: scale(1.8);
				opacity: 0;
			}
		}
		@keyframes pulse-ring-inner {
			0% {
				transform: scale(0.9);
				opacity: 0.9;
			}
			50% {
				transform: scale(1.4);
				opacity: 0.3;
			}
			100% {
				transform: scale(0.9);
				opacity: 0.9;
			}
		}
		</style>

		<!-- JavaScript Overlay Control -->
		<script>
		(function() {
			// === 廣告平台配置 ===
			// "MOCK" (模擬廣告) | "CRAZYGAMES" (CrazyGames SDK) | "GOOGLE_H5" (Google AdSense H5 Ads)
			const AD_PLATFORM = "MOCK"; 
			const GOOGLE_AD_CLIENT = "ca-pub-XXXXXXXXXXXXXXX"; // 替換為您的 AdSense 發布商 ID
			
			// === 動態載入第三方 SDK ===
			if (AD_PLATFORM === "CRAZYGAMES") {
				console.log("[Ad Controller] Loading CrazyGames SDK v2...");
				const script = document.createElement("script");
				script.src = "https://sdk.crazygames.com/crazygames-sdk-v2.js";
				script.async = true;
				script.onload = () => {
					console.log("[Ad Controller] CrazyGames SDK loaded.");
					if (window.CrazyGames && window.CrazyGames.SDK && window.CrazyGames.SDK.game) {
						try {
							window.CrazyGames.SDK.game.gameplayStart();
							console.log("[Ad Controller] First gameplayStart triggered successfully.");
						} catch (e) {
							console.error("[Ad Controller] Failed to call gameplayStart:", e);
						}
					}
				};
				document.head.appendChild(script);
			} else if (AD_PLATFORM === "GOOGLE_H5") {
				console.log("[Ad Controller] Loading Google AdSense H5 Ads SDK with client:", GOOGLE_AD_CLIENT);
				
				// 1. 在載入腳本之前，初始化全域變數與 adBreak/adConfig 函數
				window.adsbygoogle = window.adsbygoogle || [];
				window.adBreak = window.adConfig = function(o) {
					window.adsbygoogle.push(o);
				};
				
				// 2. 進行預設配置
				window.adConfig({
					sound: 'on',
					preloadAdBreaks: 'auto'
				});
				
				// 3. 建立並插入 script 標籤，src 必須帶有 ?client=
				const script = document.createElement("script");
				script.src = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=" + GOOGLE_AD_CLIENT;
				script.async = true;
				script.crossOrigin = "anonymous";
				
				// 4. 設定測試模式與廣告頻率提示屬性
				script.setAttribute("data-ad-frequency-hint", "30s");
				// script.setAttribute("data-ad-break-test", "on"); // 正式上線版本已註解，以播放真實廣告
				
				script.onload = () => {
					console.log("[Ad Controller] Google H5 Ads script tag loaded successfully.");
				};
				document.head.appendChild(script);
			}

			let countdownInterval = null;
			
			window.showWebAd = function() {
				console.log("[Ad Controller] showWebAd triggered. Platform:", AD_PLATFORM);
				
				// --- CrazyGames SDK 廣告模式 ---
				if (AD_PLATFORM === "CRAZYGAMES") {
					if (window.CrazyGames && window.CrazyGames.SDK) {
						console.log("[Ad Controller] Requesting CrazyGames Midgame Ad...");
						window.CrazyGames.SDK.ad.requestAd("midgame", {
							adStarted: () => {
								console.log("[CrazyGames SDK] Ad started.");
							},
							adFinished: () => {
								console.log("[CrazyGames SDK] Ad finished.");
								window.closeWebAd();
							},
							adError: (error) => {
								console.warn("[CrazyGames SDK] Ad error:", error);
								window.closeWebAd(); // 失敗也放行，避免遊戲死鎖
							}
						});
					} else {
						console.warn("[Ad Controller] CrazyGames SDK not loaded yet. Skipping.");
						window.closeWebAd();
					}
					return;
				}
				
				// --- Google H5 Ads 廣告模式 ---
				if (AD_PLATFORM === "GOOGLE_H5") {
					// 3 秒安全計時器：防範被 AdBlock 阻擋導致 callback 永遠不被呼叫而卡死
					let adTriggered = false;
					const adTimeout = setTimeout(() => {
						if (!adTriggered) {
							console.warn("[Ad Controller] Google H5 Ads callback timeout (AdBlocker or no fill). Bypassing...");
							window.closeWebAd();
						}
					}, 3000);
					
					if (typeof window.adBreak === "function") {
						console.log("[Ad Controller] Requesting Google H5 adBreak...");
						window.adBreak({
							type: "next",
							name: "lobby_entry",
							beforeBreak: () => { adTriggered = true; console.log("[Google H5] beforeBreak"); },
							afterBreak: () => { adTriggered = true; clearTimeout(adTimeout); console.log("[Google H5] afterBreak"); window.closeWebAd(); },
							adDismissed: () => { adTriggered = true; clearTimeout(adTimeout); console.log("[Google H5] adDismissed"); window.closeWebAd(); },
							adBreakDone: () => { adTriggered = true; clearTimeout(adTimeout); console.log("[Google H5] adBreakDone"); window.closeWebAd(); }
						});
					} else {
						clearTimeout(adTimeout);
						console.warn("[Ad Controller] Google adBreak function not found. Skipping.");
						window.closeWebAd();
					}
					return;
				}
				
				// --- MOCK 模擬廣告模式 ---
				const overlay = document.getElementById("web-ad-overlay");
				const title = document.getElementById("web-ad-title");
				const timerLabel = document.getElementById("web-ad-timer");
				const button = document.getElementById("web-ad-btn");
				
				let lang = "zh";
				if (window.godot_current_locale) {
					lang = window.godot_current_locale;
				} else if (navigator.language && navigator.language.startsWith("en")) {
					lang = "en";
				}
				
				const dict = {
					"zh": {
						title: "📢 廣告播放中",
						timerPattern: "{sec} 秒後可跳過廣告",
						buttonTextWaiting: "請稍候...",
						buttonTextReady: "跳過廣告 ➔",
						finished: "廣告播映完畢。"
					},
					"en": {
						title: "📢 Ad Playing",
						timerPattern: "Skip in {sec} seconds",
						buttonTextWaiting: "Please wait...",
						buttonTextReady: "Skip Ad ➔",
						finished: "Ad finished."
					}
				};
				
				const t = dict[lang] || dict["zh"];
				if (lang.startsWith("zh")) {
					const dictT = dict["zh"];
					title.innerText = dictT.title;
					button.innerText = dictT.buttonTextWaiting;
				} else {
					title.innerText = t.title;
					button.innerText = t.buttonTextWaiting;
				}
				
				button.disabled = true;
				overlay.style.display = "flex";
				
				setTimeout(() => { overlay.classList.add("active"); }, 20);
				
				let secondsRemaining = 5;
				timerLabel.innerText = t.timerPattern.replace("{sec}", secondsRemaining);
				
				if (countdownInterval) clearInterval(countdownInterval);
				countdownInterval = setInterval(() => {
					secondsRemaining--;
					if (secondsRemaining <= 0) {
						clearInterval(countdownInterval);
						timerLabel.innerText = t.finished;
						button.innerText = t.buttonTextReady;
						button.disabled = false;
					} else {
						timerLabel.innerText = t.timerPattern.replace("{sec}", secondsRemaining);
					}
				}, 1000);
			};
			
			window.closeWebAd = function() {
				console.log("[Ad Controller] closing Web Ad.");
				const overlay = document.getElementById("web-ad-overlay");
				if (overlay) {
					overlay.classList.remove("active");
					setTimeout(() => {
						overlay.style.display = "none";
					}, 300);
				}
				
				if (countdownInterval) {
					clearInterval(countdownInterval);
					countdownInterval = null;
				}
				
				if (typeof window.godot_on_web_ad_finished === "function") {
					window.godot_on_web_ad_finished();
				} else {
					console.warn("[Ad Controller] window.godot_on_web_ad_finished callback not found.");
				}
			};
		})();
		</script>
	"""
    if "</body>" in html and "web-ad-overlay" not in html:
        html = html.replace("</body>", ad_overlay_html + "</body>")
        print("Successfully injected web advertisement overlay before </body>.")
    elif "</body>" in html and "web-ad-overlay" in html:
        # 如果已經有了，直接覆蓋更新 (這能防止重複注入，也能更新最新的 JS 邏輯)
        # 我們將 </body> 前面的部分替換成新的 ad_overlay_html + </body>
        # 先找到原本的注入起點 <!-- HTML Ad Overlay -->
        start_idx = html.find("<!-- HTML Ad Overlay -->")
        if start_idx != -1:
            html = html[:start_idx] + ad_overlay_html + "</body>"
            print("Successfully updated injected web advertisement overlay in index.html.")
    
    og_meta_tags = """
		<!-- Social Media Preview (Open Graph) -->
		<meta property="og:title" content="Friends & Me - 異步社交探索桌遊" />
		<meta property="og:description" content="透過自我揭露與社交驗證，促進朋友間的深度連結與自我探索。" />
		<meta property="og:image" content="https://friendandme.netlify.app/index.icon.png" />
		<meta property="og:url" content="https://friendandme.netlify.app/" />
		<meta property="og:type" content="website" />
		<meta name="twitter:card" content="summary_large_image" />
		<meta name="twitter:title" content="Friends & Me - 異步社交探索桌遊" />
		<meta name="twitter:description" content="透過自我揭露與社交驗證，促進朋友間的深度連結與自我探索。" />
		<meta name="twitter:image" content="https://friendandme.netlify.app/index.icon.png" />"""
    
    if "<!-- Social Media Preview (Open Graph) -->" in html:
        start_idx = html.find("<!-- Social Media Preview (Open Graph) -->")
        end_idx = html.find('<meta name="twitter:image"', start_idx)
        if end_idx != -1:
            end_line_idx = html.find(">", end_idx)
            if end_line_idx != -1:
                html = html[:start_idx] + og_meta_tags + html[end_line_idx + 1:]
                print("Successfully updated Open Graph Social Media Preview meta tags.")
    else:
        if "<head>" in html:
            html = html.replace("<head>", "<head>" + og_meta_tags)
            print("Successfully injected Open Graph Social Media Preview meta tags into <head>.")

    with open(export_output, 'w', encoding='utf-8') as f:
        f.write(html)
        
    print("=== Step 4: Generating Netlify and CrazyGames Releases ===")
    import shutil
    
    netlify_dir = r"C:\FriendAndMe\build_web_netlify"
    crazygames_dir = r"C:\FriendAndMe\build_web_crazygames"
    temp_dir = r"C:\FriendAndMe\build_web_temp"
    
    # 複製成兩個獨立的版本目錄
    for target_dir in [netlify_dir, crazygames_dir]:
        if os.path.exists(target_dir):
            print(f"Cleaning existing directory: {target_dir}")
            shutil.rmtree(target_dir)
        print(f"Cloning files to: {target_dir}")
        shutil.copytree(temp_dir, target_dir)
        
    # 補丁 Netlify 版本的 index.html（設置為 GOOGLE_H5 平台與真實 Publisher ID，並加上 AdSense 驗證腳本）
    netlify_html_path = os.path.join(netlify_dir, "index.html")
    with open(netlify_html_path, 'r', encoding='utf-8') as f:
        n_html = f.read()
    n_html = n_html.replace('const AD_PLATFORM = "MOCK";', 'const AD_PLATFORM = "GOOGLE_H5";')
    n_html = n_html.replace('const GOOGLE_AD_CLIENT = "ca-pub-XXXXXXXXXXXXXXX";', 'const GOOGLE_AD_CLIENT = "ca-pub-XXXXXXXXXXXXXXXX";')
    
    # 注入 AdSense 靜態驗證腳本到 <head> 中，方便 Google 驗證網站所有權
    verification_tag = '\n\t<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX" crossorigin="anonymous"></script>'
    if "<head>" in n_html:
        n_html = n_html.replace("<head>", "<head>" + verification_tag)
        
    # --- 專利優化：為通過 Google AdSense「沒有發布商內容」(Valuable Inventory: No Content) 審核，注入 SEO 質感登陸頁面 ---
    import re
    # 1. 包裝 Godot 引擎啟動代碼，改由「開始遊戲」按鈕觸發
    engine_start_pattern = r"(setStatusMode\('progress'\);\s*engine\.startGame\(\{.*?\}\)\.then\(\(\) => \{\s*setStatusMode\('hidden'\);\s*\}, displayFailureNotice\);)"
    match = re.search(engine_start_pattern, n_html, re.DOTALL)
    if match:
        wrapped_start = f"window.launchGame = function() {{\n\t\t{match.group(1)}\n\t}};"
        n_html = n_html.replace(match.group(1), wrapped_start)
        print("Netlify Patch: Wrapped Godot engine auto-start code.")
    else:
        print("Warning: Could not find engine.startGame block in Netlify build to wrap.")
        
    # 2. 注入登陸頁面 CSS 樣式到 </head> 之前
    landing_css = """
		/* Landing Page Styles */
		#landing-page {
			position: fixed;
			top: 0;
			left: 0;
			width: 100%;
			height: 100%;
			background: radial-gradient(circle at 50% 50%, #161413 0%, #080707 100%);
			z-index: 99990;
			overflow-y: auto;
			font-family: 'Outfit', 'Noto Sans TC', system-ui, -apple-system, sans-serif;
			color: #FFF2CC;
			padding: 40px 20px;
			box-sizing: border-box;
			display: flex;
			flex-direction: column;
			align-items: center;
			opacity: 1;
			transition: opacity 0.5s ease;
		}
		
		#landing-page.fade-out {
			opacity: 0;
			pointer-events: none;
		}

		.landing-header {
			width: 100%;
			max-width: 800px;
			display: flex;
			justify-content: space-between;
			align-items: center;
			margin-bottom: 40px;
		}

		.landing-logo {
			font-size: 28px;
			font-weight: 700;
			color: #D0813C;
			letter-spacing: 1px;
		}

		.landing-lang-switch {
			display: flex;
			gap: 10px;
		}

		.landing-lang-btn {
			background: rgba(255, 255, 255, 0.05);
			border: 1px solid rgba(255, 255, 255, 0.1);
			color: rgba(255, 242, 204, 0.7);
			padding: 8px 16px;
			border-radius: 20px;
			cursor: pointer;
			font-weight: 600;
			font-size: 14px;
			transition: all 0.22s ease;
		}

		.landing-lang-btn.active, .landing-lang-btn:hover {
			background: #D0813C;
			border-color: #D0813C;
			color: #fff;
			box-shadow: 0 4px 12px rgba(208, 129, 60, 0.3);
		}

		.landing-hero {
			text-align: center;
			max-width: 600px;
			margin-bottom: 40px;
		}

		#landing-hero-title {
			font-size: 38px;
			font-weight: 700;
			color: #E39450;
			margin-bottom: 15px;
			text-shadow: 0 4px 10px rgba(0,0,0,0.5);
		}

		#landing-hero-subtitle {
			font-size: 18px;
			color: rgba(255, 242, 204, 0.7);
			line-height: 1.6;
			margin-bottom: 30px;
		}

		#landing-play-btn {
			background: #D0813C;
			color: #1F1C1A;
			border: none;
			padding: 16px 40px;
			font-size: 1.3rem;
			border-radius: 50px;
			cursor: pointer;
			font-weight: 700;
			box-shadow: 0 8px 24px rgba(208, 129, 60, 0.4);
			transition: all 0.25s cubic-bezier(0.25, 0.8, 0.25, 1);
		}

		#landing-play-btn:hover {
			background: #E39450;
			transform: scale(1.05);
			box-shadow: 0 12px 30px rgba(227, 148, 80, 0.5);
		}

		#landing-play-btn:active {
			transform: scale(0.97);
		}

		.landing-container {
			width: 100%;
			max-width: 800px;
			display: flex;
			flex-direction: column;
			gap: 25px;
		}

		.landing-card {
			background: rgba(30, 26, 24, 0.6);
			backdrop-filter: blur(12px);
			-webkit-backdrop-filter: blur(12px);
			border: 2px solid rgba(208, 129, 60, 0.18);
			border-radius: 24px;
			padding: 30px;
			box-shadow: 0 10px 25px rgba(0,0,0,0.3);
		}

		.landing-card h2 {
			font-size: 22px;
			color: #D0813C;
			margin-bottom: 15px;
			font-weight: 700;
		}

		.landing-card p {
			font-size: 16px;
			line-height: 1.7;
			color: rgba(255, 242, 204, 0.8);
			margin-bottom: 15px;
		}

		.landing-card p:last-child {
			margin-bottom: 0;
		}

		.landing-card ul, .landing-card ol {
			margin-left: 20px;
			margin-bottom: 15px;
			color: rgba(255, 242, 204, 0.8);
		}

		.landing-card li {
			margin-bottom: 10px;
			line-height: 1.6;
		}

		.landing-card li strong {
			color: #E39450;
		}

		.landing-footer {
			width: 100%;
			max-width: 800px;
			margin-top: 50px;
			text-align: center;
			font-size: 14px;
			color: rgba(255, 242, 204, 0.4);
			border-top: 1px solid rgba(208, 129, 60, 0.1);
			padding-top: 25px;
			display: flex;
			flex-direction: column;
			gap: 8px;
		}

		.landing-footer a {
			color: #D0813C;
			text-decoration: none;
		}
		.landing-footer a:hover {
			text-decoration: underline;
		}

		@media (max-width: 600px) {
			#landing-page {
				padding: 30px 15px;
			}
			.landing-header {
				margin-bottom: 25px;
			}
			.landing-logo {
				font-size: 24px;
			}
			#landing-hero-title {
				font-size: 28px;
			}
			#landing-hero-subtitle {
				font-size: 16px;
			}
			#landing-play-btn {
				font-size: 1.15rem;
				padding: 14px 30px;
			}
			.landing-card {
				padding: 20px;
				border-radius: 18px;
			}
			.landing-card h2 {
				font-size: 18px;
			}
		}
	"""
    n_html = n_html.replace("</head>", f"\t<style>{landing_css}</style>\n</head>")
    
    # 3. 注入登陸頁面 HTML 與控制腳本到 <body> 之後
    landing_html = """
		<!-- Landing Page for SEO and Crawler Approval -->
		<div id="landing-page">
			<div class="landing-header">
				<div class="landing-logo">Friends & Me</div>
				<div class="landing-lang-switch">
					<button id="landing-btn-zh" class="landing-lang-btn active" onclick="setLandingLanguage('zh')">中文</button>
					<button id="landing-btn-en" class="landing-lang-btn" onclick="setLandingLanguage('en')">English</button>
				</div>
			</div>
			
			<div class="landing-hero">
				<h1 id="landing-hero-title">異步社交探索桌遊</h1>
				<p id="landing-hero-subtitle">透過自我揭露與社交驗證，促進朋友間的深度連結與自我探索。</p>
				<button id="landing-play-btn" onclick="launchEngine()">開始遊戲 ➔</button>
			</div>

			<div class="landing-container">
				<!-- Traditional Chinese Content -->
				<div id="landing-content-zh">
					<div class="landing-card">
						<h2>🧠 遊戲設計理念</h2>
						<p>本遊戲基於<strong>喬哈里視窗（Johari Window）</strong>心理學理論設計。透過「自我揭露」與「社交驗證」雙向互動，幫助玩家探索他人眼中的自己與真實自我之間的默契落差，開啟深度、溫馨且有意義的對話。</p>
					</div>

					<div class="landing-card">
						<h2>🔒 心理安全與隱私保障</h2>
						<p>我們深知揭露自我的社交焦慮，因此設計了「不回答」機制，讓玩家在不願分享特定話題時能體面拒絕，同時作為配對時的干擾項。所有對局數據僅在伺服器隨機存取記憶體 (RAM) 中暫存同步，一旦玩家離線或遊戲結束即<strong>徹底擦除</strong>，零永久儲存，保障您的絕對隱私。</p>
					</div>

					<div class="landing-card">
						<h2>☕ 社交話題深度分級 (Level 1 - 5)</h2>
						<p>遊戲提供 5 個不同的社交級別話題，適配各種聚會情境：</p>
						<ul>
							<li><strong>Level 1：閒話家常</strong> - 關於日常習慣與輕鬆偏好。</li>
							<li><strong>Level 2：下午茶閒聊</strong> - 適合普通朋友與聚會破冰。</li>
							<li><strong>Level 3：居酒屋微醺</strong> - 稍微深入的感情與生活交流。</li>
							<li><strong>Level 4：深夜真心話</strong> - 屬於摯友或伴侶間的夜深小秘密。</li>
							<li><strong>Level 5：靈魂拷問</strong> - 挑戰道德邊界或極端情境的深度思辨。</li>
						</ul>
					</div>

					<div class="landing-card">
						<h2>🎮 四大核心遊玩步驟</h2>
						<ol>
							<li><strong>創建/加入房間</strong>：快速輸入暱稱，一鍵創建 6 位數房間碼並發送給好友。</li>
							<li><strong>選題與答題</strong>：隊長隨機選題，所有玩家在限時內填寫答案或選擇不回答。</li>
							<li><strong>社交配對猜測</strong>：拖曳玩家大頭貼與對應的匿名答案進行配對。</li>
							<li><strong>精彩結算揭曉</strong>：觀看精緻的猜中率百分比動畫，統計每局的默契得分。</li>
						</ol>
					</div>

					<div class="landing-card">
						<h2>❓ 常見問答 (FAQ)</h2>
						<p><strong>問：這款遊戲適合多少人玩？</strong><br>答：本遊戲適合 2 至 6 人同時連線遊玩，是家庭聚會、派對或情侶互動的絕佳選擇。</p>
						<p><strong>問：網頁版與 App 版有什麼區別？</strong><br>答：網頁版即開即玩，方便快捷；App 版效能更穩定，且支援 Google Play 應用內購買「移除廣告」方案，提供更為純淨的無廣告遊戲體驗。</p>
					</div>
				</div>

				<!-- English Content -->
				<div id="landing-content-en" style="display: none;">
					<div class="landing-card">
						<h2>🧠 Core Vision & Concept</h2>
						<p>Designed around the psychological concept of the <strong>Johari Window</strong>. Through gameplay, players disclose aspects of themselves and verify how their friends perceive them, resolving the gap between self-perception and public-perception in a fun, meaningful way.</p>
					</div>

					<div class="landing-card">
						<h2>🔒 Psychological Safety & Privacy</h2>
						<p>To reduce social anxiety, players can select "Prefer Not to Answer" to skip sensitive questions. This option acts as a distractor during the matchmaking phase. All session data is cached temporarily in the server's RAM and is <strong>permanently erased</strong> once the session ends. No database records are kept.</p>
					</div>

					<div class="landing-card">
						<h2>☕ Topics Depth Levels (Level 1 - 5)</h2>
						<p>Features 5 progressive difficulty levels to match any social scenario:</p>
						<ul>
							<li><strong>Level 1: Casual Chat</strong> - Daily habits and light preferences.</li>
							<li><strong>Level 2: Afternoon Tea</strong> - Icebreakers and casual catch-ups.</li>
							<li><strong>Level 3: Izakaya Drunk</strong> - Relationship stories and life experiences.</li>
							<li><strong>Level 4: Late-Night Secrets</strong> - Deep personal shares for close friends.</li>
							<li><strong>Level 5: Soul Search</strong> - Extreme scenarios and ethical dilemmas.</li>
						</ul>
					</div>

					<div class="landing-card">
						<h2>🎮 Four Core Gameplay Steps</h2>
						<ol>
							<li><strong>Lobby Setup</strong>: Enter a nickname and generate a 6-digit room code to invite friends.</li>
							<li><strong>Answer Questions</strong>: The leader picks a level, and players type their answers or choose to skip.</li>
							<li><strong>Matchmaking Guess</strong>: Link player avatars with their guessed answers in a matching interface.</li>
							<li><strong>Score Revelation</strong>: Watch real-time percentage animation counting correct guesses.</li>
						</ol>
					</div>

					<div class="landing-card">
						<h2>❓ Frequently Asked Questions (FAQ)</h2>
						<p><strong>Q: How many players are supported?</strong><br>A: Best played with 2 to 6 players simultaneously, perfect for party meetups and couples.</p>
						<p><strong>Q: What is the difference between Web and App?</strong><br>A: Web version loads instantly in browser. The App version provides offline caching and includes an optional "Remove Ads" in-app purchase (1 USD / 30 TWD) to remove all interstitial ads.</p>
					</div>
				</div>
			</div>

			<footer class="landing-footer">
				<p>&copy; 2026 Friends & Me. All Rights Reserved. | <a href="/privacy.html" target="_blank">隱私權政策 (Privacy Policy)</a></p>
				<p>開發者聯絡信箱 (Contact): <strong>hank92312@gmail.com</strong></p>
			</footer>
		</div>

		<script>
			function setLandingLanguage(lang) {
				const zhDiv = document.getElementById('landing-content-zh');
				const enDiv = document.getElementById('landing-content-en');
				const btnZh = document.getElementById('landing-btn-zh');
				const btnEn = document.getElementById('landing-btn-en');
				const heroTitle = document.getElementById('landing-hero-title');
				const heroSubtitle = document.getElementById('landing-hero-subtitle');
				const playBtn = document.getElementById('landing-play-btn');
				
				if (lang === 'zh') {
					zhDiv.style.display = 'block';
					enDiv.style.display = 'none';
					btnZh.classList.add('active');
					btnEn.classList.remove('active');
					heroTitle.innerText = '異步社交探索桌遊';
					heroSubtitle.innerText = '透過自我揭露與社交驗證，促進朋友間的深度連結與自我探索。';
					playBtn.innerText = '開始遊戲 ➔';
				} else {
					zhDiv.style.display = 'none';
					enDiv.style.display = 'block';
					btnZh.classList.remove('active');
					btnEn.classList.add('active');
					heroTitle.innerText = 'Asynchronous Social Party Game';
					heroSubtitle.innerText = 'Align self-perception with friends\\' insights through fun, secure self-disclosure.';
					playBtn.innerText = 'Play Game ➔';
				}
			}
			
			function launchEngine(skipFade) {
				// 記錄本分頁已啟動過遊戲，供切換 App 後被瀏覽器重新載入時自動恢復
				try { sessionStorage.setItem('fm_launched', '1'); } catch (e) {}
				const lp = document.getElementById('landing-page');
				const startEngine = () => {
					lp.style.display = 'none';
					if (typeof window.launchGame === 'function') {
						window.launchGame();
					} else {
						// 引擎主程式尚未就緒，短暫輪詢等待（最多約 10 秒）
						let tries = 0;
						const iv = setInterval(() => {
							if (typeof window.launchGame === 'function') {
								clearInterval(iv);
								window.launchGame();
							} else if (++tries > 100) {
								clearInterval(iv);
								console.error("launchGame function not found.");
							}
						}, 100);
					}
				};
				if (skipFade) {
					startEngine();
				} else {
					lp.classList.add('fade-out');
					setTimeout(startEngine, 500);
				}
			}
			
			// Auto detect browser language
			(function() {
				let defaultLang = 'zh';
				if (navigator.language && navigator.language.startsWith('en')) {
					defaultLang = 'en';
				}
				// Wait for DOM to load
				window.addEventListener('DOMContentLoaded', () => {
					setLandingLanguage(defaultLang);
					// 若本分頁先前已啟動過遊戲（例如切到 LINE 後被 iOS Safari 記憶體回收而重新載入），
					// 自動跳過登陸頁直接啟動引擎，避免「掉回入口頁」。
					// 新訪客與爬蟲無此旗標，仍會看到登陸頁，故不影響 AdSense SEO 審核。
					try {
						if (sessionStorage.getItem('fm_launched') === '1') {
							launchEngine(true);
						}
					} catch (e) {}
				});
			})();
		</script>
"""
    n_html = n_html.replace("<body>", f"<body>{landing_html}")
    
    with open(netlify_html_path, 'w', encoding='utf-8') as f:
        f.write(n_html)
    print("Successfully configured Netlify build for GOOGLE_H5 and injected static AdSense verification script.")
    
    # 建立 Netlify 的 _headers 檔案（SharedArrayBuffer 跨域許可標頭）
    headers_path = os.path.join(netlify_dir, "_headers")
    # 註：本專案 Web 匯出 thread_support=false，不使用 SharedArrayBuffer，
    # 因此「不需要」跨域隔離標頭。先前的 Cross-Origin-Embedder-Policy: require-corp
    # 會在 iOS Safari 上封鎖跨域子資源（造成卡讀取）並擋掉 Google 廣告載入，故移除。
    headers_content = """/*
  Cross-Origin-Opener-Policy: same-origin-allow-popups

# index.html 是唯一的入口，不帶版本號，必須強制每次重新驗證，
# 確保新部署後玩家拿到最新 HTML（HTML 裡的 index.js/wasm/pck 都帶版本號）。
/index.html
  Cache-Control: no-cache, no-store, must-revalidate

# index.js / wasm / pck 都已在 build_and_patch.py 打包時注入靜態版本號 ?v=BUILD_VER，
# 相同版本所有人 URL 相同，CDN 只需從來源抓一次即可快取給所有後續使用者。
# immutable 告知瀏覽器：同 URL 的內容永遠不會改，無需重新驗證，直接從快取服務。
/*.js
  Cache-Control: public, max-age=31536000, immutable
/*.wasm
  Cache-Control: public, max-age=31536000, immutable
/*.pck
  Cache-Control: public, max-age=31536000, immutable
"""
    with open(headers_path, 'w', encoding='utf-8') as f:
        f.write(headers_content)
    print("Successfully created _headers file for Netlify.")
    
    # 建立 Netlify 的 ads.txt 檔案（宣告授權廣告賣方，防範廣告詐騙並提升廣告收益品質）
    ads_txt_path = os.path.join(netlify_dir, "ads.txt")
    ads_txt_content = "google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0\n"
    with open(ads_txt_path, 'w', encoding='utf-8') as f:
        f.write(ads_txt_content)
    print("Successfully created ads.txt file for Netlify.")
    
    # 建立 Netlify 的 privacy.html 隱私權政策網頁 (RWD 響應式排版，中英文切換，符合 Google 商店上架政策)
    privacy_html_path = os.path.join(netlify_dir, "privacy.html")
    privacy_html_content = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>Friends & Me - 隱私權政策 / Privacy Policy</title>
	<link rel="preconnect" href="https://fonts.googleapis.com">
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
	<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Noto+Sans+TC:wght@300;400;700&display=swap" rel="stylesheet">
	<style>
		:root {
			--bg-dark: #080707;
			--bg-light: #161413;
			--primary: #D0813C;
			--text-main: #FFF2CC;
			--text-muted: rgba(255, 242, 204, 0.7);
			--glass-bg: rgba(30, 26, 24, 0.6);
			--glass-border: rgba(208, 129, 60, 0.18);
		}
		
		* {
			box-sizing: border-box;
			margin: 0;
			padding: 0;
		}

		body {
			font-family: 'Outfit', 'Noto Sans TC', sans-serif;
			background: radial-gradient(circle at 50% 50%, var(--bg-light) 0%, var(--bg-dark) 100%);
			color: var(--text-main);
			min-height: 100vh;
			display: flex;
			flex-direction: column;
			align-items: center;
			justify-content: flex-start;
			padding: 40px 20px;
			line-height: 1.6;
		}

		.container {
			max-width: 800px;
			width: 100%;
			background: var(--glass-bg);
			backdrop-filter: blur(12px);
			-webkit-backdrop-filter: blur(12px);
			border: 2px solid var(--glass-border);
			border-radius: 32px;
			padding: 40px;
			box-shadow: 0 16px 32px rgba(0, 0, 0, 0.5);
			margin-top: 20px;
		}

		header {
			width: 100%;
			max-width: 800px;
			display: flex;
			justify-content: space-between;
			align-items: center;
			margin-bottom: 20px;
		}

		.logo {
			font-size: 28px;
			font-weight: 700;
			color: var(--primary);
			letter-spacing: 1px;
		}

		.lang-switch {
			display: flex;
			gap: 10px;
		}

		.lang-btn {
			background: rgba(255, 255, 255, 0.05);
			border: 1px solid rgba(255, 255, 255, 0.1);
			color: var(--text-muted);
			padding: 8px 16px;
			border-radius: 20px;
			cursor: pointer;
			font-weight: 600;
			font-size: 14px;
			transition: all 0.22s ease;
		}

		.lang-btn.active, .lang-btn:hover {
			background: var(--primary);
			border-color: var(--primary);
			color: #fff;
			box-shadow: 0 4px 12px rgba(208, 129, 60, 0.3);
		}

		h1 {
			font-size: 32px;
			font-weight: 700;
			color: var(--primary);
			margin-bottom: 30px;
			border-bottom: 1px solid var(--glass-border);
			padding-bottom: 15px;
			text-align: center;
		}

		h2 {
			font-size: 20px;
			margin-top: 30px;
			margin-bottom: 15px;
			color: var(--primary);
			display: flex;
			align-items: center;
			gap: 10px;
		}

		p {
			font-size: 16px;
			color: var(--text-muted);
			margin-bottom: 15px;
			text-align: justify;
		}

		ul {
			margin-left: 20px;
			margin-bottom: 20px;
			color: var(--text-muted);
		}

		li {
			margin-bottom: 8px;
		}

		footer {
			margin-top: 40px;
			text-align: center;
			font-size: 14px;
			color: rgba(255, 242, 204, 0.4);
		}

		/* Responsive styling */
		@media (max-width: 600px) {
			body {
				padding: 20px 10px;
			}
			.container {
				padding: 25px 20px;
				border-radius: 24px;
			}
			h1 {
				font-size: 24px;
			}
			h2 {
				font-size: 18px;
			}
		}
	</style>
</head>
<body>

	<header>
		<div class="logo">Friends & Me</div>
		<div class="lang-switch">
			<button id="btn-zh" class="lang-btn active" onclick="setLanguage('zh')">中文</button>
			<button id="btn-en" class="lang-btn" onclick="setLanguage('en')">English</button>
		</div>
	</header>

	<div class="container">
		<!-- Traditional Chinese Privacy Policy -->
		<div id="lang-zh">
			<h1>《Friends & Me》隱私權政策</h1>
			<p>更新日期：2026 年 6 月 3 日</p>
			
			<p>本遊戲《Friends & Me》（以下簡稱「本遊戲」）非常重視您的隱私權。我們致力於保護您的個人資料，請詳閱以下隱私權保護聲明：</p>

			<h2>1. 零永久儲存機制</h2>
			<p>本遊戲與遊戲連線伺服器<strong>「完全不會」</strong>永久儲存您在遊戲中輸入的任何個人對局資料（包括但不限於玩家暱稱、自訂答題文字、配對選擇或每局的投票得分紀錄）。</p>

			<h2>2. 資料即時刪除與 RAM 快取</h2>
			<p>所有遊戲中的即時數據僅暫存於伺服器的隨機存取記憶體（RAM）中，以供本局進行中的玩家即時同步。當您關閉遊戲、主動退出房間，或房間中所有玩家斷開連線後，伺服器會立即將您的所有暫存資料與個人資訊<strong>「徹底刪除」</strong>，不留任何備份或對局紀錄。</p>

			<h2>3. 第三方服務與 SDK 規範</h2>
			<p>為了維持遊戲的正常運作與基本收益，我們可能使用以下第三方 SDK 服務，其處理資訊的政策如下：</p>
			<ul>
				<li><strong>Google AdMob / AdSense H5 廣告</strong>：本遊戲使用 Google 提供的網頁 H5 廣告服務。Google 可能會收集並使用您的匿名設備識別碼、Cookie 或其他非個人化識別資訊，以向您投放相關廣告。</li>
				<li><strong>Google Play Billing (應用內購買)</strong>：本遊戲的 Android APK 版本包含購買「移除廣告」的選項。所有付款與交易均直接由 Google Play 商店安全地處理。我們不會收集、儲存或接觸您的信用卡資訊或任何交易敏感性細節，僅在本地與 Google 商店伺服器核對是否已完成購買狀態。</li>
			</ul>

			<h2>4. 本地快取 (Local Storage)</h2>
			<p>本遊戲僅在您設備本地（瀏覽器快取或 App 用戶數據區）儲存您的語言設定、音效開關偏好，以及經加密的去廣告購買狀態。這些設定僅供您本地端體驗使用，絕不會上傳或共享至任何伺服器。</p>

			<h2>5. 聯絡我們</h2>
			<p>如果您對本遊戲的隱私權政策有任何疑問，歡迎聯絡製作人：<br>
			<strong>hank92312@gmail.com</strong></p>
		</div>

		<!-- English Privacy Policy -->
		<div id="lang-en" style="display: none;">
			<h1>Privacy Policy for 《Friends & Me》</h1>
			<p>Last Updated: June 3, 2026</p>
			
			<p>We highly value your privacy. This Privacy Policy explains how we protect and handle your personal data when you play our game, 《Friends & Me》:</p>

			<h2>1. Zero Permanent Storage</h2>
			<p>This game and its connection servers <strong>DO NOT</strong> permanently store any of your inputted personal gameplay data (including nicknames, custom answers, matchmaking choices, or round score records).</p>

			<h2>2. RAM Caching & Instant Erasure</h2>
			<p>All in-game data is temporarily cached in the server's Random Access Memory (RAM) solely for real-time synchronization between active players. Once you close the game, leave the room, or all players disconnect, all cached data and personal information are immediately and permanently erased from the server. No backup copies are retained.</p>

			<h2>3. Third-Party Services & SDKs</h2>
			<p>To sustain server operations and support the app, we integrate third-party SDKs which handle data as follows:</p>
			<ul>
				<li><strong>Google AdMob / AdSense H5 Ads</strong>: The game requests H5 ads from Google. Google may collect and use anonymous device identifiers, cookies, or other non-personally identifiable information to deliver relevant advertisements.</li>
				<li><strong>Google Play Billing (In-App Purchases)</strong>: The Android APK version provides an option to purchase "Remove Ads". All payment processing and transactions are handled securely by the Google Play Store. We do not collect, view, or store any credit card numbers or transaction details. We only query Google Play to check if you have purchased the ad-free upgrade.</li>
			</ul>

			<h2>4. Local Storage</h2>
			<p>The game only saves your language settings, sound preferences, and encrypted ad-removal purchase status locally on your device's browser cache or local app storage. This data is strictly local and is never uploaded to any servers.</p>

			<h2>5. Contact Us</h2>
			<p>If you have any questions regarding this Privacy Policy, please contact the developer at:<br>
			<strong>hank92312@gmail.com</strong></p>
		</div>
	</div>

	<footer>
		&copy; 2026 Friends & Me. All Rights Reserved.
	</footer>

	<script>
		function setLanguage(lang) {
			const zhDiv = document.getElementById('lang-zh');
			const enDiv = document.getElementById('lang-en');
			const btnZh = document.getElementById('btn-zh');
			const btnEn = document.getElementById('btn-en');
			
			if (lang === 'zh') {
				zhDiv.style.display = 'block';
				enDiv.style.display = 'none';
				btnZh.classList.add('active');
				btnEn.classList.remove('active');
				document.documentElement.lang = 'zh-TW';
			} else {
				zhDiv.style.display = 'none';
				enDiv.style.display = 'block';
				btnZh.classList.remove('active');
				btnEn.classList.add('active');
				document.documentElement.lang = 'en';
			}
		}
	</script>
</body>
</html>
"""
    with open(privacy_html_path, 'w', encoding='utf-8') as f:
        f.write(privacy_html_content)
    print("Successfully created privacy.html file for Netlify.")
    
    # 補丁 CrazyGames 版本的 index.html（設置為 CRAZYGAMES 平台）
    crazygames_html_path = os.path.join(crazygames_dir, "index.html")
    with open(crazygames_html_path, 'r', encoding='utf-8') as f:
        c_html = f.read()
    c_html = c_html.replace('const AD_PLATFORM = "MOCK";', 'const AD_PLATFORM = "CRAZYGAMES";')
    with open(crazygames_html_path, 'w', encoding='utf-8') as f:
        f.write(c_html)
    print("Successfully configured CrazyGames build for CRAZYGAMES.")
    
    # 清理臨時目錄
    print("Cleaning up temporary build folder...")
    shutil.rmtree(temp_dir)
    
    print("=== Patching complete! ===")

if __name__ == '__main__':
    main()
