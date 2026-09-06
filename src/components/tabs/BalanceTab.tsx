import React, { useState } from 'react';
import {
  Wallet,
  ArrowDownLeft,
  CreditCard,
  Sparkles,
  Zap,
  CheckCircle2,
  Clock,
  ExternalLink,
  Loader2,
  PlusCircle,
} from 'lucide-react';
import { motion } from 'motion/react';
import { PaymentItem, UserAccount } from '../../types';

interface BalanceTabProps {
  user: UserAccount;
  paymentHistory: PaymentItem[];
  onTopUp: (amount: number, gateway: string) => Promise<void>;
  onSandboxTopUp: (amount: number) => Promise<void>;
  isProcessing: boolean;
}

const PRESET_AMOUNTS = [199, 499, 899, 1499];

const GATEWAYS = [
  {
    id: 'cryptobot',
    name: 'CryptoBot',
    desc: 'USDT, TON, BTC, TRX (0% комиссии)',
    icon: '⚡',
    badge: 'КРИПТА',
  },
  {
    id: 'stars',
    name: 'Telegram Stars',
    desc: 'Оплата звездами прямо в приложении',
    icon: '⭐',
    badge: 'STARS',
  },
  {
    id: 'yookassa',
    name: 'МИР / СБП / Карты',
    desc: 'Любые российские карты и СБП QR',
    icon: '💳',
    badge: 'СБП / МИР',
  },
];

export const BalanceTab: React.FC<BalanceTabProps> = ({
  user,
  paymentHistory,
  onTopUp,
  onSandboxTopUp,
  isProcessing,
}) => {
  const [selectedAmount, setSelectedAmount] = useState<number>(499);
  const [customAmount, setCustomAmount] = useState<string>('');
  const [selectedGateway, setSelectedGateway] = useState<string>('cryptobot');
  const [isSandboxLoading, setIsSandboxLoading] = useState(false);

  const activeAmount = customAmount ? parseFloat(customAmount) || 0 : selectedAmount;

  const handleTopUpSubmit = async () => {
    if (activeAmount < 10) return;
    await onTopUp(activeAmount, selectedGateway);
  };

  const handleQuickDemoTopUp = async () => {
    setIsSandboxLoading(true);
    try {
      await onSandboxTopUp(500);
    } finally {
      setIsSandboxLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="space-y-4"
    >
      {/* 1. Large Balance Display */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-b from-[#111827] to-[#0b0f19] border border-white/10 p-5 shadow-2xl backdrop-blur-xl text-center">
        <div className="absolute -top-16 left-1/2 -translate-x-1/2 w-48 h-48 bg-cyan-500/15 rounded-full blur-3xl pointer-events-none" />

        <div className="flex items-center justify-center space-x-1.5 text-xs text-slate-400 font-semibold uppercase tracking-wider mb-1">
          <Wallet className="w-3.5 h-3.5 text-cyan-400" />
          <span>Текущий баланс аккаунта</span>
        </div>

        <div className="text-4xl font-black text-white font-mono tracking-tight my-2">
          {user.balance.toFixed(2)}{' '}
          <span className="text-2xl text-cyan-400 font-normal font-sans">₽</span>
        </div>

        <p className="text-[11px] text-slate-400">
          ID аккаунта: <span className="font-mono text-slate-300">#{user.telegramId}</span>
        </p>

        {/* Sandbox test top up button */}
        <div className="mt-3 pt-3 border-t border-white/5 flex justify-center">
          <button
            id="sandbox-topup-btn"
            disabled={isSandboxLoading}
            onClick={handleQuickDemoTopUp}
            className="text-[11px] text-cyan-400/90 hover:text-cyan-300 bg-cyan-950/30 border border-cyan-800/40 px-3 py-1 rounded-full flex items-center space-x-1 transition-all"
            title="Тестовое моментальное пополнение для песочницы"
          >
            <PlusCircle className="w-3 h-3" />
            <span>{isSandboxLoading ? 'Зачисление...' : '+500 ₽ Тест (Sandbox)'}</span>
          </button>
        </div>
      </div>

      {/* 2. Amount Selector */}
      <div className="rounded-2xl bg-[#0f1422] border border-white/10 p-4 space-y-3">
        <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
          Выберите сумму пополнения
        </span>

        <div className="grid grid-cols-4 gap-2">
          {PRESET_AMOUNTS.map((amt) => (
            <button
              key={amt}
              type="button"
              onClick={() => {
                setSelectedAmount(amt);
                setCustomAmount('');
              }}
              className={`py-2.5 px-2 rounded-xl text-xs font-bold font-mono transition-all ${
                selectedAmount === amt && !customAmount
                  ? 'bg-cyan-500 text-black shadow-md shadow-cyan-950/50'
                  : 'bg-white/5 text-slate-300 hover:bg-white/10 border border-white/5'
              }`}
            >
              {amt} ₽
            </button>
          ))}
        </div>

        <div className="flex items-center space-x-2 bg-black/40 border border-white/10 rounded-xl px-3 py-2">
          <input
            type="number"
            min="10"
            max="50000"
            value={customAmount}
            onChange={(e) => setCustomAmount(e.target.value)}
            placeholder="Или введите другую сумму (мин. 10 ₽)"
            className="w-full bg-transparent text-xs text-white placeholder-slate-500 focus:outline-none font-mono"
          />
          <span className="text-xs text-slate-400 font-bold">₽</span>
        </div>
      </div>

      {/* 3. Gateway Selector */}
      <div className="rounded-2xl bg-[#0f1422] border border-white/10 p-4 space-y-3">
        <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
          Способ оплаты
        </span>

        <div className="space-y-2">
          {GATEWAYS.map((gw) => {
            const isSelected = selectedGateway === gw.id;
            return (
              <div
                key={gw.id}
                onClick={() => setSelectedGateway(gw.id)}
                className={`cursor-pointer rounded-xl p-3 flex items-center justify-between transition-all ${
                  isSelected
                    ? 'bg-gradient-to-r from-cyan-950/40 to-emerald-950/40 border-2 border-cyan-500'
                    : 'bg-white/5 border border-white/5 hover:border-white/15'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <span className="text-xl">{gw.icon}</span>
                  <div>
                    <div className="flex items-center space-x-2">
                      <h4 className="text-xs font-bold text-white">{gw.name}</h4>
                      <span className="text-[9px] bg-white/10 text-cyan-400 font-mono px-1.5 py-0.2 rounded">
                        {gw.badge}
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-400 mt-0.5">{gw.desc}</p>
                  </div>
                </div>

                <div className="w-5 h-5 rounded-full border border-white/20 flex items-center justify-center">
                  {isSelected && <div className="w-2.5 h-2.5 rounded-full bg-cyan-400" />}
                </div>
              </div>
            );
          })}
        </div>

        <button
          id="proceed-topup-btn"
          disabled={isProcessing || activeAmount < 10}
          onClick={handleTopUpSubmit}
          className="w-full mt-2 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-emerald-500 hover:from-cyan-400 hover:to-emerald-400 text-black font-bold text-sm flex items-center justify-center space-x-2 shadow-lg shadow-cyan-950/40 transition-all active:scale-98 disabled:opacity-50"
        >
          {isProcessing ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <>
              <Zap className="w-4 h-4" />
              <span>Пополнить на {activeAmount} ₽</span>
            </>
          )}
        </button>
      </div>

      {/* 4. Payment History */}
      <div className="rounded-2xl bg-[#0f1422] border border-white/5 p-4 space-y-3">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider">История операций</h3>

        {paymentHistory.length === 0 ? (
          <p className="text-xs text-slate-500 text-center py-4">Операций пополнения пока нет</p>
        ) : (
          <div className="space-y-2">
            {paymentHistory.map((item) => {
              const isPaid = item.status === 'paid';
              const dateStr = new Date(item.created_at).toLocaleDateString('ru-RU', {
                day: '2-digit',
                month: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
              });

              return (
                <div
                  key={item.order_id}
                  className="p-2.5 rounded-xl bg-white/5 border border-white/5 flex items-center justify-between text-xs"
                >
                  <div className="flex items-center space-x-2.5">
                    {isPaid ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    ) : (
                      <Clock className="w-4 h-4 text-amber-400 shrink-0" />
                    )}
                    <div>
                      <p className="font-semibold text-white">
                        {item.gateway.toUpperCase()} • {item.plan_id ? `Тариф ${item.plan_id}` : 'Баланс'}
                      </p>
                      <p className="text-[10px] text-slate-500 font-mono">{dateStr}</p>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className={`font-mono font-bold ${isPaid ? 'text-emerald-400' : 'text-amber-400'}`}>
                      +{item.amount} ₽
                    </span>
                    <span
                      className={`block text-[9px] uppercase font-semibold ${
                        isPaid ? 'text-emerald-500' : 'text-amber-500'
                      }`}
                    >
                      {isPaid ? 'Зачислено' : 'В ожидании'}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </motion.div>
  );
};
