/**
 * Public exports for the LO WebSocket connection layer.
 *
 * Provides hooks for subscribing to real-time Learning Observer data
 * (useLOConnectionDataManager, useLOConnection), a timestamp display
 * component (LOConnectionLastUpdated), and the connection status enum
 * (LO_CONNECTION_STATUS).
 */

export { useLOConnectionDataManager } from "./utilities/useLOConnectionDataManager.jsx";
export { useLOConnection } from "./utilities/useLOConnection.jsx";
export { LOConnectionLastUpdated } from "./utilities/LOConnectionLastUpdated.jsx";

export { LO_CONNECTION_STATUS } from "./constants/LO_CONNECTION_STATUS.jsx"