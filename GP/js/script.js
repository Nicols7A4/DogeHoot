document.addEventListener('DOMContentLoaded', () => {

    // --- Definición de Preguntas ---
    const questions = [
        { question: "¿Capital de Francia?", answers: [{ text: "Berlín", correct: false }, { text: "Madrid", correct: false }, { text: "París", correct: true }, { text: "Roma", correct: false }] },
        { question: "¿Cuánto es 2 + 2?", answers: [{ text: "3", correct: false }, { text: "4", correct: true }, { text: "5", correct: false }, { text: "6", correct: false }] },
        { question: "¿Color del cielo despejado?", answers: [{ text: "Azul", correct: true }, { text: "Verde", correct: false }, { text: "Rojo", correct: false }, { text: "Amarillo", correct: false }] }
    ];

    // --- Constantes de Tiempo ---
    const FADE_DURATION = 300;
    const FEEDBACK_TIME = 1500;
    const WAITING_SCREEN_TOTAL_TIME = 2500;
    const TRANSITION_ANIMATION_TIME = 3000;
    const LOBBY_WAIT_TIME = 4000;
    const HOST_QUESTION_TIME = 10000;
    const HOST_FEEDBACK_TIME = 4000;
    const SLIDE_DURATION = 500;

    // --- Variables del Juego ---
    let currentQuestionIndex = 0;
    let score = 0;
    const questionnaireTitle = "Cuestionario de Cultura General";
    let selectedPlayer = null; // Host: jugador seleccionado (Elemento DOM)
    let playerToDelete = null; // Host: jugador a eliminar (Elemento DOM)
    let maxPlayersPerGroup = 10;
    let groupsEnabled = true; // Simulación: Si el host activó grupos
    let playerSelectedGroupId = null; // Player: ID del grupo elegido
    let playerIsReady = false;
    let gameStartTimer = null;
    let isHost = false;
    let playerQuestionTimer = null;
    let playerTimerInterval = null;
    let hostQuestionTimer = null;
    let hostTimerInterval = null;

    // --- Elementos del DOM ---
    const container = document.querySelector('.container');

    // Pantallas
    const joinScreen = document.getElementById('join-screen');
    const startScreen = document.getElementById('start-screen');
    const transitionScreen = document.getElementById('transition-screen');
    const questionScreen = document.getElementById('question-screen');
    const waitingScreen = document.getElementById('waiting-screen');
    const endTransitionScreen = document.getElementById('end-transition-screen');
    const podiumScreen = document.getElementById('podium-screen');
    const hostScreen = document.getElementById('host-screen');

    // Botones
    const joinButton = document.getElementById('join-button');
    const readyButton = document.getElementById('ready-button');
    const restartButton = document.getElementById('restart-button'); // Podio
    const playAgainButton = document.getElementById('play-again-button'); // Podio
    const hostTestButton = document.getElementById('host-test-button');
    const cancelGameButton = document.getElementById('cancel-game-btn'); // Host
    const toggleGroupsBtn = document.getElementById('toggle-groups-btn'); // Host
    const editGroupSizeBtn = document.getElementById('edit-group-size-btn'); // Host
    const leaveLobbyButton = document.getElementById('leave-lobby-button'); // Jugador Lobby
    const hostReturnTestBtn = document.getElementById('host-return-test-btn'); // Host
    const deletePlayerBtn = document.getElementById('delete-player-btn'); // Host
    const startGameButton = document.getElementById('start-game-btn');


    // Elementos del Jugador
    const pinInput = document.getElementById('pin-input');
    const lobbyPinDisplay = document.getElementById('lobby-pin-display');
    const transitionTitle = document.getElementById('transition-title');
    const questionnaireName = document.getElementById('questionnaire-name');
    const endTransitionTitle = document.getElementById('end-transition-title');
    const questionText = document.getElementById('question-text');
    const answerButtons = document.getElementById('answer-buttons');
    const feedbackText = document.getElementById('feedback-text');
    const waitScore = document.getElementById('wait-score');
    const waitPosition = document.getElementById('wait-position');
    const finalScore = document.getElementById('final-score');
    const hostQuestionScreen = document.getElementById('host-question-screen');
    const hostQText = document.getElementById('host-q-text');
    const hostQTimer = document.getElementById('host-q-timer');
    const hostQAnswerGrid = document.getElementById('host-q-answer-grid');
    const hostQFeedback = document.getElementById('host-q-feedback');
    const hostNextQButton = document.getElementById('host-next-q-btn');
    const playerTimerBox = document.getElementById('player-timer-box');
    const waitingText = document.querySelector('#waiting-screen .waiting-text');

    // Específicos Lobby Jugador
    const playerLobbyMessage = document.getElementById('player-lobby-message');
    const playerLobbyGroupBoxes = document.getElementById('player-lobby-group-boxes');

    // Elementos del Host
    const playerPool = document.getElementById('host-player-pool');
    const hostBody = hostScreen ? hostScreen.querySelector('.host-body') : null;

    // Elementos del Modal de Grupo (Host)
    const groupModal = document.getElementById('group-modal-overlay');
    const modalCloseBtn = document.getElementById('modal-close-btn');
    const modalTitle = document.getElementById('modal-group-title');
    const modalGrid = document.getElementById('modal-player-grid');

    // Elementos del Modal de Tamaño de Grupo (Host)
    const groupSizeModal = document.getElementById('group-size-modal-overlay');
    const groupSizeCloseBtn = document.getElementById('group-size-close-btn');
    const groupSizeDisplay = document.getElementById('group-size-display');
    const increaseGroupSizeBtn = document.getElementById('increase-group-size-btn');
    const decreaseGroupSizeBtn = document.getElementById('decrease-group-size-btn');

    // Elementos del Modal de Confirmación Eliminar (Host)
    const confirmDeleteModal = document.getElementById('confirm-delete-modal-overlay');
    const confirmDeleteYesBtn = document.getElementById('confirm-delete-yes-btn');
    const confirmDeleteNoBtn = document.getElementById('confirm-delete-no-btn');


    // --- Funciones del Juego (JUGADOR) ---

    // Configura la vista del lobby del jugador
    function setupPlayerLobby() {
        if (!startScreen) return;

        if (!playerLobbyGroupBoxes || !playerLobbyMessage || !readyButton) {
            console.error("Error: Elementos del lobby del jugador no encontrados para setup.");
            return;
        }

        playerLobbyGroupBoxes.innerHTML = ''; // Limpiar cajas anteriores
        playerSelectedGroupId = null; // Limpiar selección lógica

        if (groupsEnabled) {
            playerLobbyMessage.classList.add('hidden');
            playerLobbyGroupBoxes.classList.remove('hidden');
            readyButton.disabled = true; // Botón LISTO desactivado hasta seleccionar

            // Crear las cajas de grupo dinámicamente
            for (let i = 1; i <= 8; i++) {
                const groupBox = document.createElement('div');
                groupBox.classList.add('player-lobby-group-box');
                groupBox.dataset.groupId = i;

                const title = document.createElement('h4');
                title.textContent = `Grupo ${i}`;
                groupBox.appendChild(title);

                const membersContainer = document.createElement('div');
                membersContainer.classList.add('player-lobby-group-members');
                groupBox.appendChild(membersContainer);

                // Obtener miembros actuales del host (simulación)
                const hostGroupList = hostScreen ? hostScreen.querySelector(`.group-box[data-group-id="${i}"] .group-player-list`) : null;
                let currentPlayers = 0;
                if (hostGroupList) {
                    const hostPlayers = hostGroupList.querySelectorAll('.player-circle:not(.player-circle-overflow)');
                    currentPlayers = hostPlayers.length;
                    hostPlayers.forEach(p => {
                        const clone = p.cloneNode(true);
                        clone.style.cursor = 'default';
                        membersContainer.appendChild(clone);
                    });
                }

                if (currentPlayers >= maxPlayersPerGroup) {
                    groupBox.classList.add('full');
                    title.textContent += " (Lleno)";
                } else {
                    groupBox.addEventListener('click', handlePlayerGroupSelection);
                }

                playerLobbyGroupBoxes.appendChild(groupBox);
            }

        } else { // Grupos NO habilitados
            playerLobbyMessage.classList.remove('hidden');
            playerLobbyGroupBoxes.classList.add('hidden');
            readyButton.disabled = false; // Botón LISTO activado
        }
    }

    // Maneja clic en caja de grupo (jugador)
    function handlePlayerGroupSelection(event) {
        const clickedBox = event.currentTarget;
        if (clickedBox.classList.contains('full')) return;

        const groupId = clickedBox.dataset.groupId;

        // Remover indicador 'TÚ' y highlight de otras cajas
        document.querySelectorAll('.player-self-indicator').forEach(indicator => indicator.remove());
        document.querySelectorAll('.player-lobby-group-box.selected-by-player').forEach(box => box.classList.remove('selected-by-player'));

        // Añadir indicador 'TÚ' a esta caja
        const selfIndicator = document.createElement('div');
        selfIndicator.className = 'player-circle player-self-indicator';
        selfIndicator.textContent = 'TÚ'; // Añadir texto directamente
        const membersContainer = clickedBox.querySelector('.player-lobby-group-members');
        if (membersContainer) membersContainer.appendChild(selfIndicator);

        // Marcar esta caja como seleccionada
        clickedBox.classList.add('selected-by-player');
        playerSelectedGroupId = groupId;

        // Habilitar botón LISTO
        if (readyButton) readyButton.disabled = false;
    }

    // Para salir del grupo (jugador) - Ya no se usa con el nuevo diseño
    /* function leavePlayerGroup() { ... } */


    function joinGame() {
        isHost = false;
        const pin = pinInput ? pinInput.value.toUpperCase() : '';

        // 1. Cambiar botón a "Entrando..." (reemplazando su HTML)
        joinButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="5" y1="12" x2="19" y2="12"></line>
        <polyline points="12 5 19 12 12 19"></polyline>
    </svg> Entrando...`;
        joinButton.disabled = true;

        setTimeout(() => {
            if (pin === "ABC123") {
                if (lobbyPinDisplay) lobbyPinDisplay.innerText = pin;
                setupPlayerLobby();
                slideScreen(joinScreen, startScreen);
                // No restauramos el botón aquí, porque nos vamos de la pantalla.
                // restartGame() se encargará de restaurarlo si volvemos.
            } else {
                alert("PIN incorrecto. Intente de nuevo.");
                if (pinInput) pinInput.value = "";

                // 2. Restaurar botón si el PIN es incorrecto
                restoreJoinButton(); // <-- ¡Aquí está la corrección!
            }
        }, 500);
    }

    function setReady() {
        if (!readyButton) return;

        if (playerIsReady) {
            // --- LÓGICA PARA CANCELAR EL ESTADO "LISTO" ---
            console.log("Jugador canceló estado 'Listo'.");

            // 1. Cancelar el temporizador si existe
            if (gameStartTimer) {
                clearTimeout(gameStartTimer);
                gameStartTimer = null;
            }
            playerIsReady = false;

            // 2. Restaurar el botón
            readyButton.innerText = "LISTO";
            readyButton.disabled = false; // Asegurarse de que sigue habilitado
            readyButton.classList.remove('waiting', 'btn-warning');
            readyButton.classList.add('btn-success');

            // 3. (IMPORTANTE) Reactivar la selección de grupos
            if (groupsEnabled) {
                document.querySelectorAll('.player-lobby-group-box:not(.full)').forEach(box => {
                    box.addEventListener('click', handlePlayerGroupSelection);
                });
            }

        } else {
            // --- LÓGICA PARA ESTABLECER EL ESTADO "LISTO" (como antes) ---

            // 1. Validar si se seleccionó un grupo (si los grupos están activos)
            if (groupsEnabled && playerSelectedGroupId === null) {
                alert("Por favor, selecciona un grupo antes de estar listo.");
                return;
            }

            console.log("Jugador listo. Grupo seleccionado:", playerSelectedGroupId);
            playerIsReady = true;

            // 2. Cambiar apariencia del botón (sin deshabilitarlo)
            readyButton.innerText = "ESPERANDO... (Cancelar)"; // Texto actualizado
            readyButton.disabled = false; // ¡IMPORTANTE! No deshabilitar
            readyButton.classList.add('waiting');
            readyButton.classList.remove('btn-success');
            readyButton.classList.add('btn-warning');

            // 3. (IMPORTANTE) Desactivar la selección de grupos
            if (groupsEnabled) {
                document.querySelectorAll('.player-lobby-group-box').forEach(box => {
                    box.removeEventListener('click', handlePlayerGroupSelection);
                });
            }

            // 4. Iniciar el temporizador (simulación del host)
            gameStartTimer = setTimeout(() => {
                console.log("Temporizador completado, iniciando juego.");
                // Resetear estado antes de empezar
                playerIsReady = false;
                gameStartTimer = null;
                startGame();
            }, LOBBY_WAIT_TIME); // Usar la constante actualizada
        }
    }

    function startGame() {
        currentQuestionIndex = 0;
        score = 0;
        showQuestion();
    }
    function showQuestion() {
        resetState();
        if (questionnaireName) questionnaireName.innerText = questionnaireTitle;
        if (transitionTitle) {
            if (currentQuestionIndex === 0) transitionTitle.innerText = "COMIENZA LA PARTIDA";
            else transitionTitle.innerText = `PREGUNTA ${currentQuestionIndex + 1}`;
        }
        if (transitionScreen) {
            transitionScreen.classList.remove('animate-slide-across');
            showScreen(transitionScreen);
            void transitionScreen.offsetWidth;
            transitionScreen.classList.add('animate-slide-across');
        }

        const question = questions[currentQuestionIndex];
        if (!question) { endGame(); return; }
        if (questionText) questionText.innerText = question.question;
        if (answerButtons) answerButtons.innerHTML = '';

        question.answers.forEach(answer => {
            const button = document.createElement('button');
            button.innerText = answer.text;
            button.classList.add('btn');
            if (answer.correct) button.dataset.correct = true;
            button.addEventListener('click', selectAnswer);
            if (answerButtons) answerButtons.appendChild(button);
        });
        // 5. Iniciar temporizadores del JUGADOR
        clearTimeout(playerQuestionTimer);
        clearInterval(playerTimerInterval);
        let timeLeft = HOST_QUESTION_TIME / 1000;

        if (playerTimerBox) {
            playerTimerBox.textContent = timeLeft;
            playerTimerBox.style.display = 'flex';
        }

        playerTimerInterval = setInterval(() => {
            timeLeft--;
            if (playerTimerBox) playerTimerBox.textContent = timeLeft;
            if (timeLeft <= 0) {
                clearInterval(playerTimerInterval);
            }
        }, 1000);

        // Temporizador principal que llama al timeout
        playerQuestionTimer = setTimeout(() => {
            handlePlayerTimeout(); // Función que se ejecuta si se acaba el tiempo
        }, HOST_QUESTION_TIME);

        // 6. Mostrar la pantalla de la pregunta después de la transición
        setTimeout(() => {
            showScreen(questionScreen);
        }, TRANSITION_ANIMATION_TIME);
    }
    function selectAnswer(e) {
        // 1. Detener los temporizadores
        clearTimeout(playerQuestionTimer);
        clearInterval(playerTimerInterval);
        if (playerTimerBox) playerTimerBox.style.display = 'none';

        // 2. Obtener respuesta
        const selectedButton = e.target;
        const isCorrect = selectedButton.dataset.correct === 'true';

        // 3. Procesar
        processPlayerAnswer(selectedButton, isCorrect);
    }
    function handlePlayerTimeout() {
        clearInterval(playerTimerInterval); // Detener contador UI
        if (playerTimerBox) playerTimerBox.style.display = 'none';
        console.log("¡Tiempo agotado para el jugador!");

        // Llamar a la función de procesamiento, indicando que no hubo selección
        processPlayerAnswer(null, false);
    }
    function processPlayerAnswer(selectedButton, isCorrect) {
        // 1. Deshabilitar todos los botones y mostrar correctos/incorrectos
        if (answerButtons) {
            Array.from(answerButtons.children).forEach(button => {
                // Si el botón que estamos iterando es el correcto
                if (button.dataset.correct) {
                    button.classList.add('correct');
                }
                // Si el botón que estamos iterando fue el que seleccionó el jugador (y no es el correcto)
                else if (button === selectedButton) {
                    button.classList.add('incorrect');
                }
                // Si no fue seleccionado, pero es incorrecto (y no es el botón nulo de timeout)
                else if (selectedButton !== null) {
                    button.classList.add('incorrect');
                    button.style.opacity = "0.6"; // Atenuar
                }

                button.disabled = true;
            });
        }

        // 2. Mostrar feedback y actualizar puntuación
        if (selectedButton === null) {
            // Caso: Tiempo agotado
            if (feedbackText) { feedbackText.innerText = "¡Tiempo agotado!"; feedbackText.style.color = "#dc3545"; }
        } else if (isCorrect) {
            // Caso: Correcto
            score++;
            if (feedbackText) { feedbackText.innerText = "¡Correcto!"; feedbackText.style.color = "#198754"; }
        } else {
            // Caso: Incorrecto
            if (feedbackText) { feedbackText.innerText = "Incorrecto"; feedbackText.style.color = "#dc3545"; }
        }

        // 3. Avanzar a la siguiente pantalla (espera o fin)
        setTimeout(() => {
            currentQuestionIndex++;

            // Comprobar si el juego ha terminado (después de incrementar)
            const isGameOver = (currentQuestionIndex >= questions.length);

            // Siempre mostrar la pantalla de espera, 
            // pero pasarle si es el final.
            showWaitingScreen(isGameOver);

        }, FEEDBACK_TIME);
    }
    function showWaitingScreen(isGameOver = false) {
        // 1. Mostrar puntuación y posición
        if (waitScore) waitScore.innerText = `${score} / ${questions.length}`;
        if (waitPosition) waitPosition.innerText = "1 / 10";

        // 2. Mostrar la pantalla
        showScreen(waitingScreen);

        if (isGameOver) {
            // 3.A. Es el final: Cambiar texto y preparar para ir al podio
            if (waitingText) waitingText.innerText = "Esperando finalización de partida";

            // Usamos el mismo tiempo de espera antes de mostrar la transición final
            setTimeout(() => {
                if (waitingScreen) waitingScreen.classList.add('fading-out');
                setTimeout(() => { endGame(); }, FADE_DURATION); // Llamar a endGame()
            }, WAITING_SCREEN_TOTAL_TIME - FADE_DURATION);

        } else {
            // 3.B. No es el final: Texto normal y preparar siguiente pregunta
            if (waitingText) waitingText.innerText = "ESPERANDO LA SIGUIENTE PREGUNTA...";

            // Comportamiento original
            setTimeout(() => {
                if (waitingScreen) waitingScreen.classList.add('fading-out');
                setTimeout(() => { showQuestion(); }, FADE_DURATION); // Llamar a showQuestion()
            }, WAITING_SCREEN_TOTAL_TIME - FADE_DURATION);
        }
    }
    function endGame() {
        if (endTransitionScreen) {
            endTransitionScreen.classList.remove('animate-slide-across');
            showScreen(endTransitionScreen);
            void endTransitionScreen.offsetWidth;
            endTransitionScreen.classList.add('animate-slide-across');
        }
        if (finalScore) finalScore.innerText = `${score} / ${questions.length}`;
        setTimeout(() => { showScreen(podiumScreen); }, TRANSITION_ANIMATION_TIME);
    }

    function restartGame() {
        // 1. Capturar el estado actual ANTES de resetear
        const wasHost = isHost;

        // 2. Resetear todos los estados del juego
        if (pinInput) pinInput.value = "";
        if (transitionScreen) transitionScreen.classList.remove('animate-slide-across');
        if (endTransitionScreen) endTransitionScreen.classList.remove('animate-slide-across');

        restoreJoinButton(); // <-- Fix para Bug 1 y 3

        playerIsReady = false;
        if (gameStartTimer) {
            clearTimeout(gameStartTimer);
            gameStartTimer = null;
        }
        if (playerQuestionTimer) clearTimeout(playerQuestionTimer);
        if (playerTimerInterval) clearInterval(playerTimerInterval);

        isHost = false; // Resetear rol para la próxima partida

        // 3. Resetear botones y UI
        if (hostNextQButton) hostNextQButton.textContent = "Siguiente Pregunta";

        // <-- Fix para Bug 2: Resetear el botón LISTO
        if (readyButton) {
            readyButton.innerText = "LISTO";
            readyButton.classList.remove('waiting', 'btn-warning');
            readyButton.classList.add('btn-success');
        }

        // 4. Resetear UI del Host
        if (hostBody) hostBody.classList.remove('groups-hidden');
        if (toggleGroupsBtn) {
            toggleGroupsBtn.classList.add('active');
            toggleGroupsBtn.textContent = 'Desactivar Grupos';
            groupsEnabled = true;
        }
        if (deletePlayerBtn) deletePlayerBtn.disabled = true;
        selectedPlayer = null;
        if (playerPool && hostScreen) {
            const groupedPlayers = hostScreen.querySelectorAll('.group-player-list .player-circle');
            groupedPlayers.forEach(player => { playerPool.appendChild(player); });
            document.querySelectorAll('.group-player-list').forEach(updateGroupDisplay);
        }

        // 5. Resetear UI del Jugador
        setupPlayerLobby(); // Esto manejará el 'disabled' del readyButton

        // 6. Mostrar la pantalla de inicio correcta
        if (wasHost) {
            showScreen(hostScreen);
        } else {
            showScreen(joinScreen);
        }
    }

    // --- LÓGICA PARA LA PANTALLA DE ANFITRIÓN ---

    function updateGroupDisplay(groupListElement) {
        if (!groupListElement) return;
        const players = groupListElement.querySelectorAll('.player-circle:not(.player-circle-overflow)');
        const count = players.length;
        let overflowBtn = groupListElement.querySelector('.player-circle-overflow');
        if (!overflowBtn) {
            overflowBtn = document.createElement('div');
            overflowBtn.className = 'player-circle player-circle-overflow';
            groupListElement.appendChild(overflowBtn);
        }
        if (count > 6) {
            groupListElement.classList.add('has-overflow');
            overflowBtn.textContent = `+${count - 6}`;
        } else {
            groupListElement.classList.remove('has-overflow');
        }
    }
    function openGroupModal(groupElement) {
        const groupList = groupElement.querySelector('.group-player-list');
        const groupTitle = groupElement.querySelector('.group-box-title').textContent;
        const players = groupList.querySelectorAll('.player-circle:not(.player-circle-overflow)');
        if (modalTitle) modalTitle.textContent = groupTitle;
        if (modalGrid) modalGrid.innerHTML = '';
        if (modalGrid && groupList) modalGrid.dataset.originGroupListId = groupList.closest('.group-box').dataset.groupId;
        players.forEach(player => {
            const playerClone = player.cloneNode(true);
            playerClone.style.display = 'flex';
            playerClone.classList.remove('selected');
            if (modalGrid) modalGrid.appendChild(playerClone);
        });
        if (groupModal) groupModal.style.display = 'flex';
    }
    function initializeHostScreen() {
        if (!hostScreen || !playerPool || !deletePlayerBtn) return;

        hostScreen.addEventListener('click', (e) => {
            const clickedPlayer = e.target.closest('.player-circle:not(.player-circle-overflow)');
            const clickedGroup = e.target.closest('.group-box');
            const clickedOverflow = e.target.closest('.player-circle-overflow');

            if (clickedOverflow) {
                openGroupModal(clickedOverflow.closest('.group-box'));
                return;
            }

            if (clickedPlayer) {
                const parentElement = clickedPlayer.parentElement;
                if (parentElement && parentElement.id === 'host-player-pool') {
                    if (clickedPlayer === selectedPlayer) {
                        clickedPlayer.classList.remove('selected');
                        selectedPlayer = null;
                        deletePlayerBtn.disabled = true;
                    } else {
                        if (selectedPlayer) selectedPlayer.classList.remove('selected');
                        clickedPlayer.classList.add('selected');
                        selectedPlayer = clickedPlayer;
                        deletePlayerBtn.disabled = false;
                    }
                } else {
                    const oldGroupList = clickedPlayer.closest('.group-player-list');
                    playerPool.appendChild(clickedPlayer);
                    if (oldGroupList) updateGroupDisplay(oldGroupList);
                    if (selectedPlayer === clickedPlayer) {
                        selectedPlayer = null;
                        deletePlayerBtn.disabled = true;
                    }
                    clickedPlayer.classList.remove('selected');
                }
            }
            else if (clickedGroup && selectedPlayer) {
                const groupList = clickedGroup.querySelector('.group-player-list');
                if (groupList) {
                    const currentPlayersInGroup = groupList.querySelectorAll('.player-circle:not(.player-circle-overflow)').length;
                    if (currentPlayersInGroup < maxPlayersPerGroup) {
                        groupList.appendChild(selectedPlayer);
                        selectedPlayer.classList.remove('selected');
                        selectedPlayer = null;
                        deletePlayerBtn.disabled = true;
                        updateGroupDisplay(groupList);
                    } else {
                        alert(`Este grupo ya está lleno (máximo ${maxPlayersPerGroup} participantes).`);
                    }
                }
            }
            else if (!clickedPlayer && !clickedGroup && !clickedOverflow && selectedPlayer) {
                selectedPlayer.classList.remove('selected');
                selectedPlayer = null;
                deletePlayerBtn.disabled = true;
            }
        });

        if (modalGrid) {
            modalGrid.addEventListener('click', (e) => {
                const clickedPlayerInModal = e.target.closest('.player-circle');
                if (!clickedPlayerInModal) return;
                const playerId = clickedPlayerInModal.dataset.playerId;
                const originalPlayerElement = hostScreen.querySelector(`.player-circle[data-player-id="${playerId}"]`);
                if (originalPlayerElement) {
                    const originalGroupList = originalPlayerElement.closest('.group-player-list');
                    playerPool.appendChild(originalPlayerElement);
                    clickedPlayerInModal.remove();
                    if (originalGroupList) updateGroupDisplay(originalGroupList);
                    if (selectedPlayer === originalPlayerElement) {
                        selectedPlayer = null;
                        deletePlayerBtn.disabled = true;
                    }
                    originalPlayerElement.classList.remove('selected');
                }
            });
        }
    }

    // --- Funciones Auxiliares ---
    function showScreen(screenToShow) {
        // 1. Limpiar todas las pantallas
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.remove('active');
            screen.classList.remove('fading-out');
            // --- AÑADIR ESTA LÍNEA DE LIMPIEZA ---
            screen.classList.remove('sliding', 'slide-in-left', 'slide-in-right', 'slide-out-left', 'slide-out-right');
        });

        // 2. Limpiar todos los modales
        if (groupModal) groupModal.style.display = 'none';
        if (groupSizeModal) groupSizeModal.style.display = 'none';
        if (confirmDeleteModal) confirmDeleteModal.style.display = 'none';

        // 3. Limpiar el contenedor
        if (container) {
            container.classList.remove('is-sliding'); // <-- ARREGLA EL BUG DEL BACKGROUND
            container.classList.remove('transition-active');
        }

        // 4. Mostrar la pantalla deseada
        if (screenToShow) {
            screenToShow.classList.add('active');

            // Aplicar transparencia solo para las transiciones de fade (no slide)
            if (screenToShow.id === 'transition-screen' || screenToShow.id === 'end-transition-screen') {
                if (container) container.classList.add('transition-active');
            }
        } else {
            console.error("Error: La pantalla que se intenta mostrar no existe.");
        }
    }
    function slideScreen(currentScreen, newScreen) {
        if (!currentScreen || !newScreen) {
            console.error("Error: Faltan pantallas para la transición de deslizamiento.");
            showScreen(newScreen);
            return;
        }

        const currentHeight = container.offsetHeight; // 1. Obtener altura actual
        if (container) {
            container.classList.add('is-sliding');
            container.style.minHeight = `${currentHeight}px`; // 2. Fijar altura
        }

        // 1. Aplicar clases de posicionamiento y 'active'
        currentScreen.classList.add('sliding');
        newScreen.classList.add('sliding');
        newScreen.classList.add('active'); // Para que sea display:block

        // 2. Aplicar animaciones
        newScreen.classList.add('slide-in-right');
        currentScreen.classList.add('slide-out-left');

        // 3. Limpiar clases después de la animación
        setTimeout(() => {
            currentScreen.classList.remove('active');
            currentScreen.classList.remove('slide-out-left', 'sliding');
            newScreen.classList.remove('slide-in-right', 'sliding');
            if (container) container.classList.remove('is-sliding');
        }, SLIDE_DURATION);
    }
    // --- REEMPLAZAR ESTA FUNCIÓN ---
    function slideScreenReverse(currentScreen, newScreen) {
        if (!currentScreen || !newScreen) {
            console.error("Error: Faltan pantallas para la transición de deslizamiento inverso.");
            showScreen(newScreen);
            return;
        }

        const currentHeight = container.offsetHeight; // 1. Obtener altura actual
        if (container) {
            container.classList.add('is-sliding');
            container.style.minHeight = `${currentHeight}px`; // 2. Fijar altura
        }

        // 1. Aplicar clases de posicionamiento y 'active'
        currentScreen.classList.add('sliding');
        newScreen.classList.add('sliding');
        newScreen.classList.add('active'); // Para que sea display:block

        // 2. Aplicar animaciones (INVERSAS)
        newScreen.classList.add('slide-in-left');
        currentScreen.classList.add('slide-out-right');

        // 3. Limpiar clases después de la animación
        setTimeout(() => {
            currentScreen.classList.remove('active');
            currentScreen.classList.remove('slide-out-right', 'sliding');
            newScreen.classList.remove('slide-in-left', 'sliding');
            if (container) container.classList.remove('is-sliding');
        }, SLIDE_DURATION);
    }

    function resetState() {
        if (feedbackText) feedbackText.innerText = "";
        if (playerTimerBox) playerTimerBox.style.display = 'none';
        if (answerButtons) {
            while (answerButtons.firstChild) {
                answerButtons.removeChild(answerButtons.firstChild);
            }
        }
    }

    function restoreJoinButton() {
        if (!joinButton) return;
        // Restaura el HTML original exacto del botón
        joinButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="5" y1="12" x2="19" y2="12"></line>
        <polyline points="12 5 19 12 12 19"></polyline>
    </svg> Unirse Ahora`;
        joinButton.disabled = false;
    }

    // --- Event Listeners ---
    if (joinButton) joinButton.addEventListener('click', joinGame);
    if (readyButton) readyButton.addEventListener('click', setReady);
    if (restartButton) restartButton.addEventListener('click', restartGame);
    if (playAgainButton) playAgainButton.addEventListener('click', restartGame);
    if (startGameButton) startGameButton.addEventListener('click', hostStartGame);
    if (hostNextQButton) hostNextQButton.addEventListener('click', hostGoToNextStep);

    // LISTENERS HOST
    if (hostTestButton) hostTestButton.addEventListener('click', () => { showScreen(hostScreen); });
    if (cancelGameButton) cancelGameButton.addEventListener('click', () => { restartGame(); });
    // Listener toggle grupos (Actualiza variable global 'groupsEnabled')
    if (toggleGroupsBtn && hostBody && playerPool) {
        toggleGroupsBtn.addEventListener('click', () => {
            const wereGroupsVisible = !hostBody.classList.contains('groups-hidden');
            hostBody.classList.toggle('groups-hidden');
            toggleGroupsBtn.classList.toggle('active');
            groupsEnabled = !hostBody.classList.contains('groups-hidden');

            if (!groupsEnabled) {
                toggleGroupsBtn.textContent = 'Activar Grupos';
                if (wereGroupsVisible) {
                    const groupedPlayers = hostScreen.querySelectorAll('.group-player-list .player-circle:not(.player-circle-overflow)');
                    groupedPlayers.forEach(player => {
                        playerPool.appendChild(player);
                        player.classList.remove('selected');
                    });
                    if (selectedPlayer && selectedPlayer.parentElement !== playerPool) {
                        selectedPlayer = null;
                        if (deletePlayerBtn) deletePlayerBtn.disabled = true;
                    }
                    document.querySelectorAll('.group-player-list').forEach(updateGroupDisplay);
                }
            } else {
                toggleGroupsBtn.textContent = 'Desactivar Grupos';
            }
            // ACTUALIZAR VISTA JUGADOR (si está en lobby)
            if (startScreen && startScreen.classList.contains('active')) {
                setupPlayerLobby();
            }
        });
    }
    // Listener para botón TEST Regresar
    if (hostReturnTestBtn) {
        hostReturnTestBtn.addEventListener('click', () => {
            showScreen(joinScreen);
        });
    }
    // Listener para botón Eliminar Participante
    if (deletePlayerBtn) {
        deletePlayerBtn.addEventListener('click', () => {
            if (selectedPlayer && selectedPlayer.parentElement.id === 'host-player-pool') {
                playerToDelete = selectedPlayer;
                if (confirmDeleteModal) confirmDeleteModal.style.display = 'flex';
            } else {
                console.warn("Intento de eliminar sin jugador seleccionado en el pool.");
            }
        });
    }

    // LISTENERS MODAL GRUPO (HOST)
    if (modalCloseBtn) modalCloseBtn.addEventListener('click', () => { groupModal.style.display = 'none'; });
    if (groupModal) groupModal.addEventListener('click', (e) => { if (e.target.id === 'group-modal-overlay') groupModal.style.display = 'none'; });

    // LISTENERS MODAL TAMAÑO GRUPO (HOST)
    if (editGroupSizeBtn) { editGroupSizeBtn.addEventListener('click', () => { if (groupSizeDisplay) groupSizeDisplay.textContent = maxPlayersPerGroup; if (groupSizeModal) groupSizeModal.style.display = 'flex'; }); }
    if (groupSizeCloseBtn) {
        groupSizeCloseBtn.addEventListener('click', () => {
            if (groupSizeModal) groupSizeModal.style.display = 'none';
            // ACTUALIZAR VISTA JUGADOR (si está en lobby)
            if (startScreen && startScreen.classList.contains('active')) {
                setupPlayerLobby();
            }
        });
    }
    if (groupSizeModal) { groupSizeModal.addEventListener('click', (e) => { if (e.target.id === 'group-size-modal-overlay') groupSizeModal.style.display = 'none'; }); }
    if (increaseGroupSizeBtn) { increaseGroupSizeBtn.addEventListener('click', () => { maxPlayersPerGroup++; if (groupSizeDisplay) groupSizeDisplay.textContent = maxPlayersPerGroup; }); }
    if (decreaseGroupSizeBtn) { decreaseGroupSizeBtn.addEventListener('click', () => { if (maxPlayersPerGroup > 1) { maxPlayersPerGroup--; if (groupSizeDisplay) groupSizeDisplay.textContent = maxPlayersPerGroup; } }); }

    // LISTENERS MODAL CONFIRMACIÓN ELIMINAR (HOST)
    if (confirmDeleteYesBtn) {
        confirmDeleteYesBtn.addEventListener('click', () => {
            if (playerToDelete) playerToDelete.remove();
            playerToDelete = null;
            selectedPlayer = null;
            if (deletePlayerBtn) deletePlayerBtn.disabled = true;
            if (confirmDeleteModal) confirmDeleteModal.style.display = 'none';
        });
    }
    if (confirmDeleteNoBtn) {
        confirmDeleteNoBtn.addEventListener('click', () => {
            playerToDelete = null;
            if (confirmDeleteModal) confirmDeleteModal.style.display = 'none';
        });
    }
    if (confirmDeleteModal) {
        confirmDeleteModal.addEventListener('click', (e) => {
            if (e.target.id === 'confirm-delete-modal-overlay') {
                playerToDelete = null;
                confirmDeleteModal.style.display = 'none';
            }
        });
    }


    // --- LISTENERS PARA SELECCIÓN/VISTA DE GRUPO DEL JUGADOR ---
    // (La selección de grupo se añade dinámicamente en setupPlayerLobby)

    // Listener para botón "Salir de la Partida" (ID: leave-lobby-button)
    if (leaveLobbyButton) {
        leaveLobbyButton.addEventListener('click', () => {
            console.log("Botón Salir de la Partida clickeado");

            // Limpiar temporizadores y estados del lobby
            if (gameStartTimer) {
                clearTimeout(gameStartTimer);
                gameStartTimer = null;
            }
            playerIsReady = false;
            if (readyButton) {
                readyButton.innerText = "LISTO";
                readyButton.classList.remove('waiting', 'btn-warning');
                readyButton.classList.add('btn-success');
            }

            // --- AÑADIR ESTA LÍNEA (LA SOLUCIÓN) ---
            restoreJoinButton();
            // --- FIN DE LA SOLUCIÓN ---

            slideScreenReverse(startScreen, joinScreen); // Volver a la pantalla de unirse
        });
    }

    // --- INICIALIZACIÓN ---
    showScreen(joinScreen); // Muestra la pantalla inicial
    initializeHostScreen(); // Configura la lógica interactiva del host

    // --- LÓGICA DE JUEGO (ANFITRIÓN) ---

    function hostStartGame() {
        isHost = true;
        console.log("Host ha iniciado la partida.");
        currentQuestionIndex = 0; // Usamos el índice global
        hostShowQuestion();
    }

    function hostShowQuestion() {
        // 1. Limpiar estado anterior
        if (hostNextQButton) hostNextQButton.classList.add('hidden');
        if (hostQuestionTimer) clearTimeout(hostQuestionTimer);
        if (hostTimerInterval) clearInterval(hostTimerInterval);
        if (hostQAnswerGrid) {
            hostQAnswerGrid.innerHTML = '';
            hostQAnswerGrid.classList.remove('showing-results');
        }
        if (hostQFeedback) hostQFeedback.textContent = "Esperando respuestas...";

        // 2. Usar las transiciones del jugador
        if (questionnaireName) questionnaireName.innerText = questionnaireTitle;
        if (transitionTitle) {
            if (currentQuestionIndex === 0) transitionTitle.innerText = "COMIENZA LA PARTIDA";
            else transitionTitle.innerText = `PREGUNTA ${currentQuestionIndex + 1}`;
        }
        if (transitionScreen) {
            transitionScreen.classList.remove('animate-slide-across');
            showScreen(transitionScreen);
            void transitionScreen.offsetWidth;
            transitionScreen.classList.add('animate-slide-across');
        }

        // 3. Obtener pregunta
        const question = questions[currentQuestionIndex];
        if (!question) {
            hostEndGame();
            return;
        }

        // 4. Poblar la pantalla del host
        if (hostQText) hostQText.innerText = question.question;

        question.answers.forEach(answer => {
            const button = document.createElement('button');
            button.classList.add('btn');

            // Contenido del botón
            const answerText = document.createElement('span');
            answerText.textContent = answer.text;
            button.appendChild(answerText);

            // Span para el contador (oculto)
            const answerCount = document.createElement('span');
            answerCount.className = 'answer-count';
            answerCount.textContent = '0'; // Valor inicial
            button.appendChild(answerCount);

            if (answer.correct) button.dataset.correct = true;
            if (hostQAnswerGrid) hostQAnswerGrid.appendChild(button);
        });

        // 5. Iniciar temporizadores
        let timeLeft = HOST_QUESTION_TIME / 1000;
        if (hostQTimer) hostQTimer.textContent = timeLeft;

        hostTimerInterval = setInterval(() => {
            timeLeft--;
            if (hostQTimer) hostQTimer.textContent = timeLeft;
            if (timeLeft <= 0) {
                clearInterval(hostTimerInterval);
            }
        }, 1000);

        // Temporizador principal de 10 segundos
        hostQuestionTimer = setTimeout(() => {
            hostShowResults(question);
        }, HOST_QUESTION_TIME);

        // 6. Mostrar la pantalla del host después de la transición
        setTimeout(() => {
            showScreen(hostQuestionScreen);
        }, TRANSITION_ANIMATION_TIME);
    }

    function hostShowResults(question) {
        if (hostTimerInterval) clearInterval(hostTimerInterval);
        if (hostQFeedback) hostQFeedback.textContent = "Resultados de la pregunta. Haz clic en 'Siguiente'.";
        if (hostQAnswerGrid) hostQAnswerGrid.classList.add('showing-results');

        // SIMULACIÓN de recuento de votos (valores fijos)
        const totalPlayers = 7; // Simulación basada en los 7 perfiles
        let votes = [
            Math.floor(Math.random() * (totalPlayers + 1)), 0, 0, 0
        ];
        votes[1] = Math.floor(Math.random() * (totalPlayers - votes[0] + 1));
        votes[2] = Math.floor(Math.random() * (totalPlayers - votes[0] - votes[1] + 1));
        votes[3] = totalPlayers - votes[0] - votes[1] - votes[2];

        // Re-barajar los votos
        votes.sort(() => Math.random() - 0.5);

        // Aplicar clases y contadores
        const buttons = hostQAnswerGrid.querySelectorAll('.btn');
        buttons.forEach((button, index) => {
            if (!question.answers[index]) return;
            const answer = question.answers[index];
            const countSpan = button.querySelector('.answer-count');

            if (countSpan) countSpan.textContent = votes[index];

            if (answer.correct) {
                button.classList.add('correct');
            } else {
                button.classList.add('incorrect');
            }
            button.disabled = true;
        });

        // --- LÓGICA MODIFICADA ---
        // Ya no usamos setTimeout para avanzar.
        // En lugar de eso, mostramos el botón de siguiente.
        if (hostNextQButton) {
            // Si es la última pregunta, cambiamos el texto del botón
            if (currentQuestionIndex >= questions.length - 1) {
                hostNextQButton.textContent = "Ver Resultados Finales";
            } else {
                hostNextQButton.textContent = "Siguiente Pregunta";
            }
            hostNextQButton.classList.remove('hidden');
        }
    }

    function hostGoToNextStep() {
        // 1. Ocultar el botón
        if (hostNextQButton) hostNextQButton.classList.add('hidden');

        // 2. Incrementar índice
        currentQuestionIndex++;

        // 3. Decidir el siguiente paso (Esta era la lógica del antiguo setTimeout)
        if (currentQuestionIndex < questions.length) {
            hostShowQuestion(); // Ir a la siguiente pregunta
        } else {
            hostEndGame(); // Ir al final
        }
    }

    function hostEndGame() {
        if (hostNextQButton) hostNextQButton.textContent = "Siguiente Pregunta"; // Resetear texto
        // Usar la transición de fin
        if (endTransitionScreen) {
            endTransitionScreen.classList.remove('animate-slide-across');
            showScreen(endTransitionScreen);
            void endTransitionScreen.offsetWidth;
            endTransitionScreen.classList.add('animate-slide-across');
        }

        // Después de la transición, volver al lobby del host
        setTimeout(() => {
            // restartGame() limpia todos los estados (incluyendo grupos)
            // y nos devuelve a joinScreen.
            // Sobreescribimos para que el host vea su pantalla de lobby.
            showScreen(podiumScreen);
        }, TRANSITION_ANIMATION_TIME);
    }

});