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
