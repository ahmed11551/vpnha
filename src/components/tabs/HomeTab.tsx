import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  Copy,
  Check,
  QrCode,
  RefreshCw,
  ExternalLink,
  Sparkles,
  Zap,
  Activity,
  ChevronRight,
  Wifi,
  Download,
} from 'lucide-react';
import { motion } from 'motion/react';
import { ActiveSubscription, ServerLocation, UserAccount } from '../../types';

interface HomeTabProps {
  user: UserAccount;
  activeSub: ActiveSubscription | null;
  currentServer: ServerLocation;
  onOpenLocations: () => void;
  onOpenPlans: () => void;
  onOpenQr: () => void;
  onCopyKey: () => void;
  hasCopied: boolean;
  onActivateTrial: () => void;
  isActivatingTrial: boolean;
  onRevokeKey: () => void;
  isRevokingKey: boolean;
}

export const HomeTab: React.FC<HomeTabProps> = ({
  user,
  activeSub,
  currentServer,
  onOpenLocations,
  onOpenPlans,
  onOpenQr,
  onCopyKey,
  hasCopied,
  onActivateTrial,
  isActivatingTrial,
  onRevokeKey,
  isRevokingKey,
}) => {
  // Live Countdown Timer
  const [timeLeft, setTimeLeft] = useState<{ days: number; hours: number; minutes: number; seconds: number }>({
    days: 0,
    hours: 0,
    minutes: 0,
    seconds: 0,
  });

  useEffect(() => {
    if (!activeSub) return;

    const updateTimer = () => {
      const now = new Date().getTime();
      const end = new Date(activeSub.endDate).getTime();
      const diff = Math.max(0, end - now);

      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diff % (1000 * 60)) / 1000);

      setTimeLeft({ days, hours, minutes, seconds });
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [activeSub]);

  // Traffic calculation
  const usedGB = (activeSub?.usedTrafficBytes || 14.8 * 1024 * 1024 * 1024) / (1024 * 1024 * 1024);
  const totalGB = activeSub?.trafficLimitBytes ? activeSub.trafficLimitBytes / (1024 * 1024 * 1024) : 0; // 0 = unlimited
  const trafficPercent = totalGB > 0 ? Math.min(100, Math.round((usedGB / totalGB) * 100)) : 22;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="space-y-4"
    >
      {/* 1. Main Status & Orb Display */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-b from-[#111827]/80 to-[#0b0f19]/90 border border-white/10 p-5 shadow-2xl backdrop-blur-xl">
        {/* Glow effect */}
        <div
          className={`absolute -top-12 left-1/2 -translate-x-1/2 w-48 h-48 rounded-full blur-3xl pointer-events-none transition-all duration-700 ${
            activeSub?.isActive ? 'bg-emerald-500/20' : 'bg-amber-500/15'
          }`}
        />

        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <span className="relative flex h-3 w-3">
              {activeSub?.isActive && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              )}
              <span
                className={`relative inline-flex rounded-full h-3 w-3 ${
                  activeSub?.isActive ? 'bg-emerald-500' : 'bg-amber-500'
                }`}
              />
            </span>
            <span className="text-xs font-semibold tracking-wide uppercase text-slate-300">
              {activeSub?.isActive ? 'Подписка активна' : 'Подписка не активна'}
            </span>
          </div>

          <span className="text-[11px] font-mono text-cyan-400/90 bg-cyan-950/40 border border-cyan-800/40 px-2 py-0.5 rounded-full">
            VLESS Reality
          </span>
        </div>

        {/* Live Countdown Grid or Onboarding */}
        {activeSub?.isActive ? (
          <div className="text-center py-2">
            <p className="text-[11px] uppercase tracking-wider text-slate-400 mb-2">Осталось времени</p>
            <div className="grid grid-cols-4 gap-2 max-w-xs mx-auto">
              <div className="bg-white/5 border border-white/5 rounded-2xl py-2 px-1">
                <span className="block text-2xl font-black text-white font-mono">{timeLeft.days}</span>
                <span className="text-[10px] text-slate-400 uppercase">Дней</span>
              </div>
              <div className="bg-white/5 border border-white/5 rounded-2xl py-2 px-1">
                <span className="block text-2xl font-black text-white font-mono">
                  {String(timeLeft.hours).padStart(2, '0')}
                </span>
                <span className="text-[10px] text-slate-400 uppercase">Часов</span>
              </div>
              <div className="bg-white/5 border border-white/5 rounded-2xl py-2 px-1">
                <span className="block text-2xl font-black text-white font-mono">
                  {String(timeLeft.minutes).padStart(2, '0')}
                </span>
                <span className="text-[10px] text-slate-400 uppercase">Мин</span>
              </div>
              <div className="bg-white/5 border border-white/5 rounded-2xl py-2 px-1">
                <span className="block text-2xl font-black text-emerald-400 font-mono">
                  {String(timeLeft.seconds).padStart(2, '0')}
                </span>
                <span className="text-[10px] text-slate-400 uppercase">Сек</span>
              </div>
            </div>

            <p className="text-xs text-slate-400 mt-3">
              Тариф: <strong className="text-white">{activeSub.planName}</strong>
            </p>
          </div>
        ) : (
          <div className="text-center py-4">
            <ShieldAlert className="w-12 h-12 mx-auto text-amber-400 mb-2 opacity-80" />
            <h3 className="text-base font-bold text-white mb-1">Защитите ваш интернет</h3>
            <p className="text-xs text-slate-400 max-w-xs mx-auto mb-4">
              Обход любых блокировок, маскировка под Google/Chrome и неограниченная скорость до 1 Гбит/с.
            </p>

            {!user.freeTrialUsed ? (
              <button
                id="home-activate-trial-btn"
                disabled={isActivatingTrial}
                onClick={onActivateTrial}
                className="w-full py-3 px-4 rounded-2xl bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-black font-bold text-sm flex items-center justify-center space-x-2 shadow-lg shadow-emerald-950/40 active:scale-98 transition-all"
              >
                <Sparkles className="w-4 h-4" />
                <span>{isActivatingTrial ? 'Активация...' : 'Активировать 3 дня бесплатно'}</span>
              </button>
            ) : (
              <button
                id="home-get-plan-btn"
                onClick={onOpenPlans}
                className="w-full py-3 px-4 rounded-2xl bg-gradient-to-r from-cyan-500 to-emerald-500 text-black font-bold text-sm flex items-center justify-center space-x-2 shadow-lg shadow-cyan-950/40 active:scale-98 transition-all"
              >
                <Zap className="w-4 h-4" />
                <span>Выбрать тарифный план</span>
              </button>
            )}
          </div>
        )}

        {/* Traffic Progress */}
        {activeSub?.isActive && (
          <div className="mt-4 pt-4 border-t border-white/5">
            <div className="flex justify-between items-center text-xs mb-1.5">
              <span className="text-slate-400">Использовано трафика</span>
              <span className="font-mono font-medium text-slate-200">
                {usedGB.toFixed(1)} ГБ {totalGB > 0 ? `/ ${totalGB} ГБ` : '(Безлимит)'}
              </span>
            </div>
            <div className="h-2 w-full bg-slate-800/80 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-cyan-500 to-emerald-400 rounded-full transition-all duration-500"
                style={{ width: `${trafficPercent}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* 2. Selected Location Selector Card */}
      <button
        id="home-change-location-btn"
        onClick={onOpenLocations}
        className="w-full rounded-2xl bg-[#0f1422]/90 border border-white/5 p-4 flex items-center justify-between hover:border-white/15 transition-all text-left group"
      >
        <div className="flex items-center space-x-3.5">
          <div className="text-2xl p-2 rounded-xl bg-white/5 border border-white/5 flex items-center justify-center">
            {currentServer.flag}
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h4 className="text-sm font-bold text-white group-hover:text-cyan-400 transition-colors">
                {currentServer.country}, {currentServer.city}
              </h4>
              <span className="text-[10px] bg-emerald-950/50 text-emerald-400 border border-emerald-800/40 px-1.5 py-0.2 rounded font-mono">
                {currentServer.pingMs} ms
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">Высокоскоростной шлюз • Без фильтрации</p>
          </div>
        </div>

        <div className="flex items-center space-x-1 text-slate-400 group-hover:text-white transition-colors">
          <span className="text-xs">Сменить</span>
          <ChevronRight className="w-4 h-4" />
        </div>
      </button>

      {/* 3. VLESS Key & Client Connection Actions */}
      {activeSub?.isActive && activeSub.vlessLink && (
        <div className="rounded-2xl bg-[#0e1320] border border-white/10 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center space-x-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Ваш VLESS Reality ключ</span>
            </span>

            <button
              id="home-open-qr-btn"
              onClick={onOpenQr}
              className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center space-x-1 bg-cyan-950/30 px-2.5 py-1 rounded-lg border border-cyan-800/40 transition-colors"
            >
              <QrCode className="w-3.5 h-3.5" />
              <span>QR-код</span>
            </button>
          </div>

          {/* Truncated Key Display */}
          <div
            onClick={onCopyKey}
            className="p-3 rounded-xl bg-black/40 border border-white/5 font-mono text-[11px] text-slate-400 break-all cursor-pointer hover:border-cyan-500/40 transition-colors relative group"
            title="Нажмите чтобы скопировать"
          >
            <span className="text-slate-200">{activeSub.vlessLink.substring(0, 52)}...</span>
            <span className="absolute right-2.5 top-2.5 bg-slate-800/90 text-cyan-400 p-1.5 rounded-lg opacity-80 group-hover:opacity-100 transition-opacity">
              {hasCopied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
            </span>
          </div>

          {/* Copy Button */}
          <button
            id="home-copy-key-btn"
            onClick={onCopyKey}
            className="w-full py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-emerald-500 hover:from-cyan-400 hover:to-emerald-400 text-black font-bold text-xs flex items-center justify-center space-x-2 shadow-md transition-all active:scale-98"
          >
            {hasCopied ? (
              <>
                <Check className="w-3.5 h-3.5" />
                <span>Ключ скопирован в буфер!</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span>Скопировать ключ VLESS</span>
              </>
            )}
          </button>

          {/* Direct App Launch Links */}
          <div className="pt-2 border-t border-white/5">
            <p className="text-[11px] text-slate-400 mb-2">Открыть в клиенте (1 клик):</p>
            <div className="grid grid-cols-3 gap-2">
              <a
                href={`happ://vless/${encodeURIComponent(activeSub.vlessLink)}`}
                className="py-1.5 px-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 text-[11px] text-center font-medium border border-white/5 transition-colors flex items-center justify-center space-x-1"
              >
                <span>Happ</span>
                <ExternalLink className="w-2.5 h-2.5 opacity-60" />
              </a>
              <a
                href={`v2rayng://install-config?url=${encodeURIComponent(activeSub.vlessLink)}`}
                className="py-1.5 px-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 text-[11px] text-center font-medium border border-white/5 transition-colors flex items-center justify-center space-x-1"
              >
                <span>v2rayNG</span>
                <ExternalLink className="w-2.5 h-2.5 opacity-60" />
              </a>
              <a
                href={`streisand://import/${encodeURIComponent(activeSub.vlessLink)}`}
                className="py-1.5 px-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 text-[11px] text-center font-medium border border-white/5 transition-colors flex items-center justify-center space-x-1"
              >
                <span>Streisand</span>
                <ExternalLink className="w-2.5 h-2.5 opacity-60" />
              </a>
            </div>
          </div>

          {/* Revoke button */}
          <div className="pt-1">
            <button
              id="home-revoke-key-btn"
              disabled={isRevokingKey}
              onClick={onRevokeKey}
              className="w-full py-1.5 text-[11px] text-amber-400/80 hover:text-amber-300 border border-amber-900/40 bg-amber-950/20 hover:bg-amber-950/30 rounded-lg flex items-center justify-center space-x-1.5 transition-all"
            >
              <RefreshCw className={`w-3 h-3 ${isRevokingKey ? 'animate-spin' : ''}`} />
              <span>{isRevokingKey ? 'Перевыпуск в Marzban...' : 'Сменить ключ при утечке (Revoke)'}</span>
            </button>
          </div>
        </div>
      )}
    </motion.div>
  );
};
