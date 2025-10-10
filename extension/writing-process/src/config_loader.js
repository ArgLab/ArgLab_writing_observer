let __CFG = null;

export async function getConfig() {
  if (__CFG) return __CFG;

  const url = chrome.runtime.getURL('src/config.json'); // adjust if bundler changes path
  console.log('[Config Loader] fetching:', chrome.runtime.getURL('src/config.json'));
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to load config.json: ${res.status}`);

  const base = await res.json();
  const merged = await applyOverrides(base);     // <- await the async override
  const validated = validateConfig(merged);      // <- validate final object
  console.log('[Config Loader] Loaded configuration:', validated);  // 👈 add this

  __CFG = validated;                              // <- cache the final config
  return __CFG;
}

/**
 * Merge runtime configuration overrides (from chrome.storage.sync)
 * into the base config loaded from config.json.
 *
 * This allows developers or testers to change certain parameters
 * (like WEBSOCKET_SERVER_URL, LOG_LEVEL, etc.) dynamically
 * without rebuilding or reloading the entire extension.
 *
 * Example of what chrome.storage.sync might contain:
 * {
 *   "CONFIG_OVERRIDE": {
 *     "WEBSOCKET_SERVER_URL": "ws://localhost:8888/wsapi/in/",
 *     "LOG_LEVEL": "debug"
 *   }
 * }
 */
async function applyOverrides(cfg) {
  try {
    const stored = await chrome.storage.sync.get('CONFIG_OVERRIDE'); // requires "storage" permission
    const overrides = stored?.CONFIG_OVERRIDE || {};
    if (Object.keys(overrides).length > 0) {
      console.log('[Config] Applying overrides from chrome.storage.sync:', overrides);
      return { ...cfg, ...overrides };
    }
    return cfg;
  } catch (err) {
    console.error('[Config] Failed to load overrides from storage:', err);
    return cfg;
  }
}


/** Minimal validation so we fail early with clear errors. */
function validateConfig(cfg) {
  const required = ['WEBSOCKET_SERVER_URL'];
  for (const k of required) {
    if (!cfg[k]) throw new Error(`Missing required config: ${k}`);
  }
  if (!/^wss?:\/\//.test(cfg.WEBSOCKET_SERVER_URL)) {
    throw new Error('WEBSOCKET_SERVER_URL must start with ws:// or wss://');
  }
  return cfg;
}