export const CONFIG = {
    ENV_NAME: "prod",
    WEBSOCKET_SERVER_URL: "wss://learning-observer.org/wsapi/in/",
    HTTP_API_BASE_URL: "https://learning-observer.org",
    LOG_LEVEL: "info",
    REQUEST_TIMEOUT_MS: 15000,
    HEARTBEAT_MS: 30000,
    RECONNECT: { initialMs: 1000, maxMs: 15000, factor: 1.7 },
    FEATURE_FLAGS: { verboseErrors: false },
  };