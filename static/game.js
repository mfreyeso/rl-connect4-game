/* ============================================================
   Connect 4 — Browser Game Client
   Canvas rendering + REST API integration
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

  /* ---- Sizing (responsive) ---- */
  function squareSize() {
    return Math.max(40, Math.min(85, Math.floor((window.innerWidth - 60) / N_COLS)));
  }

  /* ---- DOM refs ---- */
  const $startScreen = document.getElementById("screen-start");
  const $gameScreen = document.getElementById("screen-game");
  const $modalOverlay = document.getElementById("modal-overlay");
  const $nicknameIn = document.getElementById("nickname-input");
  const $btnPlay = document.getElementById("btn-play");
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

  /* ============================================================
     Screen management
     ============================================================ */
  function showScreen(name) {
    $startScreen.classList.toggle("active", name === "start");
    $gameScreen.classList.toggle("active", name === "game");
    if (name === "start") $nicknameIn.focus();
  }

  function showModal(result, humanScore, machineScore) {
    let msg, cls;
    if (result === "human_win") { msg = `${nickname} wins!`; cls = "win"; }
    else if (result === "machine_win") { msg = "Machine wins!"; cls = "lose"; }
    else { msg = "It's a draw!"; cls = "draw"; }

    $modalResult.textContent = msg;
    $modalResult.className = "modal-result " + cls;
    $modalScores.textContent = `${nickname}: ${humanScore}  —  Machine: ${machineScore}`;
    $modalOverlay.classList.add("visible");
  }

  function hideModal() { $modalOverlay.classList.remove("visible"); }

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

    // Hover row background
    ctx.fillStyle = COLORS.board;
    ctx.fillRect(0, 0, N_COLS * SQ, SQ);

    // Hover ghost piece
    if (hoverCol >= 0 && !locked && !gameFinished) {
      ctx.beginPath();
      ctx.arc(hoverCol * SQ + SQ / 2, SQ / 2, R, 0, Math.PI * 2);
      ctx.fillStyle = COLORS.hoverGhost;
      ctx.fill();

      // Solid preview piece
      ctx.beginPath();
      ctx.arc(hoverCol * SQ + SQ / 2, SQ / 2, R, 0, Math.PI * 2);
      ctx.fillStyle = COLORS.player2;
      ctx.globalAlpha = 0.7;
      ctx.fill();
      ctx.globalAlpha = 1;
    }

    // Board grid
    for (let r = 0; r < N_ROWS; r++) {
      for (let c = 0; c < N_COLS; c++) {
        const x = c * SQ;
        const y = (N_ROWS - r) * SQ;  // row 0 = bottom → screen bottom

        // Board square
        ctx.fillStyle = COLORS.board;
        ctx.fillRect(x, y, SQ, SQ);

        // Cell circle
        ctx.beginPath();
        ctx.arc(x + SQ / 2, y + SQ / 2, R, 0, Math.PI * 2);

        const piece = board[r] ? board[r][c] : 0;
        if (piece === MACHINE_PIECE) ctx.fillStyle = COLORS.player1;
        else if (piece === HUMAN_PIECE) ctx.fillStyle = COLORS.player2;
        else ctx.fillStyle = COLORS.cellEmpty;

        // Highlight winning cells with pulsing glow
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
  /* ---- Win highlight animation ---- */
  function startWinHighlight(winningCells, state, durationMs) {
    if (winHighlightTimer) cancelAnimationFrame(winHighlightTimer);
    const t0 = performance.now();

    function pulse(now) {
      const elapsed = now - t0;
      const phase = (elapsed / 200);  // controls pulse speed
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

  /* ---- Drop animation ---- */
  function animateDrop(col, targetRow, piece, callback) {
    const SQ = squareSize();
    const R = SQ / 2 - 5;
    const color = piece === MACHINE_PIECE ? COLORS.player1 : COLORS.player2;

    const startY = SQ / 2;                                 // top of board
    const endY = (N_ROWS - targetRow) * SQ + SQ / 2;     // destination
    const duration = 250 + (N_ROWS - targetRow) * 35;       // ms
    const t0 = performance.now();

    function frame(now) {
      const elapsed = now - t0;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out bounce feel
      const eased = 1 - Math.pow(1 - progress, 3);
      const y = startY + (endY - startY) * eased;

      drawBoard();

      // Animated piece
      ctx.beginPath();
      ctx.arc(col * SQ + SQ / 2, y, R, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();

      if (progress < 1) {
        requestAnimationFrame(frame);
      } else {
        // commit piece to board data and redraw
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
    hideModal();
    if (winHighlightTimer) { cancelAnimationFrame(winHighlightTimer); winHighlightTimer = null; }
    gameFinished = false;
    locked = true;
    $turnInd.textContent = "Starting...";
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

      // If machine went first, animate its piece
      if (data.state.machine_move !== null && data.state.machine_move !== undefined) {
        const mCol = data.state.machine_move;
        const mRow = findPieceRow(board, mCol, MACHINE_PIECE);
        // Temporarily remove the piece so we can animate it
        board[mRow][mCol] = 0;
        drawBoard();
        animateDrop(mCol, mRow, MACHINE_PIECE, () => {
          locked = false;
          $turnInd.textContent = "Your turn";
        });
      } else {
        locked = false;
        $turnInd.textContent = "Your turn";
      }
    } catch (err) {
      console.error("Failed to start game:", err);
      $turnInd.textContent = "Error starting game";
      locked = false;
    }
  }

  /** Find the row where a particular piece sits in a column (topmost). */
  function findPieceRow(boardData, col, piece) {
    for (let r = N_ROWS - 1; r >= 0; r--) {
      if (boardData[r] && boardData[r][col] === piece) return r;
    }
    return 0;
  }

  /** Find the first empty row in a column (for animation target). */
  function findNextOpenRow(col) {
    for (let r = 0; r < N_ROWS; r++) {
      if (!board[r] || board[r][col] === 0) return r;
    }
    return -1;
  }

  async function humanMove(col) {
    if (locked || gameFinished) return;
    if (col < 0 || col >= N_COLS) return;

    const targetRow = findNextOpenRow(col);
    if (targetRow < 0) return; // column full

    locked = true;
    $turnInd.textContent = "";

    // Animate human piece drop locally first
    animateDrop(col, targetRow, HUMAN_PIECE, async () => {
      $turnInd.textContent = "Machine is thinking...";
      $turnInd.classList.add("thinking");

      try {
        const state = await apiMove(col);
        board = state.board;

        if (state.result) {
          gameFinished = true;
          $humanScore.textContent = state.human_score;
          $machineScore.textContent = state.machine_score;

          // If human won, draw with highlight and delay modal
          if (state.result === "human_win") {
            locked = false;
            $turnInd.classList.remove("thinking");
            $turnInd.textContent = "";
            startWinHighlight(state.winning_cells, state, 3000);
            return;
          }
        }

        // Animate machine move if it played
        if (state.machine_move !== null && state.machine_move !== undefined) {
          const mCol = state.machine_move;
          const mRow = findPieceRow(board, mCol, MACHINE_PIECE);
          board[mRow][mCol] = 0; // temp remove for animation
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
              $turnInd.textContent = "Your turn";
              drawBoard();
            }
          });
        } else {
          // No machine move (game ended on human move — draw)
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
        $turnInd.textContent = "Error — try again";
        $turnInd.classList.remove("thinking");
        locked = false;
      }
    });
  }

  /* ============================================================
     Event listeners
     ============================================================ */

  /* -- Start screen -- */
  $nicknameIn.addEventListener("input", () => {
    $btnPlay.disabled = !$nicknameIn.value.trim();
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
  $btnNo.addEventListener("click", () => {
    hideModal();
    showScreen("start");
    $nicknameIn.value = nickname;
    $nicknameIn.focus();
    $btnPlay.disabled = false;
    sessionId = null;
  });

  /* -- Touch support for mobile -- */
  $canvas.addEventListener("touchstart", (e) => {
    e.preventDefault(); // prevent page scroll while playing
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

  /* ---- Init ---- */
  showScreen("start");

})();
