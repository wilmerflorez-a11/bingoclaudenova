document.addEventListener('DOMContentLoaded', () => {
    
    // ===============================
    // INITIALIZATION
    // ===============================
    const grid = document.getElementById('bingo-grid');
    const socket = new WebSocket(WS_URL);
    const markedCells = new Set(); // Stores indices of marked cells (0-24)
    
    // Render the Bingo Card
    renderCard(MY_CARD);

    // ===============================
    // WEBSOCKET HANDLERS
    // ===============================
    socket.onopen = () => {
        console.log("Conectado al juego");
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        switch(data.type) {
            case 'new_ball':
                handleNewBall(data.number);
                break;
            case 'chat_message':
                addChatMessage(data.user, data.message);
                break;
            case 'game_over':
                handleGameOver(data.winner);
                break;
            case 'game_reset':
                console.log('[DEBUG] game_reset event received!');
                alert("El administrador ha reiniciado el juego. Recargando...");
                console.log('[DEBUG] About to reload page...');
                window.location.reload();
                break;
        }
    };

    // ===============================
    // GAME LOGIC
    // ===============================
    function renderCard(matrix) {
        grid.innerHTML = '';
        matrix.forEach((row, rIndex) => {
            row.forEach((num, cIndex) => {
                const cell = document.createElement('div');
                cell.classList.add('bingo-cell');
                cell.dataset.row = rIndex;
                cell.dataset.col = cIndex;
                
                if (num === 0) {
                    cell.classList.add('marked', 'free');
                    cell.innerHTML = '★';
                    markedCells.add(`${rIndex},${cIndex}`);
                } else {
                    cell.textContent = num;
                    cell.onclick = () => toggleMark(cell, num);
                }
                
                grid.appendChild(cell);
            });
        });
    }

    function toggleMark(cell, number) {
        // In a real game, we might validate if the number has been called.
        // For MVP, we allow free marking to simulate the physical experience.
        cell.classList.toggle('marked');
        
        const key = `${cell.dataset.row},${cell.dataset.col}`;
        if (cell.classList.contains('marked')) {
            markedCells.add(key);
        } else {
            markedCells.delete(key);
        }
        
        checkBingoPossibility();
    }
    
    function handleNewBall(number) {
        // Update current ball display
        const currentBall = document.getElementById('current-ball');
        const history = document.getElementById('ball-history');
        
        // Move current to history
        if (currentBall.textContent !== '--') {
            const mini = document.createElement('div');
            mini.classList.add('mini-ball');
            mini.textContent = currentBall.textContent;
            history.prepend(mini);
        }
        
        // Set new ball
        currentBall.textContent = number;
        
        // Reset timer
        resetTimer();
    }
    
    // ===============================
    // TIMER LOGIC
    // ===============================
    let timerInterval;
    
    function resetTimer() {
        const timerEl = document.getElementById('timer');
        let timeLeft = 10; // 10 seconds
        
        // Clear existing
        if (timerInterval) clearInterval(timerInterval);
        
        // Update display immediately
        timerEl.textContent = `00:${timeLeft.toString().padStart(2, '0')}`;
        
        // Visual pulse effect
        timerEl.classList.remove('pulse');
        void timerEl.offsetWidth; // trigger reflow
        timerEl.classList.add('pulse');
        
        // Start countdown
        timerInterval = setInterval(() => {
            timeLeft--;
            if (timeLeft >= 0) {
                timerEl.textContent = `00:${timeLeft.toString().padStart(2, '0')}`;
            } else {
                clearInterval(timerInterval);
                // Optional: visual indication that time is up (e.g. red color)
                // timerEl.style.color = '#ef4444'; 
            }
        }, 1000);
    }
    
    function checkBingoPossibility() {
        // Enable Bingo button if enough cells are marked (e.g. at least 5)
        const btn = document.getElementById('btn-bingo');
        btn.disabled = markedCells.size < 5;
    }

    // ===============================
    // CHAT
    // ===============================
    document.getElementById('btn-send').onclick = sendChat;
    document.getElementById('chat-input').onkeypress = (e) => {
        if(e.key === 'Enter') sendChat();
    };

    function sendChat() {
        const input = document.getElementById('chat-input');
        const msg = input.value.trim();
        if (!msg) return;
        
        socket.send(JSON.stringify({
            type: 'chat_message',
            message: msg
        }));
        
        input.value = '';
    }

    function addChatMessage(user, msg) {
        const container = document.getElementById('chat-messages');
        const div = document.createElement('div');
        div.classList.add('chat-msg');
        div.innerHTML = `<strong>${user}:</strong> ${msg}`;
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    }
    
    // ===============================
    // BINGO CLAIM
    // ===============================
    document.getElementById('btn-bingo').onclick = () => {
        if (confirm("¿Estás seguro de cantar BINGO?")) {
            socket.send(JSON.stringify({
                type: 'bingo_claim'
            }));
        }
    };
    
    // ===============================
    // GAME OVER
    // ===============================
    function handleGameOver(winner) {
        // Disable further play
        document.getElementById('btn-bingo').disabled = true;
        
        // Show winner overlay
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.9);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        `;
        
        overlay.innerHTML = `
            <div style="text-align: center; color: white;">
                <h1 style="font-size: 4rem; color: #22c55e; font-family: 'Press Start 2P', cursive; margin-bottom: 20px;">
                    🏆 ¡BINGO! 🏆
                </h1>
                <h2 style="font-size: 2rem; margin-bottom: 30px;">
                    Ganador: ${winner}
                </h2>
                <button onclick="location.reload()" style="
                    background: #3b82f6;
                    color: white;
                    border: none;
                    padding: 15px 30px;
                    font-size: 1.2rem;
                    border-radius: 8px;
                    cursor: pointer;
                    font-family: 'Press Start 2P', cursive;
                ">
                    JUGAR DE NUEVO
                </button>
            </div>
        `;
        
        document.body.appendChild(overlay);
    }

});
