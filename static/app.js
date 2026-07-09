// Точка входа для фронтенд-логики (SPA)
document.addEventListener("DOMContentLoaded", () => {
    // DOM Элементы
    const authContainer = document.getElementById("auth-container");
    const appContainer = document.getElementById("app-container");
    
    const authForm = document.getElementById("auth-form");
    const authEmail = document.getElementById("auth-email");
    const authPassword = document.getElementById("auth-password");
    const authSubmitBtn = document.getElementById("auth-submit-btn");
    const authToggleBtn = document.getElementById("auth-toggle-btn");
    const authToggleText = document.getElementById("auth-toggle-text");
    const authSubtitle = document.getElementById("auth-subtitle");
    const authToggleMsg = document.getElementById("auth-toggle-msg");
    const authError = document.getElementById("auth-error");

    const userDisplayEmail = document.getElementById("user-display-email");
    const logoutBtn = document.getElementById("logout-btn");
    const refreshHistoryBtn = document.getElementById("refresh-history-btn");

    const resumeText = document.getElementById("resume-text");
    const vacancyText = document.getElementById("vacancy-text");
    const matchBtn = document.getElementById("match-btn");
    const matchError = document.getElementById("match-error");

    const resultsSection = document.getElementById("results-section");
    const scoreGauge = document.getElementById("score-gauge");
    const scoreValue = document.getElementById("score-value");
    const resCategory = document.getElementById("res-category");
    const resLevel = document.getElementById("res-level");
    const resExplanation = document.getElementById("res-explanation");

    const cntMatched = document.getElementById("cnt-matched");
    const cntMissing = document.getElementById("cnt-missing");
    const cntExtra = document.getElementById("cnt-extra");
    const listMatched = document.getElementById("list-matched");
    const listMissing = document.getElementById("list-missing");
    const listExtra = document.getElementById("list-extra");

    const historyTbody = document.getElementById("history-tbody");

    // Модальное окно
    const modalContainer = document.getElementById("modal-container");
    const modalCloseBtn = document.getElementById("modal-close-btn");
    const modalContent = document.getElementById("modal-content");

    // Состояние приложения (State)
    let isLoginMode = true;
    let jwtToken = localStorage.getItem("jwt_token");
    let userEmail = localStorage.getItem("user_email");
    let matchHistoryCache = []; // Кэш для деталей истории

    // Инициализация
    if (jwtToken && userEmail) {
        showApp();
    } else {
        showAuth();
    }

    // Переключение режимов: Войти / Зарегистрироваться
    authToggleBtn.addEventListener("click", (e) => {
        e.preventDefault();
        isLoginMode = !isLoginMode;
        authError.classList.add("hide");
        
        if (isLoginMode) {
            authSubtitle.textContent = "Войдите в систему для анализа резюме и вакансий";
            authSubmitBtn.querySelector(".btn-text").textContent = "Войти";
            authToggleText.textContent = "Нет аккаунта?";
            authToggleBtn.textContent = "Зарегистрироваться";
        } else {
            authSubtitle.textContent = "Создайте аккаунт, чтобы начать использование сервиса";
            authSubmitBtn.querySelector(".btn-text").textContent = "Зарегистрироваться";
            authToggleText.textContent = "Уже есть аккаунт?";
            authToggleBtn.textContent = "Войти";
        }
    });

    // Обработка отправки формы Входа / Регистрации
    authForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        authError.classList.add("hide");
        authSubmitBtn.classList.add("loading");
        authSubmitBtn.disabled = true;

        const email = authEmail.value.trim();
        const password = authPassword.value;
        const endpoint = isLoginMode ? "/auth/login" : "/auth/register";

        try {
            let response;
            if (isLoginMode) {
                // Стандартный OAuth2 Password Flow требует x-www-form-urlencoded
                const formData = new URLSearchParams();
                formData.append("username", email);
                formData.append("password", password);

                response = await fetch(endpoint, {
                    method: "POST",
                    headers: { "Content-Type": "application/x-www-form-urlencoded" },
                    body: formData
                });
            } else {
                response = await fetch(endpoint, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password })
                });
            }

            const data = await response.json();

            if (!response.ok) {
                let errMsg = "Произошла ошибка";
                if (data.detail) {
                    if (typeof data.detail === "string") {
                        errMsg = data.detail;
                    } else if (Array.isArray(data.detail)) {
                        errMsg = data.detail.map(err => {
                            const field = err.loc[err.loc.length - 1];
                            return `${field}: ${err.msg}`;
                        }).join("\n");
                    }
                }
                throw new Error(errMsg);
            }

            if (isLoginMode) {
                // Успешный вход
                jwtToken = data.access_token;
                userEmail = email;
                localStorage.setItem("jwt_token", jwtToken);
                localStorage.setItem("user_email", userEmail);
                showApp();
            } else {
                // Успешная регистрация
                isLoginMode = true;
                authSubtitle.textContent = "Регистрация успешна! Войдите, используя свои данные.";
                authSubmitBtn.querySelector(".btn-text").textContent = "Войти";
                authToggleText.textContent = "Нет аккаунта?";
                authToggleBtn.textContent = "Зарегистрироваться";
                authForm.reset();
            }
        } catch (err) {
            authError.style.whiteSpace = "pre-wrap";
            authError.textContent = err.message;
            authError.classList.remove("hide");
        } finally {
            authSubmitBtn.classList.remove("loading");
            authSubmitBtn.disabled = false;
        }
    });

    // Выход
    logoutBtn.addEventListener("click", () => {
        localStorage.removeItem("jwt_token");
        localStorage.removeItem("user_email");
        jwtToken = null;
        userEmail = null;
        showAuth();
        authForm.reset();
    });

    // Сравнение вакансии и резюме
    matchBtn.addEventListener("click", async () => {
        matchError.classList.add("hide");
        const rText = resumeText.value.trim();
        const vText = vacancyText.value.trim();

        if (rText.length < 10 || vText.length < 10) {
            matchError.textContent = "Минимальная длина текстов должна быть не менее 10 символов.";
            matchError.classList.remove("hide");
            return;
        }

        matchBtn.classList.add("loading");
        matchBtn.disabled = true;

        try {
            const response = await fetch("/match", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${jwtToken}`
                },
                body: JSON.stringify({
                    resume_text: rText,
                    vacancy_text: vText
                })
            });

            const data = await response.json();

            if (response.status === 401) {
                logoutBtn.click();
                throw new Error("Ваша сессия истекла. Пожалуйста, войдите снова.");
            }

            if (!response.ok) {
                throw new Error(data.detail || "Произошла ошибка при расчёте совпадения.");
            }

            renderResults(data);
            loadHistory(); // Обновляем историю в таблице
        } catch (err) {
            matchError.textContent = err.message;
            matchError.classList.remove("hide");
        } finally {
            matchBtn.classList.remove("loading");
            matchBtn.disabled = false;
        }
    });

    // Обновление истории по кнопке
    refreshHistoryBtn.addEventListener("click", loadHistory);

    // Модальное окно: Закрытие
    modalCloseBtn.addEventListener("click", () => {
        modalContainer.classList.add("hide");
    });
    modalContainer.addEventListener("click", (e) => {
        if (e.target === modalContainer) {
            modalContainer.classList.add("hide");
        }
    });

    // Вспомогательные функции переключения экранов
    function showApp() {
        authContainer.classList.remove("active");
        appContainer.classList.remove("hide");
        userDisplayEmail.textContent = userEmail;
        resultsSection.classList.add("hide");
        resumeText.value = "";
        vacancyText.value = "";
        loadHistory();
    }

    function showAuth() {
        appContainer.classList.add("hide");
        authContainer.classList.add("active");
    }

    // Отрисовка результатов сравнения
    function renderResults(data) {
        resultsSection.classList.remove("hide");
        
        // Match Score (0.0 - 1.0)
        const scorePercent = Math.round(data.match_score * 100);
        scoreValue.textContent = `${scorePercent}%`;
        
        // Gauge анимация
        const circumference = 314.16; // 2 * pi * r(50)
        const offset = circumference - (circumference * scorePercent) / 100;
        scoreGauge.style.strokeDashoffset = offset;

        // Настройка цвета круга
        if (scorePercent >= 75) {
            scoreGauge.style.stroke = "var(--success-color)";
        } else if (scorePercent >= 45) {
            scoreGauge.style.stroke = "var(--warning-color)";
        } else {
            scoreGauge.style.stroke = "var(--danger-color)";
        }

        // Категория и Уровень вакансии/резюме
        resCategory.textContent = data.resume_analysis.category.toUpperCase();
        resLevel.textContent = data.resume_analysis.level.toUpperCase();
        resExplanation.textContent = data.explanation;

        // Рендеринг тегов навыков
        renderSkillTags(listMatched, data.matched_skills, cntMatched);
        renderSkillTags(listMissing, data.missing_skills, cntMissing);
        renderSkillTags(listExtra, data.extra_resume_skills, cntExtra);

        // Плавная прокрутка к результатам
        resultsSection.scrollIntoView({ behavior: "smooth" });
    }

    function renderSkillTags(container, list, counterEl) {
        container.innerHTML = "";
        counterEl.textContent = list.length;
        
        if (list.length === 0) {
            container.innerHTML = '<span class="skill-tag" style="opacity:0.6; font-style:italic;">Навыки отсутствуют</span>';
            return;
        }

        list.forEach(skill => {
            const span = document.createElement("span");
            span.className = "skill-tag";
            span.textContent = skill;
            container.appendChild(span);
        });
    }

    // Загрузка истории сравнений
    async function loadHistory() {
        try {
            const response = await fetch("/match/history?limit=10&offset=0", {
                headers: {
                    "Authorization": `Bearer ${jwtToken}`
                }
            });

            if (!response.ok) {
                if (response.status === 401) {
                    logoutBtn.click();
                }
                return;
            }

            const data = await response.json();
            matchHistoryCache = data.items; // сохраняем в кэш для модалки
            renderHistoryTable(data.items);
        } catch (err) {
            console.error("Ошибка загрузки истории:", err);
        }
    }

    // Рендер таблицы истории
    function renderHistoryTable(items) {
        if (!items || items.length === 0) {
            historyTbody.innerHTML = `
                <tr>
                    <td colspan="6" class="table-empty">История пуста. Запустите сравнение резюме и вакансии.</td>
                </tr>
            `;
            return;
        }

        historyTbody.innerHTML = "";
        items.forEach((item) => {
            const tr = document.createElement("tr");
            
            const date = new Date(item.created_at).toLocaleString("ru-RU", {
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit"
            });

            const scorePercent = Math.round(item.match_score * 100);
            let scoreClass = "score-low";
            if (scorePercent >= 75) scoreClass = "score-high";
            else if (scorePercent >= 45) scoreClass = "score-mid";

            // Сокращаем навыки для отображения в таблице
            const skillsShort = item.matched_skills.slice(0, 5).join(", ");
            const skillsDisplay = item.matched_skills.length > 5 
                ? `${skillsShort}... (+${item.matched_skills.length - 5})` 
                : skillsShort || "—";

            tr.innerHTML = `
                <td>${date}</td>
                <td><span class="badge badge-info">${item.resume_analysis.category.toUpperCase()}</span></td>
                <td>${item.resume_analysis.level.toUpperCase()} / ${item.vacancy_analysis.level.toUpperCase()}</td>
                <td><small>${skillsDisplay}</small></td>
                <td><span class="score-badge ${scoreClass}">${scorePercent}%</span></td>
                <td><button class="btn btn-secondary btn-sm view-details-btn" data-id="${item.id}">Детали</button></td>
            `;

            historyTbody.appendChild(tr);
        });

        // Навешиваем клики на кнопки деталей
        document.querySelectorAll(".view-details-btn").forEach(btn => {
            btn.addEventListener("click", (e) => {
                const id = e.target.getAttribute("data-id");
                showDetailsModal(id);
            });
        });
    }

    // Отображение деталей истории в модальном окне
    function showDetailsModal(id) {
        const item = matchHistoryCache.find(x => x.id === id);
        if (!item) return;

        modalContent.innerHTML = `
            <div class="results-grid" style="margin-top:0;">
                <div class="metrics-summary">
                    <div class="gauge-wrapper">
                        <svg class="gauge" viewBox="0 0 120 120">
                            <circle class="gauge-bg" cx="60" cy="60" r="50"></circle>
                            <circle class="gauge-fill" style="stroke-dasharray: 314.16; stroke-dashoffset: ${314.16 - (314.16 * Math.round(item.match_score * 100)) / 100}; stroke: ${item.match_score >= 0.75 ? 'var(--success-color)' : item.match_score >= 0.45 ? 'var(--warning-color)' : 'var(--danger-color)'};" cx="60" cy="60" r="50"></circle>
                        </svg>
                        <div class="gauge-text">
                            <span class="gauge-value">${Math.round(item.match_score * 100)}%</span>
                            <span class="gauge-label">Match Score</span>
                        </div>
                    </div>
                    <div class="classification-tags">
                        <div class="class-card-mini">
                            <span class="mini-label">Направление</span>
                            <span class="mini-val">${item.resume_analysis.category.toUpperCase()}</span>
                        </div>
                        <div class="class-card-mini">
                            <span class="mini-label">Грейд (Резюме / Вакансия)</span>
                            <span class="mini-val">${item.resume_analysis.level.toUpperCase()} / ${item.vacancy_analysis.level.toUpperCase()}</span>
                        </div>
                    </div>
                </div>

                <div style="background: rgba(0,0,0,0.2); padding: 1.25rem; border-radius: 12px; border: 1px solid var(--card-border); max-height:220px; overflow-y:auto;">
                    <h5 style="color:var(--text-secondary); margin-bottom:0.5rem; font-size:0.85rem;">Тексты сравнения</h5>
                    <div style="margin-bottom:1rem;">
                        <strong style="font-size:0.8rem; color:#fff;">Резюме:</strong>
                        <p style="font-size:0.85rem; color:#9ca3af; margin-top:0.25rem; white-space: pre-wrap;">${escapeHtml(item.resume_text)}</p>
                    </div>
                    <div>
                        <strong style="font-size:0.8rem; color:#fff;">Вакансия:</strong>
                        <p style="font-size:0.85rem; color:#9ca3af; margin-top:0.25rem; white-space: pre-wrap;">${escapeHtml(item.vacancy_text)}</p>
                    </div>
                </div>

                <div class="skills-analysis">
                    <div class="skills-groups">
                        <div class="skills-box skills-matched">
                            <h5>Совпавшие навыки <span class="badge badge-success">${item.matched_skills.length}</span></h5>
                            <div class="skills-list">
                                ${item.matched_skills.map(s => `<span class="skill-tag">${s}</span>`).join("") || '<span class="skill-tag" style="opacity:0.6; font-style:italic;">Навыки отсутствуют</span>'}
                            </div>
                        </div>
                        <div class="skills-box skills-missing">
                            <h5>Отсутствуют в резюме <span class="badge badge-danger">${item.missing_skills.length}</span></h5>
                            <div class="skills-list">
                                ${item.missing_skills.map(s => `<span class="skill-tag">${s}</span>`).join("") || '<span class="skill-tag" style="opacity:0.6; font-style:italic;">Навыки отсутствуют</span>'}
                            </div>
                        </div>
                        <div class="skills-box skills-extra">
                            <h5>Дополнительные навыки <span class="badge badge-info">${item.extra_resume_skills.length}</span></h5>
                            <div class="skills-list">
                                ${item.extra_resume_skills.map(s => `<span class="skill-tag">${s}</span>`).join("") || '<span class="skill-tag" style="opacity:0.6; font-style:italic;">Навыки отсутствуют</span>'}
                            </div>
                        </div>
                    </div>
                </div>

                <div class="explanation-box" style="margin-top:0;">
                    <h4>Объяснение модели</h4>
                    <p>${item.explanation}</p>
                </div>
            </div>
        `;

        modalContainer.classList.remove("hide");
    }

    // Хелпер защиты от XSS
    function escapeHtml(text) {
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
