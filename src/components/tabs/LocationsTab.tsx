import React from 'react';
import { Check, Signal, Zap, Shield, Sparkles } from 'lucide-react';
import { motion } from 'motion/react';
import { ServerLocation } from '../../types';

interface LocationsTabProps {
  locations: ServerLocation[];
  currentServer: ServerLocation;
  onSelectServer: (server: ServerLocation) => void;
}

export const LocationsTab: React.FC<LocationsTabProps> = ({
  locations,
  currentServer,
  onSelectServer,
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="space-y-3"
    >
      <div className="pb-1">
        <h2 className="text-lg font-bold text-white">Выбор локации сервера</h2>
        <p className="text-xs text-slate-400">
          Все серверы поддерживают протокол VLESS Reality с маскировкой под TLS-трафик Google
        </p>
      </div>

      <div className="space-y-2">
        {locations.map((server) => {
          const isSelected = currentServer.id === server.id;
          const isFast = server.pingMs < 40;

          return (
            <div
              key={server.id}
              onClick={() => onSelectServer(server)}
              className={`cursor-pointer rounded-2xl p-3.5 flex items-center justify-between transition-all duration-200 ${
                isSelected
                  ? 'bg-gradient-to-r from-cyan-950/40 to-emerald-950/40 border-2 border-cyan-500 shadow-md shadow-cyan-950/50'
                  : 'bg-[#0f1422]/90 border border-white/5 hover:border-white/15'
              }`}
            >
              <div className="flex items-center space-x-3.5">
                <span className="text-2xl p-2 rounded-xl bg-white/5 border border-white/5 flex items-center justify-center">
                  {server.flag}
                </span>

                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="text-sm font-bold text-white">{server.country}</h3>
                    <span className="text-xs text-slate-400">({server.city})</span>
                    {isFast && (
                      <span className="text-[9px] font-black uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-1.5 py-0.2 rounded-full">
                        FAST
                      </span>
                    )}
                  </div>

                  <div className="flex items-center space-x-3 mt-1 text-[11px] text-slate-400">
                    <span className="flex items-center space-x-1">
                      <span
                        className={`w-2 h-2 rounded-full ${
                          server.pingMs < 45 ? 'bg-emerald-400' : server.pingMs < 80 ? 'bg-cyan-400' : 'bg-amber-400'
                        }`}
                      />
                      <span className="font-mono text-slate-300">{server.pingMs} ms</span>
                    </span>

                    <span>•</span>

                    <span>Нагрузка: {server.loadPercent}%</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                {isSelected ? (
                  <div className="w-6 h-6 rounded-full bg-cyan-500 text-black flex items-center justify-center shadow-lg shadow-cyan-500/50">
                    <Check className="w-3.5 h-3.5 stroke-[3]" />
                  </div>
                ) : (
                  <div className="w-6 h-6 rounded-full border border-white/10 hover:border-white/30" />
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Speed Tip */}
      <div className="p-3.5 rounded-2xl bg-cyan-950/20 border border-cyan-800/30 text-xs text-cyan-300 flex items-start space-x-2.5">
        <Sparkles className="w-4 h-4 shrink-0 text-cyan-400 mt-0.5" />
        <span>
          <strong>Совет:</strong> Для звонков в Telegram и игр выбирайте <strong>Хельсинки</strong> или <strong>Франкфурт</strong> для наименьшего пинга.
        </span>
      </div>
    </motion.div>
  );
};
