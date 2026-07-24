/* ============================================================
   Connect 4 — Browser Game Client
   Canvas rendering + REST API integration + Multi-language i18n
   ============================================================ */

(() => {
  "use strict";

  /* ---- Constants (match backend / constants.py) ---- */
  const N_ROWS = 6;
  const N_COLS = 7;
  const MACHINE_PIECE = 1;
  const HUMAN_PIECE = 2;

  /* ---- Colours ---- */
  const COLORS = {
    bg: "#141624",
    board: "#1e3c96",
    cellEmpty: "#0f111e",
    player1: "#e63946",
    player2: "#ffc832",
    white: "#ffffff",
    win: "#32cd64",
    lose: "#e63946",
    draw: "#b4b4c8",
    hoverGhost: "rgba(255, 200, 50, 0.35)",
  };

  /* ---- Translations (i18n) ---- */
  const TRANSLATIONS = {
    en: {
      appTitle: 'Connect <span class="accent">4</span>',
      subtitle: "Challenge the RL Agent",
      inputLabel: "Enter your nickname",
      placeholder: "e.g. Mario",
      btnPlay: "Play",
      btnLeaderboard: "Leaderboard",
      btnAbout: "About",
      vs: "vs",
      machine: "Machine",
      yourTurn: "Your turn",
      starting: "Starting...",
      thinking: "Machine is thinking...",
      errStart: "Error starting game",
      errMove: "Error — try again",
      humanWin: "{name} wins!",
      machineWin: "Machine wins!",
      draw: "It's a draw!",
      playAgain: "Play again?",
      btnYes: "Yes",
      btnNo: "No",
      leaderboardTitle: "Top 10 Leaderboard",
      thRank: "Rank",
      thPlayer: "Player",
      thMatches: "Matches",
      thWinRate: "Win Rate",
      userRankFooter: "Your Rank: #{rank}  |  {name} ({winRate}% Win Rate)",
      btnClose: "Close",
      aboutText:
        "A Connect 4 game built with a custom reinforcement learning agent. Created for the 2024 Reinforcement Learning course at Universidad de los Andes, this project explores the application of the Q-learning algorithm in strategic gameplay.",
      aboutAuthor:
        'Author: <a href="https://github.com/mfreyeso" target="_blank" rel="noopener noreferrer">Mario Reyes Ojeda</a>',
      langBtn: "🌐 ES",
    },
    es: {
      appTitle: 'Conecta <span class="accent">4</span>',
      subtitle: "Desafía al agente de RL",
      inputLabel: "Escribe tu apodo",
      placeholder: "ej. Mario",
      btnPlay: "Jugar",
      btnLeaderboard: "Tabla de Clasificación",
      btnAbout: "Acerca de",
      vs: "vs",
      machine: "Máquina",
      yourTurn: "Tu turno",
      starting: "Iniciando...",
      thinking: "La máquina está pensando...",
      errStart: "Error al iniciar el juego",
      errMove: "Error — intenta de nuevo",
      humanWin: "¡{name} ganó!",
      machineWin: "¡La máquina ganó!",
      draw: "¡Es un empate!",
      playAgain: "¿Jugar de nuevo?",
      btnYes: "Sí",
      btnNo: "No",
      leaderboardTitle: "Tabla de Clasificación - Top 10",
      thRank: "Posición",
      thPlayer: "Jugador",
      thMatches: "Partidas",
      thWinRate: "% Victorias",
      userRankFooter: "Tu Posición: #{rank}  |  {name} ({winRate}% Victorias)",
      btnClose: "Cerrar",
      aboutText:
        "Un juego de Conecta 4 creado con un agente de aprendizaje por refuerzo personalizado. Creado para el curso de Aprendizaje por Refuerzo de 2024 en la Universidad de los Andes, este proyecto explora la aplicación del algoritmo Q-learning en juegos de estrategia.",
      aboutAuthor:
        'Autor: <a href="https://github.com/mfreyeso" target="_blank" rel="noopener noreferrer">Mario Reyes Ojeda</a>',
      langBtn: "🌐 EN",
    },
  };

  /* ---- Detect Browser Language ---- */
  const userLang = (navigator.language || (navigator.languages && navigator.languages[0]) || "en").toLowerCase();
  let currentLang = userLang.startsWith("es") ? "es" : "en";

  /* ---- Sizing & Utils ---- */
  function squareSize() {
    return Math.max(40, Math.min(85, Math.floor((window.innerWidth - 60) / N_COLS)));
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  /* ---- DOM refs ---- */
  const $startScreen = document.getElementById("screen-start");
  const $gameScreen = document.getElementById("screen-game");
  const $modalOverlay = document.getElementById("modal-overlay");
  const $leaderboardOverlay = document.getElementById("leaderboard-overlay");
  const $nicknameIn = document.getElementById("nickname-input");
  const $btnPlay = document.getElementById("btn-play");
  const $btnLeaderboard = document.getElementById("btn-leaderboard");
  const $btnLeaderboardClose = document.getElementById("btn-leaderboard-close");
  const $btnLangToggle = document.getElementById("btn-lang-toggle");
  const $humanName = document.getElementById("human-name");
  const $humanScore = document.getElementById("human-score");
  const $machineScore = document.getElementById("machine-score");
  const $canvas = document.getElementById("board-canvas");
  const $turnInd = document.getElementById("turn-indicator");
  const $modalResult = document.getElementById("modal-result");
  const $modalScores = document.getElementById("modal-scores");
  const $btnYes = document.getElementById("btn-yes");
  const $btnNo = document.getElementById("btn-no");
  const $btnAbout = document.getElementById("btn-about");
  const $aboutOverlay = document.getElementById("about-overlay");
  const $btnAboutClose = document.getElementById("btn-about-close");
  const ctx = $canvas.getContext("2d");

  /* ---- Game state ---- */
  let sessionId = null;
  let nickname = "";
  let board = [];     // [row][col], row 0 = bottom
  let hoverCol = -1;
  let locked = false;  // true while waiting for API or animation
  let gameFinished = false;
  let winHighlightTimer = null;  // animation frame ID for pulsing glow
  let checkDebounceTimer = null;
  let lastModalResult = null;
  let lastHumanScore = 0;
  let lastMachineScore = 0;

  /* ============================================================
     Language / i18n Controller
     ============================================================ */
  function setLanguage(lang) {
    if (!TRANSLATIONS[lang]) return;
    currentLang = lang;
    document.documentElement.lang = lang;

    const t = TRANSLATIONS[lang];

    // Update elements with data-i18n
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (t[key] !== undefined) {
        el.innerHTML = t[key];
      }
    });

    // Update input placeholders
    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const key = el.getAttribute("data-i18n-placeholder");
      if (t[key] !== undefined) {
        el.placeholder = t[key];
      }
    });

    // Update language toggle button
    if ($btnLangToggle) {
      $btnLangToggle.textContent = t.langBtn;
    }

    // Refresh dynamic texts if currently visible
    if ($modalOverlay.classList.contains("visible") && lastModalResult) {
      showModal(lastModalResult, lastHumanScore, lastMachineScore);
    }
    if (!$turnInd.classList.contains("thinking") && !gameFinished && $gameScreen.classList.contains("active")) {
      $turnInd.textContent = t.yourTurn;
    }
  }

  /* ============================================================
     Screen management
     ============================================================ */
  function showScreen(name) {
    $startScreen.classList.toggle("active", name === "start");
    $gameScreen.classList.toggle("active", name === "game");
    if (name === "start") $nicknameIn.focus();
  }

  function showModal(result, humanScore, machineScore) {
    lastModalResult = result;
    lastHumanScore = humanScore;
    lastMachineScore = machineScore;

    const t = TRANSLATIONS[currentLang];
    let msg, cls;

    if (result === "human_win") {
      msg = t.humanWin.replace("{name}", nickname);
      cls = "win";
    } else if (result === "machine_win") {
      msg = t.machineWin;
      cls = "lose";
    } else {
      msg = t.draw;
      cls = "draw";
    }

    $modalResult.textContent = msg;
    $modalResult.className = "modal-result " + cls;
    $modalScores.textContent = `${nickname}: ${humanScore}  —  ${t.machine}: ${machineScore}`;
    $modalOverlay.classList.add("visible");
  }

  function hideModal() { $modalOverlay.classList.remove("visible"); }

  /* ============================================================
     Player Profile & Leaderboard API
     ============================================================ */
  async function checkPlayerProfile(name) {
    if (!name || !name.trim()) {
      $btnLeaderboard.style.display = "none";
      return;
    }
    try {
      const res = await fetch(`/api/players/${encodeURIComponent(name.trim())}`);
      if (res.ok) {
        const data = await res.json();
        if (data.can_view_leaderboard) {
          $btnLeaderboard.style.display = "inline-block";
        } else {
          $btnLeaderboard.style.display = "none";
        }
      }
    } catch (e) {
      $btnLeaderboard.style.display = "none";
    }
  }

  async function showLeaderboard(name) {
    const user = name || nickname || "";
    const t = TRANSLATIONS[currentLang];
    try {
      const res = await fetch(`/api/leaderboard?username=${encodeURIComponent(user)}`);
      if (!res.ok) return;
      const data = await res.json();

      const $tbody = document.getElementById("leaderboard-tbody");
      const $footer = document.getElementById("leaderboard-footer");
      $tbody.innerHTML = "";
      $footer.textContent = "";

      data.top_players.forEach((p, idx) => {
        const tr = document.createElement("tr");
        const isUser = user && p.username.toLowerCase() === user.trim().toLowerCase();
        if (isUser) tr.classList.add("user-row");

        tr.innerHTML = `
          <td>#${idx + 1}</td>
          <td>${escapeHtml(p.username)}</td>
          <td>${p.total_games}</td>
          <td>${p.win_rate.toFixed(1)}%</td>
        `;
        $tbody.appendChild(tr);
      });

      if (data.user_rank && data.user_rank.rank > 10) {
        $footer.textContent = t.userRankFooter
          .replace("{rank}", data.user_rank.rank)
          .replace("{name}", data.user_rank.username)
          .replace("{winRate}", data.user_rank.win_rate.toFixed(1));
      }

      $leaderboardOverlay.classList.add("visible");
    } catch (err) {
      console.error("Failed to load leaderboard:", err);
    }
  }

  /* ============================================================
     Canvas rendering
     ============================================================ */
  function setupCanvas() {
    const SQ = squareSize();
    $canvas.width = N_COLS * SQ;
    $canvas.height = (N_ROWS + 1) * SQ;  // +1 for hover row at top
    drawBoard();
  }

  function drawBoard(highlightCells, highlightPhase) {
    const SQ = squareSize();
    const R = SQ / 2 - 5;

    ctx.fillStyle = COLORS.board;
    ctx.fillRect(0, 0, N_COLS * SQ, SQ);

    if (hoverCol >= 0 && !locked && !gameFinished) {
      ctx.beginPath();
      ctx.arc(hoverCol * SQ + SQ / 2, SQ / 2, R, 0, Math.PI * 2);
      ctx.fillStyle = COLORS.hoverGhost;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(hoverCol * SQ + SQ / 2, SQ / 2, R, 0, Math.PI * 2);
      ctx.fillStyle = COLORS.player2;
      ctx.globalAlpha = 0.7;
      ctx.fill();
      ctx.globalAlpha = 1;
    }

    for (let r = 0; r < N_ROWS; r++) {
      for (let c = 0; c < N_COLS; c++) {
        const x = c * SQ;
        const y = (N_ROWS - r) * SQ;

        ctx.fillStyle = COLORS.board;
        ctx.fillRect(x, y, SQ, SQ);

        ctx.beginPath();
        ctx.arc(x + SQ / 2, y + SQ / 2, R, 0, Math.PI * 2);

        const piece = board[r] ? board[r][c] : 0;
        if (piece === MACHINE_PIECE) ctx.fillStyle = COLORS.player1;
        else if (piece === HUMAN_PIECE) ctx.fillStyle = COLORS.player2;
        else ctx.fillStyle = COLORS.cellEmpty;

        if (highlightCells && highlightCells.some(([hr, hc]) => hr === r && hc === c)) {
          const pulse = highlightPhase !== undefined
            ? 22 + 16 * Math.sin(highlightPhase)
            : 28;
          ctx.shadowColor = ctx.fillStyle;
          ctx.shadowBlur = pulse;
        }

        ctx.fill();
        ctx.shadowBlur = 0;
      }
    }
  }

  function startWinHighlight(winningCells, state, durationMs) {
    if (winHighlightTimer) cancelAnimationFrame(winHighlightTimer);
    const t0 = performance.now();

    function pulse(now) {
      const elapsed = now - t0;
      const phase = (elapsed / 200);
      drawBoard(winningCells, phase);

      if (elapsed < durationMs) {
        winHighlightTimer = requestAnimationFrame(pulse);
      } else {
        winHighlightTimer = null;
        showModal(state.result, state.human_score, state.machine_score);
      }
    }

    winHighlightTimer = requestAnimationFrame(pulse);
  }

  function animateDrop(col, targetRow, piece, callback) {
    const SQ = squareSize();
    const R = SQ / 2 - 5;
    const color = piece === MACHINE_PIECE ? COLORS.player1 : COLORS.player2;

    const startY = SQ / 2;
    const endY = (N_ROWS - targetRow) * SQ + SQ / 2;
    const duration = 250 + (N_ROWS - targetRow) * 35;
    const t0 = performance.now();

    function frame(now) {
      const elapsed = now - t0;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const y = startY + (endY - startY) * eased;

      drawBoard();

      ctx.beginPath();
      ctx.arc(col * SQ + SQ / 2, y, R, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();

      if (progress < 1) {
        requestAnimationFrame(frame);
      } else {
        if (!board[targetRow]) board[targetRow] = new Array(N_COLS).fill(0);
        board[targetRow][col] = piece;
        drawBoard();
        if (callback) callback();
      }
    }

    requestAnimationFrame(frame);
  }

  /* ============================================================
     API helpers
     ============================================================ */
  async function apiNewGame() {
    const res = await fetch("/api/game/new", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nickname, session_id: sessionId }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  async function apiMove(column) {
    const res = await fetch(`/api/game/${sessionId}/move`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ column }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  /* ============================================================
     Game flow
     ============================================================ */
  async function startNewGame() {
    const t = TRANSLATIONS[currentLang];
    hideModal();
    if (winHighlightTimer) { cancelAnimationFrame(winHighlightTimer); winHighlightTimer = null; }
    gameFinished = false;
    locked = true;
    $turnInd.textContent = t.starting;
    $turnInd.classList.remove("thinking");

    try {
      const data = await apiNewGame();
      sessionId = data.session_id;
      board = data.state.board;
      $humanName.textContent = nickname;
      $humanScore.textContent = data.state.human_score;
      $machineScore.textContent = data.state.machine_score;

      showScreen("game");
      setupCanvas();

      if (data.state.machine_move !== null && data.state.machine_move !== undefined) {
        const mCol = data.state.machine_move;
        const mRow = findPieceRow(board, mCol, MACHINE_PIECE);
        board[mRow][mCol] = 0;
        drawBoard();
        animateDrop(mCol, mRow, MACHINE_PIECE, () => {
          locked = false;
          $turnInd.textContent = t.yourTurn;
        });
      } else {
        locked = false;
        $turnInd.textContent = t.yourTurn;
      }
    } catch (err) {
      console.error("Failed to start game:", err);
      $turnInd.textContent = t.errStart;
      locked = false;
    }
  }

  function findPieceRow(boardData, col, piece) {
    for (let r = N_ROWS - 1; r >= 0; r--) {
      if (boardData[r] && boardData[r][col] === piece) return r;
    }
    return 0;
  }

  function findNextOpenRow(col) {
    for (let r = 0; r < N_ROWS; r++) {
      if (!board[r] || board[r][col] === 0) return r;
    }
    return -1;
  }

  async function humanMove(col) {
    if (locked || gameFinished) return;
    if (col < 0 || col >= N_COLS) return;

    const t = TRANSLATIONS[currentLang];
    const targetRow = findNextOpenRow(col);
    if (targetRow < 0) return;

    locked = true;
    $turnInd.textContent = "";

    animateDrop(col, targetRow, HUMAN_PIECE, async () => {
      $turnInd.textContent = t.thinking;
      $turnInd.classList.add("thinking");

      try {
        const state = await apiMove(col);
        board = state.board;

        if (state.result) {
          gameFinished = true;
          $humanScore.textContent = state.human_score;
          $machineScore.textContent = state.machine_score;

          if (state.result === "human_win") {
            locked = false;
            $turnInd.classList.remove("thinking");
            $turnInd.textContent = "";
            startWinHighlight(state.winning_cells, state, 3000);
            return;
          }
        }

        if (state.machine_move !== null && state.machine_move !== undefined) {
          const mCol = state.machine_move;
          const mRow = findPieceRow(board, mCol, MACHINE_PIECE);
          board[mRow][mCol] = 0;
          drawBoard();
          animateDrop(mCol, mRow, MACHINE_PIECE, () => {
            $turnInd.classList.remove("thinking");

            if (state.finished) {
              gameFinished = true;
              $humanScore.textContent = state.human_score;
              $machineScore.textContent = state.machine_score;
              locked = false;
              $turnInd.textContent = "";
              if (state.result === "machine_win" || state.result === "human_win") {
                startWinHighlight(state.winning_cells, state, 3000);
              } else {
                drawBoard();
                setTimeout(() => showModal(state.result, state.human_score, state.machine_score), 500);
              }
            } else {
              locked = false;
              $turnInd.textContent = t.yourTurn;
              drawBoard();
            }
          });
        } else {
          $turnInd.classList.remove("thinking");
          drawBoard();
          locked = false;
          if (state.finished) {
            $turnInd.textContent = "";
            setTimeout(() => showModal(state.result, state.human_score, state.machine_score), 600);
          }
        }
      } catch (err) {
        console.error("Move failed:", err);
        $turnInd.textContent = t.errMove;
        $turnInd.classList.remove("thinking");
        locked = false;
      }
    });
  }

  /* ============================================================
     Event listeners
     ============================================================ */

  /* -- Language toggle -- */
  if ($btnLangToggle) {
    $btnLangToggle.addEventListener("click", () => {
      const nextLang = currentLang === "en" ? "es" : "en";
      setLanguage(nextLang);
    });
  }

  /* -- Start screen -- */
  $nicknameIn.addEventListener("input", () => {
    const val = $nicknameIn.value.trim();
    $btnPlay.disabled = !val;

    if (checkDebounceTimer) clearTimeout(checkDebounceTimer);
    checkDebounceTimer = setTimeout(() => {
      checkPlayerProfile(val);
    }, 300);
  });

  $nicknameIn.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && $nicknameIn.value.trim()) {
      nickname = $nicknameIn.value.trim();
      startNewGame();
    }
  });

  $btnAbout.addEventListener("click", () => {
    $aboutOverlay.classList.add("visible");
  });
  $btnAboutClose.addEventListener("click", () => {
    $aboutOverlay.classList.remove("visible");
  });

  $btnLeaderboard.addEventListener("click", () => {
    showLeaderboard($nicknameIn.value.trim() || nickname);
  });

  $btnLeaderboardClose.addEventListener("click", () => {
    $leaderboardOverlay.classList.remove("visible");
    showScreen("start");
    checkPlayerProfile($nicknameIn.value.trim() || nickname);
  });

  $btnPlay.addEventListener("click", () => {
    if ($nicknameIn.value.trim()) {
      nickname = $nicknameIn.value.trim();
      startNewGame();
    }
  });

  /* -- Canvas interactions -- */
  $canvas.addEventListener("mousemove", (e) => {
    const SQ = squareSize();
    const rect = $canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    hoverCol = Math.floor(x / SQ);
    if (hoverCol < 0 || hoverCol >= N_COLS) hoverCol = -1;
    if (!locked && !gameFinished) drawBoard();
  });

  $canvas.addEventListener("mouseleave", () => {
    hoverCol = -1;
    if (!locked && !gameFinished) drawBoard();
  });

  $canvas.addEventListener("click", (e) => {
    const SQ = squareSize();
    const rect = $canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const col = Math.floor(x / SQ);
    humanMove(col);
  });

  /* -- Modal buttons -- */
  $btnYes.addEventListener("click", () => startNewGame());
  $btnNo.addEventListener("click", async () => {
    hideModal();
    sessionId = null;
    await showLeaderboard(nickname);
  });

  /* -- Touch support for mobile -- */
  $canvas.addEventListener("touchstart", (e) => {
    e.preventDefault();
  }, { passive: false });

  $canvas.addEventListener("touchend", (e) => {
    e.preventDefault();
    const touch = e.changedTouches[0];
    const SQ = squareSize();
    const rect = $canvas.getBoundingClientRect();
    const x = touch.clientX - rect.left;
    const col = Math.floor(x / SQ);
    if (col >= 0 && col < N_COLS) humanMove(col);
  }, { passive: false });

  /* -- Responsive resize -- */
  window.addEventListener("resize", () => {
    if ($gameScreen.classList.contains("active")) setupCanvas();
  });

  /* ---- Init language & screen ---- */
  setLanguage(currentLang);
  showScreen("start");

})();
