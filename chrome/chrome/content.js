// Learning Assistant - Content Script
// 在线编程学习平台自动答题助手

class LearningAssistant {
    constructor() {
        this.socket = null;
        this.isVisible = false;
        this.isMinimized = false;
        this.generatedCode = null;
        this.currentQuestionContent = null;
        this.isInputInProgress = false;
        this.shouldShowProgress = false;
        this.virtualProgress = 0;
        this.serverProgress = 0;
        this.virtualProgressTimer = null;
        this.serverUrl = 'ws://localhost:8000';
        this.retryCount = 0;
        this.maxRetries = 3;
        this.currentTab = 'auto';
        this.manualDisconnect = false;
        this.init();
    }

    async init() {
        this.createTopTipOverlay();
        this.createFloatingWindow();
        this.attachEventListeners();
        this._setupResizeHandle();
        await this.loadSettings();
        this.extractPageContent();
        await this.autoConnect();
        this.show();
    }

    // ========== Settings ==========
    async loadSettings() {
        // 先触发后台脚本同步配置文件
        try {
            const resp = await new Promise((resolve) => {
                chrome.runtime.sendMessage({ action: 'syncConfig' }, resolve);
            });
            if (resp && resp.serverUrl) {
                this.serverUrl = resp.serverUrl;
                return;
            }
        } catch (e) {
            // 消息发送失败，回退到 storage
        }

        // 回退：从 storage 读取
        return new Promise((resolve) => {
            chrome.storage.local.get(['serverUrl'], (result) => {
                if (result.serverUrl) {
                    this.serverUrl = result.serverUrl;
                }
                resolve();
            });
        });
    }

    // ========== Top Tip Overlay ==========
    createTopTipOverlay() {
        this.topTipOverlay = document.createElement('div');
        this.topTipOverlay.className = 'la-top-tip-overlay';
        this.topTipOverlay.innerHTML = `
            <div class="la-top-tip-bar">
                <span class="la-top-tip-icon">◉</span>
                <span class="la-top-tip-text">代码输入中</span>
                <div class="la-top-tip-progress">
                    <div class="la-top-tip-progress-bar" style="width:0%"></div>
                </div>
                <span class="la-top-tip-percent">0%</span>
                <button class="la-top-tip-cancel">取消</button>
            </div>
        `;
        document.body.appendChild(this.topTipOverlay);
        this.topTipProgressBar = this.topTipOverlay.querySelector('.la-top-tip-progress-bar');
        this.topTipPercent = this.topTipOverlay.querySelector('.la-top-tip-percent');
        this.topTipText = this.topTipOverlay.querySelector('.la-top-tip-text');
    }

    showTopTip(text) {
        this.topTipText.textContent = text || '代码输入中';
        this.topTipOverlay.classList.add('la-visible');
        this.shouldShowProgress = true;
        this.startVirtualProgress();
    }

    hideTopTip() {
        this.topTipOverlay.classList.remove('la-visible');
        this.shouldShowProgress = false;
        this.stopVirtualProgress();
        this.updateProgress(0);
    }

    startVirtualProgress() {
        this.virtualProgress = 0;
        this.serverProgress = 0;
        this.stopVirtualProgress();
        this.virtualProgressTimer = setInterval(() => {
            if (this.virtualProgress < 90) {
                this.virtualProgress += 90 / 100;
                const display = this.serverProgress > 0
                    ? Math.round(this.serverProgress)
                    : Math.round(this.virtualProgress);
                this.updateProgress(display);
            }
        }, 100);
    }

    stopVirtualProgress() {
        if (this.virtualProgressTimer) {
            clearInterval(this.virtualProgressTimer);
            this.virtualProgressTimer = null;
        }
    }

    updateProgress(percent) {
        const p = Math.min(100, Math.max(0, percent));
        if (this.topTipProgressBar) this.topTipProgressBar.style.width = p + '%';
        if (this.topTipPercent) this.topTipPercent.textContent = Math.round(p) + '%';
    }

    // ========== Floating Window ==========
    createFloatingWindow() {
        this.container = document.createElement('div');
        this.container.className = 'la-container';
        this.container.innerHTML = `
            <div class="la-header" id="la-drag-handle">
                <div class="la-header-left">
                    <span class="la-header-dot">◉</span>
                    <span class="la-header-title">学习助手</span>
                    <span class="la-header-version">v1.0</span>
                </div>
                <div class="la-header-right">
                    <button class="la-header-btn la-minimize-btn" title="最小化">—</button>
                    <button class="la-header-btn la-close-btn" title="关闭">×</button>
                </div>
            </div>
            <div class="la-body">
                <div class="la-status-bar">
                    <span class="la-status-indicator la-status-disconnected">
                        <span class="la-status-dot"></span>
                        <span class="la-status-text">未连接</span>
                    </span>
                    <span class="la-model-info">模型: --</span>
                    <select class="la-lang-select">
                        <option value="python">Python</option>
                        <option value="javascript">JavaScript</option>
                        <option value="java">Java</option>
                        <option value="cpp">C++</option>
                        <option value="c">C</option>
                        <option value="csharp">C#</option>
                    </select>
                </div>
                <div class="la-tabs">
                    <div class="la-tab la-tab-active" data-tab="auto">▶ 自动答题</div>
                    <div class="la-tab" data-tab="manual">✎ 手动输入</div>
                </div>
                <div class="la-tab-content la-tab-auto la-tab-visible" data-tab="auto">
                    <button class="la-btn la-btn-auto la-btn-full" title="F6">
                        ⚡ 一键获取并粘贴 <span class="la-hotkey">F6</span>
                    </button>
                    <button class="la-btn la-btn-warning la-btn-full la-btn-correct" title="F5">
                        🔄 智能纠错 <span class="la-hotkey">F5</span>
                    </button>
                    <div class="la-btn-row">
                        <button class="la-btn la-btn-ghost la-btn-half la-btn-simulate">模拟键盘输入</button>
                        <button class="la-btn la-btn-ghost la-btn-half la-btn-cancel-input" disabled>取消输入</button>
                    </div>
                    <div class="la-btn-row">
                        <button class="la-btn la-btn-ghost la-btn-half la-btn-disconnect">断开连接</button>
                        <button class="la-btn la-btn-ghost la-btn-half la-btn-reconnect" style="display:none">重新连接</button>
                    </div>
                </div>
                <div class="la-tab-content la-tab-manual" data-tab="manual">
                    <label class="la-label">获取题目</label>
                    <textarea class="la-textarea la-question-input" placeholder="点击获取题目按钮获取内容..." rows="4"></textarea>
                    <button class="la-btn la-btn-primary la-btn-full la-btn-fetch-question">
                        📋 获取题目
                    </button>
                    <button class="la-btn la-btn-primary la-btn-full la-btn-manual-generate" title="F3" style="margin-top:8px">
                        ✎ 生成代码 <span class="la-hotkey">F3</span>
                    </button>
                    <div class="la-btn-row">
                        <button class="la-btn la-btn-ghost la-btn-half la-btn-simulate">模拟键盘输入</button>
                        <button class="la-btn la-btn-ghost la-btn-half la-btn-cancel-input" disabled>取消输入</button>
                    </div>
                </div>
                <div class="la-resizable-area">
                    <label class="la-label">AI 生成代码</label>
                    <textarea class="la-textarea la-code-text" rows="4" placeholder="等待生成..."></textarea>
                    <div class="la-code-actions">
                        <button class="la-btn la-btn-ghost la-btn-sm la-btn-copy">复制代码</button>
                        <button class="la-btn la-btn-ghost la-btn-sm la-btn-paste-code">粘贴到编辑器</button>
                        <button class="la-btn la-btn-ghost la-btn-sm la-btn-regenerate">重新生成</button>
                        <button class="la-btn la-btn-ghost la-btn-sm la-btn-sync">同步到桌面端</button>
                    </div>
                </div>
                <div class="la-resize-handle" title="拖拽调整大小"></div>
                <div class="la-log-section">
                    <div class="la-log-header">
                        <span>操作记录</span>
                        <button class="la-btn-clear-log">清空</button>
                    </div>
                    <div class="la-log-area"></div>
                </div>
            </div>
        `;
        document.body.appendChild(this.container);

        // Cache DOM references
        this.statusDot = this.container.querySelector('.la-status-dot');
        this.statusText = this.container.querySelector('.la-status-text');
        this.modelInfo = this.container.querySelector('.la-model-info');
        this.langSelect = this.container.querySelector('.la-lang-select');
        this.codePreview = this.container.querySelector('.la-code-text');
        this.logArea = this.container.querySelector('.la-log-area');
        this.questionInput = this.container.querySelector('.la-question-input');
    }

    // ========== Event Listeners ==========
    attachEventListeners() {
        // Drag
        this._setupDrag();
        // Resize
        this._setupResize();
        // Header buttons
        this.container.querySelector('.la-minimize-btn').addEventListener('click', () => this.toggleMinimize());
        this.container.querySelector('.la-close-btn').addEventListener('click', () => this.hide());
        // Tabs
        this.container.querySelectorAll('.la-tab').forEach(tab => {
            tab.addEventListener('click', () => this.switchTab(tab.dataset.tab));
        });
        // Auto tab buttons
        this.container.querySelector('.la-btn-auto').addEventListener('click', () => this.autoGetAndPaste());
        this.container.querySelector('.la-btn-correct').addEventListener('click', () => this.smartCorrection());
        this.container.querySelector('.la-btn-disconnect').addEventListener('click', () => this.disconnect());
        this.container.querySelector('.la-btn-reconnect').addEventListener('click', () => this.reconnect());
        // Manual tab buttons
        this.container.querySelector('.la-btn-fetch-question').addEventListener('click', () => this.fetchQuestion());
        this.container.querySelector('.la-btn-manual-generate').addEventListener('click', () => this.manualInput());
        // Simulate and cancel buttons (both tabs)
        this.container.querySelectorAll('.la-btn-simulate').forEach(btn => {
            btn.addEventListener('click', () => this.simulateKeyboardInput());
        });
        this.container.querySelectorAll('.la-btn-cancel-input').forEach(btn => {
            btn.addEventListener('click', () => this.cancelInput());
        });
        // Cancel button on top tip
        this.topTipOverlay.querySelector('.la-top-tip-cancel').addEventListener('click', () => this.cancelInput());
        // Code result buttons
        this.container.querySelector('.la-btn-copy').addEventListener('click', () => this.copyCode());
        this.container.querySelector('.la-btn-paste-code').addEventListener('click', () => this.pasteCodeToEditor());
        this.container.querySelector('.la-btn-regenerate').addEventListener('click', () => this.regenerate());
        this.container.querySelector('.la-btn-sync').addEventListener('click', () => this.syncCodeToDesktop(this.codePreview.value));
        // Log clear
        this.container.querySelector('.la-btn-clear-log').addEventListener('click', () => this.clearLog());
        // Language select
        this.langSelect.addEventListener('change', () => {
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.socket.send(JSON.stringify({ type: 'set_language', language: this.langSelect.value }));
            }
        });
        // Hotkeys
        document.addEventListener('keydown', (e) => {
            if (!this.isVisible) return;
            if (e.key === 'F3') { e.preventDefault(); this.manualInput(); }
            if (e.key === 'F5') { e.preventDefault(); this.smartCorrection(); }
            if (e.key === 'F6') { e.preventDefault(); this.autoGetAndPaste(); }
            if (e.key === 'Escape' && this.isInputInProgress) { this.cancelInput(); }
        });
        // Listen for messages from background
        chrome.runtime.onMessage.addListener((msg) => {
            if (msg.action === 'toggleAssistant') this.toggle();
        });
    }

    _setupDrag() {
        const handle = this.container.querySelector('#la-drag-handle');
        let isDragging = false, startX, startY, startLeft, startTop;
        handle.addEventListener('mousedown', (e) => {
            if (e.target.closest('.la-header-btn')) return;
            isDragging = true;
            startX = e.clientX; startY = e.clientY;
            const rect = this.container.getBoundingClientRect();
            startLeft = rect.left; startTop = rect.top;
            document.addEventListener('mousemove', onMove);
            document.addEventListener('mouseup', onUp);
        });
        const onMove = (e) => {
            if (!isDragging) return;
            this.container.style.left = (startLeft + e.clientX - startX) + 'px';
            this.container.style.top = (startTop + e.clientY - startY) + 'px';
            this.container.style.right = 'auto';
        };
        const onUp = () => {
            isDragging = false;
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
        };
    }

    _setupResize() {
        this.container.style.resize = 'both';
        this.container.style.overflow = 'hidden';
    }

    _setupResizeHandle() {
        const handle = this.container.querySelector('.la-resize-handle');
        const resizableArea = this.container.querySelector('.la-resizable-area');
        const logSection = this.container.querySelector('.la-log-section');
        if (!handle || !resizableArea || !logSection) return;

        let isDragging = false;
        let startY = 0;
        let startHeightArea = 0;
        let startHeightLog = 0;

        // 加载保存的尺寸
        chrome.storage.local.get(['panelHeightArea', 'panelHeightLog'], (result) => {
            if (result.panelHeightArea) {
                resizableArea.style.flex = 'none';
                resizableArea.style.height = result.panelHeightArea + 'px';
            }
            if (result.panelHeightLog) {
                logSection.style.flex = 'none';
                logSection.style.height = result.panelHeightLog + 'px';
            }
        });

        handle.addEventListener('mousedown', (e) => {
            e.preventDefault();
            isDragging = true;
            startY = e.clientY;
            startHeightArea = resizableArea.offsetHeight;
            startHeightLog = logSection.offsetHeight;
            document.addEventListener('mousemove', onMove);
            document.addEventListener('mouseup', onUp);
        });

        const onMove = (e) => {
            if (!isDragging) return;
            const delta = e.clientY - startY;
            const newAreaHeight = Math.max(80, startHeightArea + delta);
            const newLogHeight = Math.max(60, startHeightLog - delta);
            resizableArea.style.flex = 'none';
            resizableArea.style.height = newAreaHeight + 'px';
            logSection.style.flex = 'none';
            logSection.style.height = newLogHeight + 'px';
        };

        const onUp = () => {
            isDragging = false;
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
            // 保存尺寸
            chrome.storage.local.set({
                panelHeightArea: resizableArea.offsetHeight,
                panelHeightLog: logSection.offsetHeight
            });
        };
    }

    // ========== Tab Switching ==========
    switchTab(tabName) {
        this.currentTab = tabName;
        this.container.querySelectorAll('.la-tab').forEach(t => {
            t.classList.toggle('la-tab-active', t.dataset.tab === tabName);
        });
        this.container.querySelectorAll('.la-tab-content').forEach(c => {
            c.classList.toggle('la-tab-visible', c.dataset.tab === tabName);
        });
    }

    // ========== Visibility ==========
    show() { this.container.style.display = 'block'; this.isVisible = true; }
    hide() { this.container.style.display = 'none'; this.isVisible = false; }
    toggle() { this.isVisible ? this.hide() : this.show(); }
    toggleMinimize() {
        this.isMinimized = !this.isMinimized;
        this.container.classList.toggle('la-minimized', this.isMinimized);
    }

    // ========== Connection State ==========
    updateConnectionState(state) {
        this.statusDot.className = 'la-status-dot';
        const disconnectBtn = this.container.querySelector('.la-btn-disconnect');
        const reconnectBtn = this.container.querySelector('.la-btn-reconnect');

        if (state === 'OPEN') {
            this.statusDot.classList.add('la-connected');
            this.statusText.textContent = '已连接';
            disconnectBtn.style.display = '';
            reconnectBtn.style.display = 'none';
        } else if (state === 'CONNECTING') {
            this.statusDot.classList.add('la-connecting');
            this.statusText.textContent = '连接中...';
            disconnectBtn.style.display = 'none';
            reconnectBtn.style.display = 'none';
        } else {
            this.statusDot.classList.add('la-disconnected');
            this.statusText.textContent = '未连接';
            disconnectBtn.style.display = 'none';
            reconnectBtn.style.display = '';
        }
    }

    // ========== WebSocket ==========
    async autoConnect() {
        if (this.manualDisconnect) return;
        this.updateConnectionState('CONNECTING');
        try {
            this.socket = new WebSocket(this.serverUrl);
            this.socket.onopen = () => {
                this.updateConnectionState('OPEN');
                this.addLog('已连接到服务器', 'success');
                this.manualDisconnect = false;
            };
            this.socket.onclose = () => {
                this.updateConnectionState('CLOSED');
                if (!this.manualDisconnect) {
                    this.addLog('与服务器断开连接，5秒后重连...', 'error');
                    setTimeout(() => this.autoConnect(), 5000);
                } else {
                    this.addLog('已断开连接', 'info');
                }
            };
            this.socket.onerror = () => {
                this.addLog('连接失败，请检查服务器是否启动', 'error');
            };
            this.socket.onmessage = (event) => this.handleMessage(event.data);
        } catch (e) {
            this.addLog('连接异常: ' + e.message, 'error');
        }
    }

    disconnect() {
        this.manualDisconnect = true;
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
        this.updateConnectionState('CLOSED');
        this.addLog('已断开连接', 'info');
    }

    async reconnect() {
        this.manualDisconnect = false;
        // 重新读取配置
        await this.loadSettings();
        this.addLog('已重新读取配置: ' + this.serverUrl, 'info');
        this.autoConnect();
    }

    handleMessage(raw) {
        try {
            const data = JSON.parse(raw);
            switch (data.type) {
                case 'server_ack':
                    this.addLog(data.message || '服务器已确认', 'info');
                    break;
                case 'code_solution':
                    this.handleCodeSolution(data);
                    break;
                case 'code_revision':
                    this.handleCodeRevision(data);
                    break;
                case 'input_progress':
                    this.updateProgress(data.progress);
                    break;
                case 'input_complete':
                    this.handleInputComplete(data);
                    break;
                case 'progress_update':
                    this.serverProgress = data.progress;
                    this.updateProgress(data.progress);
                    break;
                case 'test_results_response':
                    this.handleTestResultsResponse(data);
                    break;
                case 'config_info':
                    if (data.model) {
                        this.modelInfo.textContent = '模型: ' + data.model;
                    }
                    break;
                case 'error':
                    this.addLog('错误: ' + data.message, 'error');
                    this.setInputInProgress(false);
                    break;
                default:
                    this.addLog('收到消息: ' + raw, 'info');
            }
        } catch (e) {
            this.addLog('收到: ' + raw, 'receive');
        }
    }

    handleCodeSolution(data) {
        this.generatedCode = data.code;
        this.codePreview.value = data.code;
        this.addLog('✅ 代码已生成' + (data.model_used ? ' (模型: ' + data.model_used + ')' : ''), 'success');
        this.setInputInProgress(false);
        this.hideTopTip();
        // 同步代码到桌面端
        this.syncCodeToDesktop(data.code);
    }

    handleCodeRevision(data) {
        this.generatedCode = data.code;
        this.codePreview.value = data.code;
        this.addLog('✅ 代码已修正 (第' + (data.revision_number || '') + '次纠错)', 'success');
        this.setInputInProgress(false);
        this.hideTopTip();
        // 同步代码到桌面端
        this.syncCodeToDesktop(data.code);
    }

    handleInputComplete(data) {
        if (data.success) {
            this.addLog('✅ 代码输入完成', 'success');
        } else {
            this.addLog('代码输入失败', 'error');
        }
        this.setInputInProgress(false);
        this.hideTopTip();
    }

    handleTestResultsResponse(data) {
        if (data.has_failures) {
            this.addLog('纠错: ' + (data.message || '仍有失败'), 'warning');
        } else {
            this.addLog('✅ ' + (data.message || '所有测试通过'), 'success');
        }
        this.setInputInProgress(false);
    }

    syncCodeToDesktop(code) {
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
            return; // 未连接桌面端，跳过同步
        }
        this.socket.send(JSON.stringify({
            type: 'sync_code',
            code: code
        }));
        this.addLog('代码已同步到桌面端', 'info');
    }

    cancelInput() {
        if (!this.isInputInProgress) return;
        // 通知服务器取消
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({ type: 'cancel_request' }));
        }
        this.setInputInProgress(false);
        this.hideTopTip();
        this.stopVirtualProgress();
        this.addLog('已取消操作', 'warning');
    }

    simulateKeyboardInput() {
        // 获取AI生成代码框的内容
        const code = this.codePreview.value;
        if (!code) {
            this.addLog('AI生成代码框为空，请先生成代码', 'warning');
            return;
        }
        // 发送模拟输入请求到桌面端
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                type: 'simulate_input',
                code: code,
                language: this.langSelect.value
            }));
            this.setInputInProgress(true);
            this.showTopTip('模拟键盘输入中');
            this.addLog('开始模拟键盘输入...', 'info');
        } else {
            this.addLog('未连接到桌面端', 'error');
        }
    }

    fetchQuestion() {
        // 清空代码预览框
        this.codePreview.value = '';
        this.generatedCode = '';
        // 调用页面内容提取
        const content = this.extractPageContent();
        if (content) {
            this.questionInput.value = content;
            this.addLog('题目内容已获取', 'success');
        } else {
            this.addLog('未找到题目内容，请手动输入', 'warning');
            this.questionInput.focus();
        }
    }

    setInputInProgress(val) {
        this.isInputInProgress = val;
        const btns = this.container.querySelectorAll('.la-btn');
        btns.forEach(b => {
            // 取消输入按钮在输入进行中时保持启用
            if (b.classList.contains('la-btn-cancel-input')) {
                b.disabled = !val;
            } else {
                b.disabled = val;
            }
        });
    }

    // ========== Content Extraction ==========
    extractPageContent() {
        const selectors = [
            '.tab-panel-body___iueV_.markdown-body.mdBody___raKXb',
            '.markdown-body', '.tab-panel-body',
            '.problem-content', '.question-content',
            '.problem-description', '.shixun-content'
        ];
        let content = '';
        for (const sel of selectors) {
            const el = document.querySelector(sel);
            if (el && el.innerText.trim().length > 50) {
                content = el.innerText.replace(/\s+/g, ' ').trim();
                break;
            }
        }
        // Fallback: scan divs
        if (!content) {
            const candidates = document.querySelectorAll('div, section, article');
            let best = '';
            for (const el of candidates) {
                const text = el.innerText || '';
                if (text.length > 200 && text.length > best.length) {
                    if (/题目|问题|描述|description|problem/i.test(text)) {
                        best = text;
                    }
                }
            }
            content = best.replace(/\s+/g, ' ').trim();
        }
        this.currentQuestionContent = content;
        return content;
    }

    async enrichContentWithImageOCR(content) {
        const images = this.extractImageUrlsFromElements(document.querySelectorAll('.markdown-body img, .problem-content img, .question-content img'));
        if (images.length === 0) return content;
        let ocrText = '';
        for (const url of images.slice(0, 5)) {
            try {
                const result = await this.ocrImageByApi(url);
                if (result) ocrText += '\n[图片文字] ' + result;
            } catch (e) { /* skip */ }
        }
        return content + ocrText;
    }

    extractImageUrlsFromElements(elements) {
        const urls = [];
        elements.forEach(el => {
            const src = el.src || el.getAttribute('data-src');
            if (src && src.startsWith('http')) urls.push(src);
        });
        return urls;
    }

    async ocrImageByApi(imageUrl) {
        try {
            const resp = await fetch('https://ocr.yhsun.cn/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: imageUrl }),
                signal: AbortSignal.timeout(15000)
            });
            const data = await resp.json();
            return data.text || data.result || '';
        } catch (e) {
            return '';
        }
    }

    // ========== Editor Code Reading ==========
    extractCurrentEditorCode() {
        // Try page context (Monaco API)
        let code = this._readFromMonacoAPI();
        if (code) return code;
        // DOM fallback
        code = this._readFromDOM();
        return code || '';
    }

    _readFromMonacoAPI() {
        try {
            if (typeof window.monaco !== 'undefined' && window.monaco.editor) {
                const editors = window.monaco.editor.getEditors();
                if (editors.length === 0) return null;
                // Pick best editor
                const editor = this._pickMonacoEditor(editors);
                return editor.getValue();
            }
        } catch (e) { /* fallback */ }
        return null;
    }

    _pickMonacoEditor(editors) {
        // 1. Active element editor
        for (const ed of editors) {
            try {
                if (ed.hasTextFocus && ed.hasTextFocus()) return ed;
            } catch (e) { /* ignore */ }
        }
        // 2. Largest visible editor
        let best = editors[0];
        let bestArea = 0;
        for (const ed of editors) {
            try {
                const dom = ed.getDomNode();
                if (dom) {
                    const rect = dom.getBoundingClientRect();
                    const area = rect.width * rect.height;
                    if (area > bestArea && rect.width > 0) {
                        bestArea = area;
                        best = ed;
                    }
                }
            } catch (e) { /* ignore */ }
        }
        return best;
    }

    _readFromDOM() {
        // Monaco DOM
        const monacoEl = document.querySelector('.monaco-editor .view-lines');
        if (monacoEl && monacoEl.innerText.trim()) return monacoEl.innerText;
        // CodeMirror
        const cmEl = document.querySelector('.CodeMirror-code');
        if (cmEl && cmEl.innerText.trim()) return cmEl.innerText;
        // Ace
        const aceEl = document.querySelector('.ace_text-layer');
        if (aceEl && aceEl.innerText.trim()) return aceEl.innerText;
        // Textarea
        const textareas = Array.from(document.querySelectorAll('textarea'));
        if (textareas.length > 0) {
            textareas.sort((a, b) => this.editorElementScore(b) - this.editorElementScore(a));
            const best = textareas[0];
            if (this.editorElementScore(best) > 0 && best.value.trim()) return best.value;
        }
        // pre code
        const pres = document.querySelectorAll('pre code, pre');
        let longest = '';
        pres.forEach(p => {
            const t = p.innerText || '';
            if (t.length > longest.length) longest = t;
        });
        return longest;
    }

    editorElementScore(el) {
        let score = 0;
        const id = (el.id || '').toLowerCase();
        const cls = (el.className || '').toLowerCase();
        const name = (el.name || '').toLowerCase();
        const placeholder = (el.placeholder || '').toLowerCase();
        const combined = id + cls + name + placeholder;
        if (/editor|code|monaco/.test(combined)) score += 2;
        if (el.tagName === 'TEXTAREA') score += 1;
        const rect = el.getBoundingClientRect();
        const area = rect.width * rect.height;
        if (area > 100000) score += 3;
        else if (area > 50000) score += 2;
        else if (area > 10000) score += 1;
        const val = el.value || '';
        if (/[{}();]/.test(val) || /\b(class|def|function|import)\b/.test(val)) score += 4;
        if (/search|查询|搜索/.test(combined)) score -= 8;
        return score;
    }

    // ========== Code Writing (5-layer fallback) ==========
    isVisibleElement(el) {
        if (!el) return false;
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
    }

    pickBestMonacoEditor(editors) {
        const active = document.activeElement;
        const visibleEditors = (editors || []).filter(editor => {
            try {
                const node = editor.getDomNode && editor.getDomNode();
                return node && this.isVisibleElement(node);
            } catch (e) { return false; }
        });

        if (!visibleEditors.length) return null;

        const activeMatch = visibleEditors.find(editor => {
            try {
                const node = editor.getDomNode && editor.getDomNode();
                return node && active && node.contains(active);
            } catch (e) { return false; }
        });
        if (activeMatch) return activeMatch;

        const focusedMatch = visibleEditors.find(editor => {
            try { return editor.hasTextFocus && editor.hasTextFocus(); } catch (e) { return false; }
        });
        if (focusedMatch) return focusedMatch;

        visibleEditors.sort((a, b) => {
            const an = a.getDomNode && a.getDomNode();
            const bn = b.getDomNode && b.getDomNode();
            const aRect = an ? an.getBoundingClientRect() : { width: 0, height: 0 };
            const bRect = bn ? bn.getBoundingClientRect() : { width: 0, height: 0 };
            return (bRect.width * bRect.height) - (aRect.width * aRect.height);
        });

        return visibleEditors[0] || null;
    }

    async setCodeToPageEditor(code) {
        const hasMonacoDom = !!document.querySelector('.monaco-editor');

        // Layer 0: Page context (Monaco API)
        const pageContextResult = await this.setCodeViaPageContext(code);
        if (pageContextResult.ok) return true;

        // Monaco 页面只尝试 Monaco，避免误写到其他输入框
        if (hasMonacoDom) {
            if (this.setCodeToMonaco(code)) return true;
            return false;
        }

        // Layer 1: Monaco DOM
        if (this.setCodeToMonaco(code)) return true;
        // Layer 2: CodeMirror
        if (this.setCodeToCodeMirror(code)) return true;
        // Layer 3: Ace
        if (this.setCodeToAce(code)) return true;
        // Layer 4: Textarea
        if (this.setCodeToTextarea(code)) return true;
        // Layer 5: ContentEditable
        if (this.setCodeToContentEditable(code)) return true;

        // All failed - request desktop keyboard input
        this.requestDesktopInput(code);
        return false;
    }

    async setCodeViaPageContext(code) {
        return new Promise((resolve) => {
            const channel = `la-code-set-result-${Date.now()}-${Math.random().toString(36).slice(2)}`;
            const timeoutMs = 2500;
            let settled = false;
            let timer = null;

            const finish = (payload) => {
                if (settled) return;
                settled = true;
                if (timer) {
                    clearTimeout(timer);
                    timer = null;
                }
                window.removeEventListener('message', onMessage);
                resolve(payload);
            };

            const onMessage = (event) => {
                if (event.source !== window || !event.data) return;
                if (event.data.source !== channel) return;
                finish({ ok: !!event.data.ok, reason: event.data.reason || '' });
            };

            window.addEventListener('message', onMessage);
            timer = setTimeout(() => {
                finish({ ok: false, reason: 'page_context_timeout' });
            }, timeoutMs);

            const script = document.createElement('script');
            script.textContent = `
                (async function () {
                    const source = ${JSON.stringify(channel)};
                    const code = ${JSON.stringify(code)};
                    const normalizedCode = (code || '').replace(/\\r\\n/g, '\\n');
                    let ok = false;
                    let reason = '';
                    const hasMonacoDom = !!document.querySelector('.monaco-editor');

                    function visible(el) {
                        if (!el) return false;
                        const style = window.getComputedStyle(el);
                        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
                        const rect = el.getBoundingClientRect();
                        return rect.width > 0 && rect.height > 0;
                    }

                    function areaOf(el) {
                        if (!el) return 0;
                        const rect = el.getBoundingClientRect();
                        return Math.max(0, rect.width) * Math.max(0, rect.height);
                    }

                    function pickMonacoEditor(editors) {
                        const active = document.activeElement;
                        const visibleEditors = (editors || []).filter(ed => {
                            try {
                                const node = ed.getDomNode && ed.getDomNode();
                                return node && visible(node);
                            } catch (e) { return false; }
                        });

                        if (!visibleEditors.length) return null;

                        const byActive = visibleEditors.find(ed => {
                            try {
                                const node = ed.getDomNode && ed.getDomNode();
                                return node && active && node.contains(active);
                            } catch (e) { return false; }
                        });
                        if (byActive) return byActive;

                        const byTextFocus = visibleEditors.find(ed => {
                            try { return ed.hasTextFocus && ed.hasTextFocus(); } catch (e) { return false; }
                        });
                        if (byTextFocus) return byTextFocus;

                        visibleEditors.sort((a, b) => {
                            const an = a.getDomNode && a.getDomNode();
                            const bn = b.getDomNode && b.getDomNode();
                            return areaOf(bn) - areaOf(an);
                        });

                        return visibleEditors[0] || null;
                    }

                    try {
                        // 先做一次通用清空动作
                        try {
                            const active = document.activeElement;
                            if (active && typeof active.focus === 'function') {
                                active.focus();
                                if (document.execCommand) {
                                    document.execCommand('selectAll', false, null);
                                    document.execCommand('delete', false, null);
                                }
                            }
                        } catch (e) {}

                        // Monaco
                        if (!ok && window.monaco && window.monaco.editor) {
                            try {
                                const editors = typeof window.monaco.editor.getEditors === 'function'
                                    ? (window.monaco.editor.getEditors() || [])
                                    : [];
                                let target = pickMonacoEditor(editors);
                                if (!target) {
                                    const models = typeof window.monaco.editor.getModels === 'function'
                                        ? window.monaco.editor.getModels()
                                        : [];
                                    if (models && models.length === 1 && typeof models[0].setValue === 'function') {
                                        models[0].setValue('');
                                        models[0].setValue(normalizedCode);
                                        const verify = typeof models[0].getValue === 'function'
                                            ? (models[0].getValue() || '').replace(/\\r\\n/g, '\\n')
                                            : '';
                                        if (verify === normalizedCode) {
                                            ok = true;
                                            reason = 'monaco_single_model_setValue_verified';
                                        } else {
                                            reason = 'monaco_single_model_verify_mismatch';
                                        }
                                    } else {
                                        reason = 'monaco_target_not_found';
                                    }
                                } else {
                                    target.setValue('');
                                    target.setValue(normalizedCode);
                                    const verify = typeof target.getValue === 'function'
                                        ? (target.getValue() || '').replace(/\\r\\n/g, '\\n')
                                        : '';
                                    if (verify === normalizedCode) {
                                        ok = true;
                                        reason = 'monaco_editor_setValue_verified';
                                    } else {
                                        reason = 'monaco_editor_verify_mismatch';
                                    }
                                    if (ok && target.focus) target.focus();
                                }
                            } catch (e) {
                                reason = 'monaco_error:' + (e && e.message ? e.message : String(e));
                            }
                        } else if (!ok && hasMonacoDom) {
                            reason = 'monaco_dom_detected_but_api_unavailable';
                        }

                        // CodeMirror
                        if (!ok && !hasMonacoDom) {
                            try {
                                const cmEls = Array.from(document.querySelectorAll('.CodeMirror'));
                                for (const el of cmEls) {
                                    if (!visible(el)) continue;
                                    if (el.CodeMirror && typeof el.CodeMirror.setValue === 'function') {
                                        el.CodeMirror.setValue('');
                                        el.CodeMirror.setValue(code);
                                        el.CodeMirror.focus();
                                        ok = true;
                                        reason = 'codemirror_setValue';
                                        break;
                                    }
                                }
                            } catch (e) {
                                reason = 'codemirror_error:' + (e && e.message ? e.message : String(e));
                            }
                        }

                        // Ace
                        if (!ok && !hasMonacoDom && window.ace && typeof window.ace.edit === 'function') {
                            try {
                                const aceEls = Array.from(document.querySelectorAll('.ace_editor'));
                                for (const el of aceEls) {
                                    if (!visible(el)) continue;
                                    const editor = window.ace.edit(el);
                                    editor.setValue('', -1);
                                    editor.setValue(code, -1);
                                    editor.focus();
                                    ok = true;
                                    reason = 'ace_setValue';
                                    break;
                                }
                            } catch (e) {
                                reason = 'ace_error:' + (e && e.message ? e.message : String(e));
                            }
                        }

                        // textarea
                        if (!ok && !hasMonacoDom) {
                            try {
                                const textareas = Array.from(document.querySelectorAll('textarea'))
                                    .filter(el => !el.readOnly && !el.disabled && visible(el));
                                for (const el of textareas) {
                                    el.focus();
                                    el.value = '';
                                    el.value = code;
                                    el.dispatchEvent(new Event('input', { bubbles: true }));
                                    el.dispatchEvent(new Event('change', { bubbles: true }));
                                    ok = true;
                                    reason = 'textarea_value';
                                    break;
                                }
                            } catch (e) {
                                reason = 'textarea_error:' + (e && e.message ? e.message : String(e));
                            }
                        }

                        // contenteditable
                        if (!ok && !hasMonacoDom) {
                            try {
                                const edits = Array.from(document.querySelectorAll('[contenteditable="true"]'))
                                    .filter(el => visible(el));
                                for (const el of edits) {
                                    el.focus();
                                    el.textContent = '';
                                    el.textContent = code;
                                    el.dispatchEvent(new Event('input', { bubbles: true }));
                                    ok = true;
                                    reason = 'contenteditable_textContent';
                                    break;
                                }
                            } catch (e) {
                                reason = 'contenteditable_error:' + (e && e.message ? e.message : String(e));
                            }
                        }
                    } catch (e) {
                        reason = 'page_context_error:' + (e && e.message ? e.message : String(e));
                    }

                    window.postMessage({ source, ok, reason }, '*');
                })();
            `;

            script.onload = () => script.remove();
            script.onerror = () => finish({ ok: false, reason: 'script_injection_error' });

            (document.documentElement || document.head || document.body).appendChild(script);
        });
    }

    setCodeToMonaco(code) {
        try {
            if (!window.monaco || !window.monaco.editor) return false;

            const normalizedCode = (code || '').replace(/\r\n/g, '\n');
            const getEditors = window.monaco.editor.getEditors;

            if (typeof getEditors === 'function') {
                const editors = getEditors.call(window.monaco.editor) || [];
                const targetEditor = this.pickBestMonacoEditor(editors);
                if (targetEditor) {
                    targetEditor.setValue('');
                    targetEditor.setValue(normalizedCode);
                    const verify = typeof targetEditor.getValue === 'function'
                        ? (targetEditor.getValue() || '').replace(/\r\n/g, '\n')
                        : '';
                    if (verify !== normalizedCode) return false;
                    if (targetEditor.focus) targetEditor.focus();
                    return true;
                }
            }

            const models = window.monaco.editor.getModels ? window.monaco.editor.getModels() : [];
            if (models && models.length === 1) {
                models[0].setValue('');
                models[0].setValue(normalizedCode);
                const verify = typeof models[0].getValue === 'function'
                    ? (models[0].getValue() || '').replace(/\r\n/g, '\n')
                    : '';
                if (verify !== normalizedCode) return false;
                return true;
            }
        } catch (e) {
            // fallback
        }
        return false;
    }

    setCodeToCodeMirror(code) {
        try {
            const cm = document.querySelector('.CodeMirror');
            if (cm && cm.CodeMirror) {
                cm.CodeMirror.setValue('');
                cm.CodeMirror.setValue(code);
                cm.CodeMirror.focus();
                return true;
            }
        } catch (e) { /* fallback */ }
        return false;
    }

    setCodeToAce(code) {
        try {
            if (typeof ace !== 'undefined') {
                const editors = document.querySelectorAll('.ace_editor');
                for (const el of editors) {
                    const ed = ace.edit(el);
                    if (ed) {
                        ed.setValue('', -1);
                        ed.setValue(code, -1);
                        ed.focus();
                        return true;
                    }
                }
            }
        } catch (e) { /* fallback */ }
        return false;
    }

    setCodeToTextarea(code) {
        try {
            const textareas = Array.from(document.querySelectorAll('textarea'));
            if (textareas.length === 0) return false;
            textareas.sort((a, b) => this.editorElementScore(b) - this.editorElementScore(a));
            const best = textareas[0];
            if (this.editorElementScore(best) > 0) {
                best.focus();
                best.value = '';
                best.value = code;
                best.dispatchEvent(new Event('input', { bubbles: true }));
                best.dispatchEvent(new Event('change', { bubbles: true }));
                return true;
            }
        } catch (e) { /* fallback */ }
        return false;
    }

    setCodeToContentEditable(code) {
        try {
            const editables = document.querySelectorAll('[contenteditable="true"]');
            for (const el of editables) {
                if (el.innerText.length > 50 || el.closest('.editor, .code, .monaco')) {
                    el.focus();
                    el.textContent = '';
                    el.textContent = code;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    return true;
                }
            }
        } catch (e) { /* fallback */ }
        return false;
    }

    requestDesktopInput(code) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                type: 'ready_for_input',
                code: code,
                input_method: 'paste'
            }));
            this.addLog('回退到桌面端键盘模拟输入', 'warning');
        } else {
            this.addLog('无法写入代码：未连接服务器', 'error');
        }
    }

    // ========== Test Results Extraction ==========
    extractTestResults() {
        this.addLog('开始提取测试结果...', 'info');
        let structured = {
            test_result_info: '',
            error_info: '',
            test_sets: []
        };
        let text = '';

        // Educoder specific selectors
        const educoderSelectors = [
            '.test-set-container___JHp4n',
            '.test-set-container',
            '.test-case-container',
            '[class*="test-set"]',
            '[class*="test-case"]',
            '[class*="result"]'
        ];

        let container = null;
        for (const selector of educoderSelectors) {
            container = document.querySelector(selector);
            if (container) {
                this.addLog(`找到测试容器: ${selector}`, 'info');
                break;
            }
        }

        if (container) {
            const items = container.querySelectorAll('.test-case-item___E3CU9, .test-case-item, [class*="test-case"]');
            items.forEach((item, idx) => {
                const name = (item.querySelector('.test-case-name, .case-title, [class*="name"]') || {}).innerText || `测试 ${idx + 1}`;
                const testInput = (item.querySelector('[class*="test-input"], .test-input, [class*="input"]') || {}).innerText || '';
                const expected = (item.querySelector('[class*="expected"], .expected-output, [class*="output"]') || {}).innerText || '';
                const actual = (item.querySelector('[class*="actual"], .actual-output, [class*="result"]') || {}).innerText || '';
                structured.test_sets.push({ name, test_input: testInput, expected, actual });
            });
            // Result info
            const resultEl = container.querySelector('.test-result, .result-summary, [class*="result"]');
            if (resultEl) structured.test_result_info = resultEl.innerText;
            // Error info
            const errorEl = container.querySelector('.error-info, .error-detail, [class*="error"]');
            if (errorEl) structured.error_info = errorEl.innerText;
        }

        // DOM fallback: scan for keywords
        if (structured.test_sets.length === 0) {
            this.addLog('使用 DOM 回退方案提取...', 'info');
            const allDivs = document.querySelectorAll('div, section');
            for (const div of allDivs) {
                const t = div.innerText || '';
                if ((t.includes('测试输入') || t.includes('预期输出') || t.includes('实际输出')) && t.length < 5000) {
                    structured.test_sets.push({
                        name: '测试结果',
                        test_input: this._extractSection(t, '测试输入'),
                        expected: this._extractSection(t, '预期输出'),
                        actual: this._extractSection(t, '实际输出')
                    });
                }
            }
        }

        // Build text
        text = structured.test_result_info + '\n';
        if (structured.error_info) text += structured.error_info + '\n';
        structured.test_sets.forEach((ts, i) => {
            text += `\n--- ${ts.name} ---\n`;
            if (ts.test_input) text += `测试输入: ${ts.test_input}\n`;
            if (ts.expected) text += `预期输出: ${ts.expected}\n`;
            if (ts.actual) text += `实际输出: ${ts.actual}\n`;
        });

        if (text.length > 50000) text = text.substring(0, 50000) + '\n... [内容过长已截断]';

        this.addLog(`提取到测试结果: ${text.length} 字符`, 'info');
        if (!text.trim()) {
            this.addLog('未能提取到测试结果，请检查页面是否已加载完成', 'warning');
        }

        return { text: text.trim(), structured };
    }

    _extractSection(text, keyword) {
        const idx = text.indexOf(keyword);
        if (idx === -1) return '';
        const after = text.substring(idx + keyword.length).trim();
        const endIdx = after.search(/\n|测试输入|预期输出|实际输出/);
        return endIdx > 0 ? after.substring(0, endIdx).trim() : after.substring(0, 200).trim();
    }

    _clearEditorBeforeInput() {
        document.execCommand('selectAll');
        document.execCommand('delete');
    }

    // ========== 一键获取并粘贴 ==========
    async autoGetAndPaste() {
        this.addLog('开始一键获取并粘贴...', 'info');

        // 获取题目内容
        await this.getEducoderContent();

        // 等待代码生成
        const waitForCode = () => {
            return new Promise((resolve) => {
                if (this.generatedCode) {
                    resolve();
                    return;
                }
                const check = setInterval(() => {
                    if (this.generatedCode) {
                        clearInterval(check);
                        resolve();
                    }
                }, 500);
                // 超时 60 秒
                setTimeout(() => {
                    clearInterval(check);
                    resolve();
                }, 60000);
            });
        };

        await waitForCode();

        if (this.generatedCode) {
            this.addLog('代码已生成，开始粘贴...', 'info');
            await this.pasteCodeToEditor();
        } else {
            this.addLog('代码生成超时', 'error');
        }
    }

    // ========== Auto Answer Flow ==========
    async getEducoderContent() {
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
            this.addLog('未连接服务器，请先启动桌面端', 'error');
            return;
        }
        if (this.isInputInProgress) return;
        this.setInputInProgress(true);
        this.addLog('正在获取题目内容...', 'info');

        // 1. Extract content
        let content = this.extractPageContent();
        if (!content) {
            this.addLog('未找到题目内容', 'error');
            this.setInputInProgress(false);
            return;
        }

        // 2. OCR enrichment
        this.addLog('正在识别图片文字...', 'info');
        content = await this.enrichContentWithImageOCR(content);

        // 3. Read current editor code
        const currentCode = this.extractCurrentEditorCode();

        // 4. Send
        this.addLog('题目已发送到服务器', 'send');
        this.showTopTip('正在生成代码...');
        this.socket.send(JSON.stringify({
            type: 'content_auto_input',
            question_content: content,
            current_code: currentCode,
            language: this.langSelect.value,
            source: window.location.hostname,
            sync_question: false
        }));
    }

    // ========== Manual Input Flow ==========
    manualInput() {
        const question = this.questionInput.value.trim();
        if (!question) {
            this.addLog('请先输入题目内容', 'warning');
            return;
        }
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
            this.addLog('未连接服务器', 'error');
            return;
        }

        this.addLog('正在调用AI生成代码...', 'info');
        const currentCode = this.extractCurrentEditorCode();
        this.socket.send(JSON.stringify({
            type: 'manual_question',
            question_content: question,
            current_code: currentCode,
            language: this.langSelect.value
        }));
    }

    fetchQuestionToInput() {
        this.addLog('正在获取页面题目...', 'info');
        let content = this.extractPageContent();
        if (!content) {
            this.addLog('未找到题目内容', 'error');
            return;
        }
        this.questionInput.value = content;
        this.addLog('✅ 题目已获取，可编辑后生成代码', 'success');
    }

    // ========== Paste Code ==========
    async pasteCodeToEditor() {
        // 优先从textarea读取，其次用generatedCode
        const codeToPaste = this.codePreview.value.trim() || this.generatedCode;
        if (!codeToPaste) {
            this.addLog('没有可粘贴的代码', 'error');
            return;
        }
        this.showTopTip('代码输入中...');
        try {
            const success = await this.setCodeToPageEditor(codeToPaste);
            if (success) {
                this.addLog('代码已粘贴到编辑器', 'success');
            } else {
                this.addLog('自动粘贴失败，请手动复制代码', 'error');
            }
        } catch (error) {
            this.addLog(`粘贴出错: ${error.message}`, 'error');
        } finally {
            this.hideTopTip();
        }
    }

    // ========== Smart Correction ==========
    async smartCorrection() {
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
            this.addLog('未连接服务器', 'error');
            return;
        }
        if (this.isInputInProgress) return;
        if (this.retryCount >= this.maxRetries) {
            this.addLog('已达最大纠错次数 (' + this.maxRetries + '次)', 'warning');
            return;
        }
        this.setInputInProgress(true);
        this.addLog('正在提取测试结果...', 'info');

        const results = this.extractTestResults();
        if (!results.text || results.structured.test_sets.length === 0) {
            this.addLog('未找到测试结果，请先运行测试', 'warning');
            this.setInputInProgress(false);
            return;
        }

        const hasFailure = /失败|fail|错误|error|\[failed\]/i.test(results.text);
        if (!hasFailure) {
            this.addLog('✅ 所有测试已通过', 'success');
            this.setInputInProgress(false);
            return;
        }

        this.retryCount++;
        this.showTopTip('智能纠错中... (' + this.retryCount + '/' + this.maxRetries + ')');
        this.addLog('检测到失败，开始第 ' + this.retryCount + ' 次纠错...', 'warning');

        const content = this.extractPageContent();
        const currentCode = this.extractCurrentEditorCode();

        this.socket.send(JSON.stringify({
            type: 'test_results',
            results: results,
            question_content: content,
            current_code: currentCode,
            language: this.langSelect.value
        }));
    }

    // ========== Copy & Regenerate ==========
    copyCode() {
        if (!this.generatedCode) {
            this.addLog('没有可复制的代码', 'warning');
            return;
        }
        navigator.clipboard.writeText(this.generatedCode).then(() => {
            this.addLog('代码已复制到剪贴板', 'success');
        }).catch(() => {
            // Fallback
            const ta = document.createElement('textarea');
            ta.value = this.generatedCode;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            ta.remove();
            this.addLog('代码已复制到剪贴板', 'success');
        });
    }

    regenerate() {
        if (this.currentTab === 'manual') {
            this.manualInput();
        } else {
            this.getEducoderContent();
        }
    }

    inputTest() {
        this.addLog('输入测试: 将在3秒后模拟输入测试文本', 'info');
        setTimeout(() => {
            const testText = 'print("Hello from Learning Assistant!")';
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.socket.send(JSON.stringify({
                    type: 'ready_for_input',
                    code: testText,
                    input_method: 'typing'
                }));
            }
        }, 3000);
    }

    // ========== Logging ==========
    addLog(message, type = 'info') {
        const now = new Date();
        const time = now.toTimeString().split(' ')[0];
        const entry = document.createElement('div');
        entry.className = 'la-log-entry la-log-' + type;
        entry.innerHTML = `<span class="la-log-time">${time}</span><span class="la-log-msg">${message}</span>`;
        // 最新消息显示在上面
        if (this.logArea.firstChild) {
            this.logArea.insertBefore(entry, this.logArea.firstChild);
        } else {
            this.logArea.appendChild(entry);
        }
    }

    clearLog() {
        this.logArea.innerHTML = '';
    }
}

// Initialize
(async function() {
    if (window.__la_instance) return;
    window.__la_instance = new LearningAssistant();
})();
