let cachedConfig = null;

function insertIntoPageEditor(text, markerId, editorMarkAttr, allowFallback) {
  function visible(el) {
    if (!el) {
      return false;
    }
    const style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
      return false;
    }
    const rect = el.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  }

  function area(el) {
    const rect = el.getBoundingClientRect();
    return Math.max(0, rect.width) * Math.max(0, rect.height);
  }

  function matchesTarget(node, target) {
    if (!node || !target) {
      return false;
    }
    return node === target || node.contains(target) || target.contains(node);
  }

  function scoreElement(el) {
    const marker = [
      el.id || '',
      el.className || '',
      el.getAttribute('name') || '',
      el.getAttribute('placeholder') || '',
      el.getAttribute('aria-label') || ''
    ].join(' ').toLowerCase();

    let score = 0;
    ['editor', 'code', 'monaco', 'codemirror', 'ace', 'textarea', 'input'].forEach((word) => {
      if (marker.includes(word)) {
        score += 3;
      }
    });
    if (el === document.activeElement || el.contains(document.activeElement)) {
      score += 10;
    }
    score += Math.min(5, Math.floor(area(el) / 120000));
    return score;
  }

  function pickBest(elements) {
    return elements
      .filter((el) => visible(el))
      .sort((a, b) => scoreElement(b) - scoreElement(a))[0] || null;
  }

  function pickMonacoEditor(editors, target) {
    const candidates = (editors || []).filter((editor) => {
      try {
        const node = editor.getDomNode && editor.getDomNode();
        return node && visible(node);
      } catch (error) {
        return false;
      }
    });
    if (!candidates.length) {
      return null;
    }

    const exact = candidates.find((editor) => {
      const node = editor.getDomNode && editor.getDomNode();
      return matchesTarget(node, target);
    });
    if (exact) {
      return exact;
    }

    const focused = candidates.find((editor) => {
      try {
        return editor.hasTextFocus && editor.hasTextFocus();
      } catch (error) {
        return false;
      }
    });
    if (focused) {
      return focused;
    }

    candidates.sort((a, b) => area(b.getDomNode()) - area(a.getDomNode()));
    return candidates[0] || null;
  }

  function tryMonaco(target) {
    if (!window.monaco || !window.monaco.editor) {
      return tryMonacoInputArea(target);
    }
    if (target && !target.closest('.monaco-editor') && !target.querySelector('.monaco-editor')) {
      return null;
    }

    const editors = typeof window.monaco.editor.getEditors === 'function'
      ? window.monaco.editor.getEditors()
      : [];
    const editor = pickMonacoEditor(editors, target);
    if (editor && typeof editor.executeEdits === 'function') {
      const selection = editor.getSelection && editor.getSelection();
      const position = editor.getPosition && editor.getPosition();
      let range = selection;
      if (!range && position && window.monaco.Range) {
        range = new window.monaco.Range(position.lineNumber, position.column, position.lineNumber, position.column);
      }
      if (!range) {
        return null;
      }

      if (editor.pushUndoStop) {
        editor.pushUndoStop();
      }
      editor.executeEdits('learning-assistant-paste', [{ range, text, forceMoveMarkers: true }]);
      if (editor.pushUndoStop) {
        editor.pushUndoStop();
      }
      if (editor.focus) {
        editor.focus();
      }
      return { ok: true, reason: 'monaco_executeEdits' };
    }

    const models = typeof window.monaco.editor.getModels === 'function'
      ? window.monaco.editor.getModels()
      : [];
    if (models.length === 1 && typeof models[0].getValue === 'function' && typeof models[0].setValue === 'function') {
      const current = models[0].getValue() || '';
      models[0].setValue(current ? current + text : text);
      return { ok: true, reason: 'monaco_single_model_append' };
    }

    return tryMonacoInputArea(target);
  }

  function tryMonacoInputArea(target) {
    const root = target && (target.closest('.monaco-editor') || target.querySelector('.monaco-editor'));
    if (target && !root) {
      return null;
    }
    const elements = root
      ? [root]
      : (allowFallback ? Array.from(document.querySelectorAll('.monaco-editor')).filter(visible) : []);
    for (const el of elements) {
      const input = el.querySelector('textarea.inputarea, textarea');
      if (!input) {
        continue;
      }
      try {
        input.focus();
        const inserted = document.execCommand && document.execCommand('insertText', false, text);
        if (inserted) {
          return { ok: true, reason: 'monaco_inputarea_insertText' };
        }
      } catch (error) {
        // 继续搜索其他 Monaco 根节点
      }
    }
    return null;
  }

  function tryCodeMirror(target) {
    const root = target && (target.closest('.CodeMirror') || target.querySelector('.CodeMirror'));
    if (target && !root) {
      return null;
    }
    const elements = root
      ? [root]
      : (allowFallback ? Array.from(document.querySelectorAll('.CodeMirror')).filter(visible) : []);
    if (!elements.length) {
      return null;
    }

    for (const el of elements) {
      const cm = el.CodeMirror;
      if (cm && typeof cm.replaceSelection === 'function') {
        cm.replaceSelection(text, 'end');
        if (typeof cm.focus === 'function') {
          cm.focus();
        }
        return { ok: true, reason: 'codemirror_replaceSelection' };
      }
    }
    return null;
  }

  function tryAce(target) {
    const root = target && (target.closest('.ace_editor') || target.querySelector('.ace_editor'));
    if (target && !root) {
      return null;
    }
    const elements = root
      ? [root]
      : (allowFallback ? Array.from(document.querySelectorAll('.ace_editor')).filter(visible) : []);
    if (!elements.length) {
      return null;
    }

    for (const el of elements) {
      const editor = (el.env && el.env.editor)
        || (el.editor)
        || (window.ace && typeof window.ace.edit === 'function' ? window.ace.edit(el) : null);
      if (!editor || !editor.session || !editor.selection) {
        continue;
      }

      editor.focus();
      const range = editor.getSelectionRange();
      const start = range.start;
      editor.session.replace(range, text);

      const lines = String(text).split(/\r\n|\r|\n/);
      const endRow = start.row + lines.length - 1;
      const endColumn = lines.length === 1
        ? start.column + lines[0].length
        : lines[lines.length - 1].length;
      editor.selection.moveTo(endRow, endColumn);
      editor.clearSelection();
      editor.focus();
      return { ok: true, reason: 'ace_session_replace' };
    }

    return null;
  }

  function isWritableInput(el) {
    if (!(el instanceof HTMLInputElement)) {
      return false;
    }
    const type = (el.getAttribute('type') || 'text').toLowerCase();
    return ['text', 'search', 'url', 'tel', 'password', 'email'].includes(type) && !el.readOnly && !el.disabled;
  }

  function insertIntoTextControl(el) {
    if (!el || (el instanceof HTMLTextAreaElement && (el.readOnly || el.disabled)) || (el instanceof HTMLInputElement && !isWritableInput(el))) {
      return null;
    }

    el.focus();
    const value = el.value || '';
    const start = typeof el.selectionStart === 'number' ? el.selectionStart : value.length;
    const end = typeof el.selectionEnd === 'number' ? el.selectionEnd : start;
    if (typeof el.setRangeText === 'function') {
      el.setRangeText(text, start, end, 'end');
    } else {
      el.value = value.slice(0, start) + text + value.slice(end);
    }
    el.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertFromPaste', data: text }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    return { ok: true, reason: el instanceof HTMLTextAreaElement ? 'textarea_setRangeText' : 'input_setRangeText' };
  }

  function dispatchRichInput(el) {
    const target = el || document.body || document.documentElement;
    try {
      target.dispatchEvent(new InputEvent('input', {
        bubbles: true,
        cancelable: true,
        inputType: 'insertFromPaste',
        data: text
      }));
    } catch (error) {
      target.dispatchEvent(new Event('input', { bubbles: true }));
    }
    target.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function getEditableTarget(target) {
    if (document.designMode && document.designMode.toLowerCase() === 'on') {
      return document.body || target;
    }

    if (target && target.closest) {
      const editable = target.closest('[contenteditable="true"]');
      if (editable) {
        return editable;
      }
    }

    const active = document.activeElement;
    if (active && active.closest) {
      const activeEditable = active.closest('[contenteditable="true"]');
      if (activeEditable) {
        return activeEditable;
      }
    }

    return allowFallback
      ? pickBest(Array.from(document.querySelectorAll('[contenteditable="true"]')))
      : null;
  }

  function rangeBelongsTo(range, editable) {
    if (!range || !editable) {
      return false;
    }
    return editable === document.body || editable.contains(range.commonAncestorContainer);
  }

  function moveCaretToEnd(editable) {
    const selection = window.getSelection && window.getSelection();
    if (!selection || !editable) {
      return null;
    }

    const range = document.createRange();
    range.selectNodeContents(editable);
    range.collapse(false);
    selection.removeAllRanges();
    selection.addRange(range);
    return range;
  }

  function insertTextByRange(editable) {
    const selection = window.getSelection && window.getSelection();
    let range = selection && selection.rangeCount ? selection.getRangeAt(0) : null;
    if (!rangeBelongsTo(range, editable)) {
      range = moveCaretToEnd(editable);
    }
    if (!range) {
      return false;
    }

    range.deleteContents();
    const textNode = document.createTextNode(text);
    range.insertNode(textNode);
    range.setStartAfter(textNode);
    range.collapse(true);
    if (selection) {
      selection.removeAllRanges();
      selection.addRange(range);
    }
    return true;
  }

  function tryRichEditable(target) {
    const editable = getEditableTarget(target);
    if (!editable) {
      return null;
    }

    try {
      if (editable.focus) {
        editable.focus();
      }
    } catch (error) {
      // 部分 designMode body 聚焦可能失败
    }

    let inserted = false;
    try {
      inserted = !!document.execCommand && document.execCommand('insertText', false, text);
    } catch (error) {
      inserted = false;
    }

    if (!inserted) {
      inserted = insertTextByRange(editable);
    }

    if (!inserted) {
      return null;
    }

    dispatchRichInput(editable);
    return {
      ok: true,
      reason: document.designMode && document.designMode.toLowerCase() === 'on'
        ? 'designmode_insertText'
        : 'contenteditable_insertText'
    };
  }

  function tryPlainControls(target) {
    if (target instanceof HTMLTextAreaElement || target instanceof HTMLInputElement) {
      return insertIntoTextControl(target);
    }

    if (target && !allowFallback) {
      return null;
    }

    const active = document.activeElement;
    if (active instanceof HTMLTextAreaElement || active instanceof HTMLInputElement) {
      const activeResult = insertIntoTextControl(active);
      if (activeResult) {
        return activeResult;
      }
    }

    const picked = pickBest(Array.from(document.querySelectorAll([
      'textarea',
      'input[type="text"]',
      'input[type="search"]',
      'input[type="url"]',
      'input[type="tel"]',
      'input[type="password"]',
      'input[type="email"]',
      'input:not([type])'
    ].join(','))).filter((el) => el instanceof HTMLTextAreaElement || isWritableInput(el)));

    return picked ? insertIntoTextControl(picked) : null;
  }

  try {
    let target = markerId
      ? document.querySelector('[' + editorMarkAttr + '="' + markerId + '"]')
      : null;
    if (markerId && !target) {
      return { ok: false, reason: 'target_not_found' };
    }

    if (!target && allowFallback) {
      target = pickBest(Array.from(document.querySelectorAll('.monaco-editor, .CodeMirror, .ace_editor, textarea, input, [contenteditable="true"]')));
      if (!target && document.designMode && document.designMode.toLowerCase() === 'on') {
        target = document.body;
      }
    }

    const strategies = [tryAce, tryMonaco, tryCodeMirror, tryRichEditable, tryPlainControls];
    for (const strategy of strategies) {
      const result = strategy(target);
      if (result && result.ok) {
        return result;
      }
    }
    return { ok: false, reason: 'no_page_editor_api_matched' };
  } catch (error) {
    return { ok: false, reason: error && error.message ? error.message : String(error) };
  }
}

function detectPageEditor() {
  function visible(el) {
    if (!el) {
      return false;
    }
    const style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
      return false;
    }
    const rect = el.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  }

  function area(el) {
    const rect = el.getBoundingClientRect();
    return Math.max(0, rect.width) * Math.max(0, rect.height);
  }

  function activeBonus(el) {
    return el === document.activeElement || el.contains(document.activeElement) ? 20 : 0;
  }

  function bestScore(selector, baseScore, apiCheck) {
    const elements = Array.from(document.querySelectorAll(selector)).filter(visible);
    let best = 0;
    for (const el of elements) {
      if (apiCheck && !apiCheck(el)) {
        continue;
      }
      const score = baseScore + activeBonus(el) + Math.min(10, Math.floor(area(el) / 90000));
      best = Math.max(best, score);
    }
    return best;
  }

  const scores = [
    bestScore('.ace_editor', 100, (el) => !!((el.env && el.env.editor) || (window.ace && typeof window.ace.edit === 'function'))),
    bestScore('.monaco-editor', 95, (el) => !!(window.monaco && window.monaco.editor) || !!el.querySelector('textarea.inputarea, textarea')),
    bestScore('.CodeMirror', 90, (el) => !!el.CodeMirror),
    document.designMode && document.designMode.toLowerCase() === 'on' ? 85 : 0,
    bestScore('[contenteditable="true"]', 80, () => true),
    bestScore('textarea, input[type="text"], input[type="search"], input[type="url"], input[type="tel"], input[type="password"], input[type="email"], input:not([type])', 45, (el) => !el.readOnly && !el.disabled)
  ];

  const score = Math.max(...scores);
  return score > 0
    ? { ok: true, score }
    : { ok: false, reason: 'no_candidate_editor' };
}

function withTimeout(promise, ms, reason) {
    return Promise.race([
        promise,
        new Promise((_, reject) => {
            setTimeout(() => reject(new Error(reason)), ms);
        })
    ]);
}

const activeFrameTargets = new Map();

function tabFrameKey(tabId) {
    return String(tabId);
}

function rememberFrameTarget(tabId, frameId, markerId, editorMarkAttr) {
    if (!tabId || typeof frameId !== 'number' || !markerId) {
        return;
    }
    activeFrameTargets.set(tabFrameKey(tabId), {
        frameId: frameId,
        markerId: markerId,
        editorMarkAttr: editorMarkAttr,
        time: Date.now()
    });
}

function getRecentFrameTarget(tabId) {
    const target = activeFrameTargets.get(tabFrameKey(tabId));
    if (!target || Date.now() - target.time > 120000) {
        return null;
    }
    return target;
}

async function resolveEditorTarget(tabId, senderFrameId, markerId, editorMarkAttr, allowFallback) {
    let target = { tabId: tabId, frameIds: typeof senderFrameId === 'number' ? [senderFrameId] : [0] };
    let resolvedMarkerId = markerId || '';
    let resolvedEditorMarkAttr = editorMarkAttr || '';
    const recentTarget = getRecentFrameTarget(tabId);

    if (resolvedMarkerId && recentTarget && recentTarget.markerId === resolvedMarkerId) {
        target = { tabId: tabId, frameIds: [recentTarget.frameId] };
        resolvedEditorMarkAttr = recentTarget.editorMarkAttr || resolvedEditorMarkAttr;
        return {
            ok: true,
            target: target,
            markerId: resolvedMarkerId,
            editorMarkAttr: resolvedEditorMarkAttr
        };
    }

    if (allowFallback) {
        const detected = await withTimeout(
            chrome.scripting.executeScript({
                target: { tabId: tabId, allFrames: true },
                world: 'MAIN',
                func: detectPageEditor
            }),
            1200,
            'detect_editor_timeout'
        );
        const best = (detected || [])
            .filter((item) => item.result && item.result.ok)
            .sort((a, b) => (b.result.score || 0) - (a.result.score || 0))[0];

        if (best && typeof best.frameId === 'number') {
            target = { tabId: tabId, frameIds: [best.frameId] };
            resolvedMarkerId = '';
        } else if (recentTarget) {
            target = { tabId: tabId, frameIds: [recentTarget.frameId] };
            resolvedMarkerId = recentTarget.markerId;
            resolvedEditorMarkAttr = recentTarget.editorMarkAttr || resolvedEditorMarkAttr;
        } else {
            return { ok: false, reason: 'no_candidate_editor' };
        }
    }

    return {
        ok: true,
        target: target,
        markerId: resolvedMarkerId,
        editorMarkAttr: resolvedEditorMarkAttr
    };
}

async function syncServerConfig() {
    try {
        const resp = await fetch(chrome.runtime.getURL('server-config.json'));
        if (resp.ok) {
            const data = await resp.json();
            if (data.ws_url) {
                cachedConfig = data;
                chrome.storage.local.set({ serverUrl: data.ws_url, ocrApiUrl: data.ocr_api_url || 'https://ocr.yhsun.cn/' });
            }
        }
    } catch (e) {
        // 配置文件不存在，跳过
    }
}

chrome.runtime.onInstalled.addListener(() => {
    syncServerConfig();
    chrome.storage.local.get(['serverUrl'], (result) => {
        if (!result.serverUrl) {
            chrome.storage.local.set({ serverUrl: 'ws://localhost:8000', ocrApiUrl: 'https://ocr.yhsun.cn/' });
        }
    });
});

chrome.runtime.onStartup.addListener(() => {
    syncServerConfig();
});

chrome.alarms.create('syncConfig', { periodInMinutes: 1 });
chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === 'syncConfig') {
        syncServerConfig();
    }
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg && msg.type === 'la_paste_frame_target') {
        rememberFrameTarget(
            sender.tab && sender.tab.id,
            sender.frameId,
            msg.markerId,
            msg.editorMarkAttr
        );
        return false;
    }

    if (msg && msg.type === 'la_copy_paste_page_insert') {
        (async () => {
            try {
                const tabId = sender.tab && sender.tab.id;
                if (!tabId) {
                    sendResponse({ ok: false, reason: 'tab_not_found' });
                    return;
                }

                const resolved = await resolveEditorTarget(
                    tabId,
                    sender.frameId,
                    msg.markerId || '',
                    msg.editorMarkAttr || '',
                    !!msg.allowFallback
                );
                if (!resolved.ok) {
                    sendResponse(resolved);
                    return;
                }

                const injection = await withTimeout(
                    chrome.scripting.executeScript({
                        target: resolved.target,
                        world: 'MAIN',
                        func: insertIntoPageEditor,
                        args: [msg.text || '', resolved.markerId, resolved.editorMarkAttr, !!msg.allowFallback]
                    }),
                    2200,
                    'insert_editor_timeout'
                );

                const results = (injection || []).map((item) => item.result).filter(Boolean);
                const success = results.find((item) => item.ok);
                sendResponse(success || results[0] || { ok: false, reason: 'empty_main_world_result' });
            } catch (error) {
                sendResponse({ ok: false, reason: error && error.message ? error.message : String(error) });
            }
        })();

        return true;
    }

    if (msg.action === 'getServerUrl') {
        if (cachedConfig && cachedConfig.ws_url) {
            sendResponse({ serverUrl: cachedConfig.ws_url });
        } else {
            chrome.storage.local.get(['serverUrl'], (result) => {
                sendResponse({ serverUrl: result.serverUrl || 'ws://localhost:8000' });
            });
        }
        return true;
    }

    if (msg.action === 'getOcrApiUrl') {
        if (cachedConfig && cachedConfig.ocr_api_url) {
            sendResponse({ ocrApiUrl: cachedConfig.ocr_api_url });
        } else {
            chrome.storage.local.get(['ocrApiUrl'], (result) => {
                sendResponse({ ocrApiUrl: result.ocrApiUrl || 'https://ocr.yhsun.cn/' });
            });
        }
        return true;
    }

    if (msg.action === 'syncConfig') {
        syncServerConfig().then(() => {
            if (cachedConfig && cachedConfig.ws_url) {
                sendResponse({ serverUrl: cachedConfig.ws_url, ocrApiUrl: cachedConfig.ocr_api_url });
            } else {
                sendResponse({ serverUrl: null, ocrApiUrl: null });
            }
        });
        return true;
    }

    return false;
});

chrome.action.onClicked.addListener((tab) => {
    chrome.tabs.sendMessage(tab.id, { action: 'toggleAssistant' });
});
