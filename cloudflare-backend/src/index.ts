import { DurableObject } from "cloudflare:workers";
import questionBankRaw from "./question_bank.json";

export interface Env {
  GAME_ROOM: DurableObjectNamespace<GameRoom>;
}

interface QuestionBank {
  levels: Record<string, {
    level: number;
    title: string;
    questions: Array<{ id: string; text: string }>;
  }>;
}

const questionBank = questionBankRaw as unknown as QuestionBank;

function getRandomQuestionFromBank(): { level: number; text: string } {
  try {
    const levelsObj = questionBank.levels || {};
    const levelKeys = Object.keys(levelsObj);
    if (levelKeys.length === 0) {
      return { level: 1, text: "(自動選題 - 題庫未載入)" };
    }
    const randomLevelKey = levelKeys[Math.floor(Math.random() * levelKeys.length)];
    const levelData = levelsObj[randomLevelKey];
    const questions = levelData?.questions || [];
    if (questions.length === 0) {
      return { level: Number(randomLevelKey) || 1, text: "(自動選題 - 無題目)" };
    }
    const q = questions[Math.floor(Math.random() * questions.length)];
    return {
      level: Number(randomLevelKey) || 1,
      text: q.text || "(自動選題)"
    };
  } catch {
    return { level: 1, text: "(自動選題 - 題庫錯誤)" };
  }
}

const CORS_HEADERS: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "*",
};

function jsonResponse(data: any, status: number = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json",
      ...CORS_HEADERS,
    },
  });
}

function generateRoomId(): string {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"; // 移除易混淆的 0, O, 1, I
  let result = "";
  for (let i = 0; i < 6; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

// ── Worker 進入點（處理 REST API 與 WebSocket 路由）─────────────────────────────
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const pathname = url.pathname;

    // 處理 CORS 預檢
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }

    // 根目錄與健康檢查
    if (pathname === "/" || pathname === "/health") {
      return jsonResponse({
        status: "ok",
        service: "friends-and-me-backend",
        version: "2.0.0-durable-object",
        timestamp: new Date().toISOString(),
      });
    }

    // REST: 建立房間
    if (pathname === "/create_room" && request.method === "POST") {
      const playerName = url.searchParams.get("player_name") || "Player";
      const roomId = generateRoomId();

      const doId = env.GAME_ROOM.idFromName(roomId);
      const roomStub = env.GAME_ROOM.get(doId);

      await roomStub.fetch(`http://internal/init_room?room_id=${roomId}&captain=${encodeURIComponent(playerName)}`);

      return jsonResponse({
        status: "success",
        room_id: roomId,
        message: `Room ${roomId} created by ${playerName}`,
      });
    }

    // REST: 加入房間（檢查房間是否存在）
    if (pathname === "/join_room" && request.method === "POST") {
      const roomId = (url.searchParams.get("room_id") || "").toUpperCase();
      const playerName = url.searchParams.get("player_name") || "Player";

      if (!roomId) {
        return jsonResponse({ status: "error", message: "請輸入房號" }, 400);
      }

      const doId = env.GAME_ROOM.idFromName(roomId);
      const roomStub = env.GAME_ROOM.get(doId);
      const checkRes = await roomStub.fetch("http://internal/check_room");
      const checkData: any = await checkRes.json();

      if (!checkData.exists) {
        return jsonResponse({
          status: "error",
          message: "房間不存在，請確認房號是否正確。",
        });
      }

      return jsonResponse({
        status: "success",
        room_id: roomId,
        player_name: playerName,
      });
    }

    // REST: 事前檢查房間
    if (pathname.startsWith("/check_room/")) {
      const roomId = pathname.replace("/check_room/", "").toUpperCase();
      if (!roomId) {
        return jsonResponse({ exists: false });
      }

      const doId = env.GAME_ROOM.idFromName(roomId);
      const roomStub = env.GAME_ROOM.get(doId);
      const checkRes = await roomStub.fetch("http://internal/check_room");
      const checkData: any = await checkRes.json();

      return jsonResponse({ exists: !!checkData.exists });
    }

    // REST: 玩家累計戰績（相容端點）
    if (pathname.startsWith("/player/") && pathname.endsWith("/stats")) {
      const segments = pathname.split("/");
      const playerName = decodeURIComponent(segments[2] || "Player");
      return jsonResponse({
        status: "success",
        name: playerName,
        total_guesses: 0,
        correct_guesses: 0,
        total_disclosures: 0,
        recognized_disclosures: 0,
      });
    }

    // WebSocket: 房間即時連線 /ws/{room_id}/{player_name}
    if (pathname.startsWith("/ws/")) {
      if (request.headers.get("Upgrade")?.toLowerCase() !== "websocket") {
        return new Response("Expected WebSocket", { status: 426 });
      }

      const parts = pathname.replace("/ws/", "").split("/");
      const roomId = decodeURIComponent(parts[0] || "").toUpperCase();
      const playerName = decodeURIComponent(parts[1] || "Player");

      if (!roomId || !playerName) {
        return new Response("Missing roomId or playerName", { status: 400 });
      }

      const doId = env.GAME_ROOM.idFromName(roomId);
      const roomStub = env.GAME_ROOM.get(doId);

      // 直接轉發給該房間的 Durable Object
      return roomStub.fetch(request);
    }

    return new Response("Not Found", { status: 404, headers: CORS_HEADERS });
  },
};

// ── GameRoom Durable Object 實作（權威遊戲狀態機）──────────────────────────────
export class GameRoom extends DurableObject<Env> {
  private roomId: string = "";
  private phase: "WAITING" | "SELECTION" | "ANSWERING" | "GUESSING" | "REVELATION" = "WAITING";
  private captain: string = "";
  private isCreated: boolean = false;
  private startedAt: number = Date.now();
  private roundCount: number = 0;
  private currentQuestion: string = "";
  private currentLevel: number = 1;

  // 玩家與連線
  private allPlayers: string[] = []; // 所有加入過的玩家名單（按順序）
  private roomWsMap: Map<string, WebSocket> = new Map(); // 連線中 playerName -> WebSocket
  private disconnectedPlayers: Map<string, { disconnectedAt: number; phase: string }> = new Map();
  private waitingForNextRound: Set<string> = new Set();
  private readyPlayers: Set<string> = new Set();

  // 答題與配對快取
  private roomAnswers: Record<string, string> = {}; // playerName -> answer
  private roomGuesses: Record<string, Record<string, string>> = {}; // guesser -> { targetName: answer }

  // 定時任務
  private phaseTimeoutTimer: any = null;
  private countdownTimer: any = null;
  private disconnectTimers: Map<string, any> = new Map();

  private static RECONNECT_GRACE_SECONDS = 30.0;
  private static DISCONNECT_KICK_SECONDS = 45.0;

  constructor(ctx: DurableObjectState, env: Env) {
    super(ctx, env);
  }

  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    const pathname = url.pathname;

    // 內部指令：初始化房間
    if (pathname === "/init_room") {
      this.roomId = url.searchParams.get("room_id") || "";
      this.captain = decodeURIComponent(url.searchParams.get("captain") || "");
      this.isCreated = true;
      this.phase = "WAITING";
      this.startedAt = Date.now();
      return jsonResponse({ status: "success" });
    }

    // 內部指令：檢查房間存在性
    if (pathname === "/check_room") {
      const activeCount = this.getActivePlayerNames().length;
      const disconnectedCount = this.disconnectedPlayers.size;
      const exists = this.isCreated && (activeCount > 0 || disconnectedCount > 0 || this.phase === "WAITING");
      return jsonResponse({ exists });
    }

    // WebSocket Upgrade 請求
    if (request.headers.get("Upgrade")?.toLowerCase() === "websocket") {
      const parts = pathname.replace("/ws/", "").split("/");
      const roomId = decodeURIComponent(parts[0] || "").toUpperCase();
      const playerName = decodeURIComponent(parts[1] || "Player");

      if (!this.roomId) {
        this.roomId = roomId;
      }
      this.isCreated = true;

      const webSocketPair = new WebSocketPair();
      const [clientWs, serverWs] = Object.values(webSocketPair);

      await this.handleWebSocketConnect(serverWs, playerName);

      return new Response(null, { status: 101, webSocket: clientWs });
    }

    return new Response("Not Found", { status: 404 });
  }

  // ── WebSocket 連線生命週期 ──────────────────────────────────────────────────
  private async handleWebSocketConnect(ws: WebSocket, playerName: string): Promise<void> {
    ws.accept();

    // 檢查是否為重連
    const isReconnect = this.disconnectedPlayers.has(playerName);

    if (isReconnect) {
      const info = this.disconnectedPlayers.get(playerName)!;
      this.disconnectedPlayers.delete(playerName);

      // 清除踢出計時器
      const timer = this.disconnectTimers.get(playerName);
      if (timer) {
        clearTimeout(timer);
        this.disconnectTimers.delete(playerName);
      }

      const elapsed = (Date.now() - info.disconnectedAt) / 1000;
      const seamless = (elapsed <= GameRoom.RECONNECT_GRACE_SECONDS && this.phase === info.phase);

      if (!seamless && this.phase !== "WAITING" && this.phase !== "SELECTION") {
        this.waitingForNextRound.add(playerName);
      }
    } else {
      // 全新加入
      if (!this.captain) {
        this.captain = playerName;
      }
      if (!this.allPlayers.includes(playerName)) {
        this.allPlayers.push(playerName);
      }
    }

    // 綁定連線
    this.roomWsMap.set(playerName, ws);

    // 廣播更新後的名單
    this.broadcastPlayerListUpdated();

    // 若為重連，發送 reconnect_status
    if (isReconnect) {
      const duration = (this.phase === "REVELATION" || this.phase === "ANSWERING") ? 120 : 60;
      const remaining = Math.max(0, duration - Math.floor((Date.now() - this.startedAt) / 1000));

      this.sendToPlayer(playerName, {
        event: "reconnect_status",
        current_phase: this.phase,
        captain: this.captain,
        remaining_seconds: remaining,
        message: "重連成功！等待本輪結束後一起加入下一輪。",
      });
    }

    // 監聽訊息
    ws.addEventListener("message", async (event: MessageEvent) => {
      try {
        const raw = typeof event.data === "string" ? event.data : new TextDecoder().decode(event.data as ArrayBuffer);
        const data = JSON.parse(raw);
        await this.handleGameEvent(playerName, data);
      } catch (err) {
        console.error(`[WebSocket Error in ${this.roomId}]`, err);
      }
    });

    // 監聽關閉與異常
    const onCloseOrError = () => {
      this.handlePlayerDisconnect(playerName, ws);
    };

    ws.addEventListener("close", onCloseOrError);
    ws.addEventListener("error", onCloseOrError);
  }

  private handlePlayerDisconnect(playerName: string, ws: WebSocket): void {
    const currentWs = this.roomWsMap.get(playerName);
    // 若該玩家已經由另一條新連線取代，則此處為舊殭屍連線，忽略
    if (currentWs && currentWs !== ws) {
      return;
    }

    this.roomWsMap.delete(playerName);
    this.disconnectedPlayers.set(playerName, {
      disconnectedAt: Date.now(),
      phase: this.phase,
    });

    // 啟動 45 秒斷線判定計時器
    const timer = setTimeout(() => {
      this.kickPlayerAfterTimeout(playerName);
    }, GameRoom.DISCONNECT_KICK_SECONDS * 1000);
    this.disconnectTimers.set(playerName, timer);

    // 即時廣播名單更新
    this.broadcastPlayerListUpdated();

    // 檢查階段是否可推進
    this.checkPhaseProgressAfterDisconnect();

    // 若房間已完全無人
    if (this.getActivePlayerNames().length === 0 && this.disconnectedPlayers.size === 0) {
      this.cleanupRoom();
    }
  }

  private kickPlayerAfterTimeout(playerName: string): void {
    if (!this.disconnectedPlayers.has(playerName)) {
      return;
    }

    this.disconnectedPlayers.delete(playerName);
    this.disconnectTimers.delete(playerName);
    this.allPlayers = this.allPlayers.filter(p => p !== playerName);

    if (this.captain === playerName) {
      this.rotateCaptain();
    }

    this.broadcastPlayerListUpdated();
    this.checkPhaseProgressAfterDisconnect();

    if (this.getActivePlayerNames().length === 0 && this.disconnectedPlayers.size === 0) {
      this.cleanupRoom();
    }
  }

  // ── 遊戲事件處理 ────────────────────────────────────────────────────────────
  private async handleGameEvent(playerName: string, data: any): Promise<void> {
    const event = data?.event;

    // 房主開始遊戲
    if (event === "start_game") {
      this.phase = "SELECTION";
      this.startedAt = Date.now();
      this.broadcast({
        event: "phase_changed",
        new_phase: "SELECTION",
        captain: this.captain,
        remaining_seconds: 60,
      });
      this.startPhaseTimeout("SELECTION", 60);
      return;
    }

    // 隊長選題
    if (event === "topic_selected") {
      // 階段守衛：只在 SELECTION 階段接受選題
      if (this.phase !== "SELECTION") return;

      this.roomAnswers = {};
      this.roomGuesses = {};
      this.currentQuestion = data.question || "";
      this.currentLevel = Number(data.level) || 1;

      this.phase = "ANSWERING";
      this.startedAt = Date.now();

      this.broadcast({
        event: "phase_changed",
        new_phase: "ANSWERING",
        level: this.currentLevel,
        question: this.currentQuestion,
        remaining_seconds: 120,
      });

      this.cancelPhaseTimeout();
      this.startPhaseTimeout("ANSWERING", 120);
      return;
    }

    // 提交答案
    if (event === "answer_submitted") {
      // 階段守衛：只在 ANSWERING 階段接受答案
      if (this.phase !== "ANSWERING") return;

      const answer = data.answer || "";
      this.roomAnswers[playerName] = answer;

      const eligible = this.getEligiblePlayerNames();
      this.broadcast({
        event: "player_submitted_status",
        player: playerName,
        submitted: Object.keys(this.roomAnswers).length,
        total: eligible.length,
      });

      // 檢查全員是否已提交
      const allDone = eligible.length > 0 && eligible.every(name => name in this.roomAnswers);
      if (allDone) {
        this.cancelPhaseTimeout();
        this.phase = "GUESSING";
        this.startedAt = Date.now();

        this.broadcast({
          event: "phase_changed",
          new_phase: "GUESSING",
          answers: this.roomAnswers,
          remaining_seconds: 60,
        });

        this.startPhaseTimeout("GUESSING", 60);
      }
      return;
    }

    // 提交配對
    if (event === "guesses_submitted") {
      // 階段守衛：只在 GUESSING 階段接受配對
      if (this.phase !== "GUESSING") return;

      const guesses = data.guesses || {};
      this.roomGuesses[playerName] = guesses;

      const eligible = this.getEligiblePlayerNames();
      const allDone = eligible.length > 0 && eligible.every(name => name in this.roomGuesses);

      if (allDone) {
        this.cancelPhaseTimeout();
        this.phase = "REVELATION";
        this.startedAt = Date.now();

        this.broadcast({
          event: "phase_changed",
          new_phase: "REVELATION",
          all_guesses: this.roomGuesses,
          all_answers: this.roomAnswers,
          player_stats: {}, // 前端由 local 即時計算
          remaining_seconds: 120,
        });

        this.startPhaseTimeout("REVELATION", 120);
      }
      return;
    }

    // 準備進入下一輪
    if (event === "ready_for_next_round") {
      this.readyPlayers.add(playerName);

      const eligible = this.getEligiblePlayerNames();
      const readyCount = Array.from(this.readyPlayers).filter(p => eligible.includes(p)).length;
      const totalCount = eligible.length;

      this.broadcast({
        event: "next_round_status",
        ready: readyCount,
        total: totalCount,
      });

      if (readyCount >= totalCount && totalCount > 0) {
        // 所有人就緒，立即推進
        this.cancelCountdown();
        this.cancelPhaseTimeout();

        const newCaptain = this.rotateCaptain();
        this.phase = "SELECTION";
        this.startedAt = Date.now();

        this.broadcast({
          event: "phase_changed",
          new_phase: "SELECTION",
          captain: newCaptain,
          players: this.getActivePlayerNames(),
          remaining_seconds: 60,
        });

        this.startPhaseTimeout("SELECTION", 60);
      } else if (readyCount >= totalCount - 1 && totalCount > 1) {
        // 剩最後一人未 ready，啟動 10 秒倒數
        this.startNextRoundCountdown();
      }
      return;
    }

    // 相容事件：next_round
    if (event === "next_round") {
      this.cancelCountdown();
      this.cancelPhaseTimeout();

      const newCaptain = this.rotateCaptain();
      this.phase = "SELECTION";
      this.startedAt = Date.now();

      this.broadcast({
        event: "phase_changed",
        new_phase: "SELECTION",
        captain: newCaptain,
        players: this.getActivePlayerNames(),
        remaining_seconds: 60,
      });

      this.startPhaseTimeout("SELECTION", 60);
      return;
    }

    // 主動離開房間
    if (event === "leave_room") {
      this.leaveRoom(playerName);
      return;
    }
  }

  // ── 階段超時推進與倒數任務 ──────────────────────────────────────────────────
  private startPhaseTimeout(expectedPhase: string, seconds: number): void {
    this.cancelPhaseTimeout();
    this.phaseTimeoutTimer = setTimeout(() => {
      this.runPhaseTimeout(expectedPhase, seconds);
    }, seconds * 1000);
  }

  private cancelPhaseTimeout(): void {
    if (this.phaseTimeoutTimer) {
      clearTimeout(this.phaseTimeoutTimer);
      this.phaseTimeoutTimer = null;
    }
  }

  private runPhaseTimeout(expectedPhase: string, seconds: number): void {
    if (this.phase !== expectedPhase) {
      return;
    }

    const active = this.getActivePlayerNames();
    if (active.length === 0) {
      this.cleanupRoom();
      return;
    }

    if (this.phase === "SELECTION") {
      // 超時自動選題
      const { level, text } = getRandomQuestionFromBank();
      this.currentLevel = level;
      this.currentQuestion = text;
      this.roomAnswers = {};
      this.roomGuesses = {};

      this.phase = "ANSWERING";
      this.startedAt = Date.now();

      this.broadcast({
        event: "phase_changed",
        new_phase: "ANSWERING",
        level: this.currentLevel,
        question: this.currentQuestion,
        remaining_seconds: 120,
      });

      this.startPhaseTimeout("ANSWERING", 120);
    } else if (this.phase === "ANSWERING") {
      // 未提交者自動補「不回答」
      const eligible = this.getEligiblePlayerNames();
      for (const name of eligible) {
        if (!this.roomAnswers[name]) {
          this.roomAnswers[name] = "不回答";
        }
      }

      this.phase = "GUESSING";
      this.startedAt = Date.now();

      this.broadcast({
        event: "phase_changed",
        new_phase: "GUESSING",
        answers: this.roomAnswers,
        remaining_seconds: 60,
      });

      this.startPhaseTimeout("GUESSING", 60);
    } else if (this.phase === "GUESSING") {
      // 未提交者自動補空配對
      const eligible = this.getEligiblePlayerNames();
      for (const name of eligible) {
        if (!this.roomGuesses[name]) {
          this.roomGuesses[name] = {};
        }
      }

      this.phase = "REVELATION";
      this.startedAt = Date.now();

      this.broadcast({
        event: "phase_changed",
        new_phase: "REVELATION",
        all_guesses: this.roomGuesses,
        all_answers: this.roomAnswers,
        player_stats: {},
        remaining_seconds: 120,
      });

      this.startPhaseTimeout("REVELATION", 120);
    } else if (this.phase === "REVELATION") {
      this.cancelCountdown();
      const newCaptain = this.rotateCaptain();

      this.phase = "SELECTION";
      this.startedAt = Date.now();

      this.broadcast({
        event: "phase_changed",
        new_phase: "SELECTION",
        captain: newCaptain,
        players: this.getActivePlayerNames(),
        remaining_seconds: 60,
      });

      this.startPhaseTimeout("SELECTION", 60);
    }
  }

  private startNextRoundCountdown(): void {
    if (this.countdownTimer) return;

    let secondsLeft = 10;
    this.countdownTimer = setInterval(() => {
      this.broadcast({
        event: "next_round_countdown",
        seconds: secondsLeft,
      });

      secondsLeft--;

      if (secondsLeft < 0) {
        this.cancelCountdown();
        this.cancelPhaseTimeout();

        const newCaptain = this.rotateCaptain();
        this.phase = "SELECTION";
        this.startedAt = Date.now();

        this.broadcast({
          event: "phase_changed",
          new_phase: "SELECTION",
          captain: newCaptain,
          players: this.getActivePlayerNames(),
          remaining_seconds: 60,
        });

        this.startPhaseTimeout("SELECTION", 60);
      }
    }, 1000);
  }

  private cancelCountdown(): void {
    if (this.countdownTimer) {
      clearInterval(this.countdownTimer);
      this.countdownTimer = null;
    }
  }

  // ── 輔助方法 ────────────────────────────────────────────────────────────────
  private getActivePlayerNames(): string[] {
    return Array.from(this.roomWsMap.keys());
  }

  private getEligiblePlayerNames(): string[] {
    const active = this.getActivePlayerNames();
    return active.filter(name => !this.waitingForNextRound.has(name));
  }

  private rotateCaptain(): string {
    const active = this.getActivePlayerNames();
    if (active.length === 0) return "";

    const idx = active.indexOf(this.captain);
    if (idx !== -1) {
      this.captain = active[(idx + 1) % active.length];
    } else {
      this.captain = active[0];
    }

    this.waitingForNextRound.clear();
    this.readyPlayers.clear();
    this.roomAnswers = {};
    this.roomGuesses = {};

    return this.captain;
  }

  private checkPhaseProgressAfterDisconnect(): void {
    const eligible = this.getEligiblePlayerNames();

    if (this.phase === "ANSWERING") {
      if (eligible.length > 0 && eligible.every(name => name in this.roomAnswers)) {
        this.cancelPhaseTimeout();
        this.phase = "GUESSING";
        this.startedAt = Date.now();

        this.broadcast({
          event: "phase_changed",
          new_phase: "GUESSING",
          answers: this.roomAnswers,
          remaining_seconds: 60,
        });

        this.startPhaseTimeout("GUESSING", 60);
      }
    } else if (this.phase === "GUESSING") {
      if (eligible.length > 0 && eligible.every(name => name in this.roomGuesses)) {
        this.cancelPhaseTimeout();
        this.phase = "REVELATION";
        this.startedAt = Date.now();

        this.broadcast({
          event: "phase_changed",
          new_phase: "REVELATION",
          all_guesses: this.roomGuesses,
          all_answers: this.roomAnswers,
          player_stats: {},
          remaining_seconds: 120,
        });

        this.startPhaseTimeout("REVELATION", 120);
      }
    } else if (this.phase === "REVELATION") {
      const readyCount = Array.from(this.readyPlayers).filter(p => eligible.includes(p)).length;
      const totalCount = eligible.length;

      if (totalCount > 0) {
        this.broadcast({
          event: "next_round_status",
          ready: readyCount,
          total: totalCount,
        });

        if (readyCount >= totalCount) {
          this.cancelCountdown();
          this.cancelPhaseTimeout();

          const newCaptain = this.rotateCaptain();
          this.phase = "SELECTION";
          this.startedAt = Date.now();

          this.broadcast({
            event: "phase_changed",
            new_phase: "SELECTION",
            captain: newCaptain,
            players: this.getActivePlayerNames(),
            remaining_seconds: 60,
          });

          this.startPhaseTimeout("SELECTION", 60);
        } else if (readyCount >= totalCount - 1 && totalCount > 1) {
          this.startNextRoundCountdown();
        }
      }
    }
  }

  private leaveRoom(playerName: string): void {
    const ws = this.roomWsMap.get(playerName);
    if (ws) {
      try {
        ws.close();
      } catch {}
    }
    this.roomWsMap.delete(playerName);
    this.allPlayers = this.allPlayers.filter(p => p !== playerName);
    this.disconnectedPlayers.delete(playerName);

    if (this.captain === playerName) {
      this.rotateCaptain();
    }

    this.broadcastPlayerListUpdated();

    if (this.getActivePlayerNames().length === 0) {
      this.cleanupRoom();
    }
  }

  private cleanupRoom(): void {
    this.cancelPhaseTimeout();
    this.cancelCountdown();
    for (const timer of this.disconnectTimers.values()) {
      clearTimeout(timer);
    }
    this.disconnectTimers.clear();

    this.roomWsMap.clear();
    this.allPlayers = [];
    this.disconnectedPlayers.clear();
    this.waitingForNextRound.clear();
    this.readyPlayers.clear();
    this.roomAnswers = {};
    this.roomGuesses = {};
    this.isCreated = false;
    this.phase = "WAITING";
  }

  private broadcastPlayerListUpdated(): void {
    this.broadcast({
      event: "player_list_updated",
      players: this.getActivePlayerNames(),
    });
  }

  private broadcast(message: any): void {
    const payload = JSON.stringify(message);
    for (const ws of this.roomWsMap.values()) {
      try {
        ws.send(payload);
      } catch {}
    }
  }

  private sendToPlayer(playerName: string, message: any): void {
    const ws = this.roomWsMap.get(playerName);
    if (ws) {
      try {
        ws.send(JSON.stringify(message));
      } catch {}
    }
  }
}

