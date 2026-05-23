import subprocess
import os
import sys

def main():
    godot_path = r"C:\Users\hank9\Downloads\Godot_v4.6.2-stable_win64.exe\Godot_v4.6.2-stable_win64_console.exe"
    project_path = r"C:\FriendAndMe\friendAndme"
    export_output = r"C:\FriendAndMe\build_web\index.html"
    
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
        
    # 定義要插入的 fetch 攔截器
    patch_code = """<script>
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
			document.write('<script src="index.js?v=' + Date.now() + '"><\\/script>');
		</script>"""

    # 替換 <script src="index.js"></script>
    target = '<script src="index.js"></script>'
    if target in html:
        html = html.replace(target, patch_code)
        print("Successfully replaced <script src=\"index.js\"></script> with cache-busting script.")
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
						console.log("[Ad Controller] Requesting CrazyGames Interstitial...");
						window.CrazyGames.SDK.ad.requestAd("interstitial", {
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
    
    with open(export_output, 'w', encoding='utf-8') as f:
        f.write(html)
        
    print("=== Step 3: Creating _headers file for Netlify ===")
    headers_path = os.path.join(os.path.dirname(export_output), "_headers")
    headers_content = """/*
  Cross-Origin-Opener-Policy: same-origin
  Cross-Origin-Embedder-Policy: require-corp
"""
    with open(headers_path, 'w', encoding='utf-8') as f:
        f.write(headers_content)
    print("Successfully created _headers file for Netlify.")
        
    print("=== Patching complete! ===")

if __name__ == '__main__':
    main()
