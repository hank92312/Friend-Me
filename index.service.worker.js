// 自毀式 Service Worker：
// 先前部署的版本註冊過 PWA service worker，這個檔案取代它，
// 清除所有快取並解除註冊，讓瀏覽器改抓最新版本。
self.addEventListener("install", () => {
	self.skipWaiting();
});
self.addEventListener("activate", async () => {
	const keys = await caches.keys();
	await Promise.all(keys.map((k) => caches.delete(k)));
	await self.registration.unregister();
	const clients = await self.clients.matchAll({ type: "window" });
	clients.forEach((c) => c.navigate(c.url));
});
