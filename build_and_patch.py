import subprocess
import os
import sys

def main():
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
							input.style.setProperty('opacity', '0.01', 'important');
							input.style.setProperty('z-index', '99999', 'important');
							input.style.setProperty('position', 'absolute', 'important');
							input.style.setProperty('top', '10px', 'important');
							input.style.setProperty('left', '10px', 'important');
							input.style.setProperty('width', 'calc(100% - 20px)', 'important');
							input.style.setProperty('height', '80px', 'important');
						});
						
						input.addEventListener('blur', function() {
							input.style.setProperty('z-index', '-1', 'important');
							input.style.setProperty('opacity', '0', 'important');
						});
					});
				}
				setInterval(patchInputs, 500);
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
							url = url + separator + 'v=' + Date.now();
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
				document.write('<script src="index.js?v=' + Date.now() + '"><\\/script>');
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

    # 確保 mainPack 也加上 Date.now() 如果原本的 export 沒有加上的話
    # 在 GODOT_CONFIG 裡面
    if '"mainPack":"index.pck"' in html:
        html = html.replace('"mainPack":"index.pck"', '"mainPack":"index.pck?v=" + Date.now()')
        print("Successfully patched mainPack in GODOT_CONFIG.")
        
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
				console.log("[Ad Controller] Loading Google AdSense H5 Ads SDK...");
				const script = document.createElement("script");
				script.src = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js";
				script.async = true;
				script.dataAdBreakTest = "on"; // 本地測試使用測試模式，上線前可刪除此屬性
				script.onload = () => {
					console.log("[Ad Controller] Google H5 Ads script loaded. Configuring...");
					window.adsbygoogle = window.adsbygoogle || [];
					window.adConfig = window.adConfig || function(p) { (window.adsbygoogle = window.adsbygoogle || []).push(p); };
					window.adConfig({
						sound: 'on',
						google_ad_client: GOOGLE_AD_CLIENT,
						google_ad_channel: "h5-games",
						google_overlay: true
					});
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
					if (typeof window.adBreak === "function") {
						console.log("[Ad Controller] Requesting Google H5 adBreak...");
						window.adBreak({
							type: "next",
							name: "lobby_entry",
							beforeBreak: () => { console.log("[Google H5] beforeBreak"); },
							afterBreak: () => { console.log("[Google H5] afterBreak"); window.closeWebAd(); },
							adDismissed: () => { console.log("[Google H5] adDismissed"); window.closeWebAd(); },
							adBreakDone: () => { console.log("[Google H5] adBreakDone"); window.closeWebAd(); }
						});
					} else {
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
        
    # 補丁 Netlify 版本的 index.html（設置為 GOOGLE_H5 平台與真實 Publisher ID）
    netlify_html_path = os.path.join(netlify_dir, "index.html")
    with open(netlify_html_path, 'r', encoding='utf-8') as f:
        n_html = f.read()
    n_html = n_html.replace('const AD_PLATFORM = "MOCK";', 'const AD_PLATFORM = "GOOGLE_H5";')
    n_html = n_html.replace('const GOOGLE_AD_CLIENT = "ca-pub-XXXXXXXXXXXXXXX";', 'const GOOGLE_AD_CLIENT = "ca-pub-XXXXXXXXXXXXXXXX";')
    with open(netlify_html_path, 'w', encoding='utf-8') as f:
        f.write(n_html)
    print("Successfully configured Netlify build for GOOGLE_H5 with ca-pub-XXXXXXXXXXXXXXXX.")
    
    # 建立 Netlify 的 _headers 檔案（SharedArrayBuffer 跨域許可標頭）
    headers_path = os.path.join(netlify_dir, "_headers")
    headers_content = """/*
  Cross-Origin-Opener-Policy: same-origin
  Cross-Origin-Embedder-Policy: require-corp
"""
    with open(headers_path, 'w', encoding='utf-8') as f:
        f.write(headers_content)
    print("Successfully created _headers file for Netlify.")
    
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
