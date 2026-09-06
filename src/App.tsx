import React from 'react';
import { MiniAppSimulator } from './components/MiniAppSimulator';

/**
 * Client-facing Telegram Mini App entry point for @asbvpn_bot.
 * All developer panels and backend dashboards are removed so the client
 * exclusively sees the native Telegram Mini App interface.
 */
export default function App() {
  return <MiniAppSimulator />;
}
