let cachedConfig = null;

async function syncServerConfig() {
    try {
        const resp = await fetch(chrome.runtime.getURL('server-config.json'));
        if (resp.ok) {
            const data = await resp.json();
            if (data.ws_url) {
                cachedConfig = data;
                chrome.storage.local.set({ serverUrl: data.ws_url });
                return;
            }
        }
    } catch (e) {
        // 配置文件不存在，跳过
    }
}

// 扩展安装时初始化
chrome.runtime.onInstalled.addListener(() => {
    syncServerConfig();
    chrome.storage.local.get(['serverUrl'], (result) => {
        if (!result.serverUrl) {
            chrome.storage.local.set({ serverUrl: 'ws://localhost:8000' });
        }
    });
});

// Chrome 启动时同步配置
chrome.runtime.onStartup.addListener(() => {
    syncServerConfig();
});

// 定期检查配置文件更新（每分钟）
chrome.alarms.create('syncConfig', { periodInMinutes: 1 });
chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === 'syncConfig') {
        syncServerConfig();
    }
});

// 处理来自内容脚本的配置请求
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.action === 'getServerUrl') {
        if (cachedConfig && cachedConfig.ws_url) {
            sendResponse({ serverUrl: cachedConfig.ws_url });
        } else {
            chrome.storage.local.get(['serverUrl'], (result) => {
                sendResponse({ serverUrl: result.serverUrl || 'ws://localhost:8000' });
            });
        }
        return true; // 异步响应
    }
    if (msg.action === 'syncConfig') {
        syncServerConfig().then(() => {
            if (cachedConfig && cachedConfig.ws_url) {
                sendResponse({ serverUrl: cachedConfig.ws_url });
            } else {
                sendResponse({ serverUrl: null });
            }
        });
        return true;
    }
});

chrome.action.onClicked.addListener((tab) => {
    chrome.tabs.sendMessage(tab.id, { action: 'toggleAssistant' });
});
