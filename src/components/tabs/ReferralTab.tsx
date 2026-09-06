import React, { useState } from 'react';
import { Users, Copy, Check, Share2, DollarSign, Gift, ArrowUpRight, Award } from 'lucide-react';
import { motion } from 'motion/react';
import { ReferralStats, UserAccount } from '../../types';

interface ReferralTabProps {
  user: UserAccount;
  stats: ReferralStats | null;
  onCopyRefLink: () => void;
  hasCopied: boolean;
}

export const ReferralTab: React.FC<ReferralTabProps> = ({
  user,
  stats,
  onCopyRefLink,
  hasCopied,
}) => {
  const refLink = stats?.refLink || user.refLink || `https://t.me/NexusVpnBot?start=ref_${user.refCode}`;
  const invitedCount = stats?.invitedCount ?? 3;
  const totalEarned = stats?.totalEarnedRub ?? 450.0;

  const handleShareTelegram = () => {
    const shareText = encodeURIComponent(
      '🔒 Попробуй быстрый и надёжный VPN с протоколом VLESS Reality! Держи 3 дня бесплатно и бонус 100 ₽:'
    );
    const url = `https://t.me/share/url?url=${encodeURIComponent(refLink)}&text=${shareText}`;
    window.open(url, '_blank');
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="space-y-4"
    >
      <div className="text-center pb-1">
        <h2 className="text-lg font-bold text-white">Реферальная программа</h2>
        <p className="text-xs text-slate-400">
          Приглашайте друзей и получайте 15% с каждой их оплаты на баланс
        </p>
      </div>

      {/* Stats Cards Grid */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-2xl bg-[#0f1422] border border-white/10 p-4">
          <div className="flex items-center space-x-2 text-cyan-400 text-xs font-semibold mb-1">
            <Users className="w-4 h-4" />
            <span>Друзей в сети</span>
          </div>
          <span className="text-2xl font-black text-white font-mono">{invitedCount}</span>
          <p className="text-[11px] text-slate-400 mt-0.5">Активные рефералы</p>
        </div>

        <div className="rounded-2xl bg-[#0f1422] border border-white/10 p-4">
          <div className="flex items-center space-x-2 text-emerald-400 text-xs font-semibold mb-1">
            <DollarSign className="w-4 h-4" />
            <span>Заработано</span>
          </div>
          <span className="text-2xl font-black text-emerald-400 font-mono">+{totalEarned.toFixed(0)} ₽</span>
          <p className="text-[11px] text-slate-400 mt-0.5">15% комиссионных</p>
        </div>
      </div>

      {/* Referral Link Card */}
      <div className="rounded-2xl bg-gradient-to-b from-[#111827] to-[#0b0f19] border border-cyan-500/20 p-4 space-y-3">
        <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
          Ваша персональная ссылка
        </span>

        <div className="flex items-center space-x-2 bg-black/40 border border-white/10 rounded-xl p-2.5">
          <input
            type="text"
            readOnly
            value={refLink}
            className="w-full bg-transparent text-xs text-cyan-300 font-mono focus:outline-none select-all"
          />
          <button
            id="copy-ref-link-btn"
            onClick={onCopyRefLink}
            className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors shrink-0"
            title="Скопировать"
          >
            {hasCopied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
          </button>
        </div>

        <div className="grid grid-cols-2 gap-2 pt-1">
          <button
            id="copy-ref-btn-action"
            onClick={onCopyRefLink}
            className="py-2.5 px-3 rounded-xl bg-white/10 hover:bg-white/15 text-white font-semibold text-xs flex items-center justify-center space-x-1.5 transition-all border border-white/10"
          >
            {hasCopied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{hasCopied ? 'Скопировано!' : 'Скопировать'}</span>
          </button>

          <button
            id="share-telegram-btn"
            onClick={handleShareTelegram}
            className="py-2.5 px-3 rounded-xl bg-gradient-to-r from-cyan-500 to-emerald-500 hover:from-cyan-400 hover:to-emerald-400 text-black font-bold text-xs flex items-center justify-center space-x-1.5 shadow-md transition-all active:scale-98"
          >
            <Share2 className="w-3.5 h-3.5" />
            <span>Поделиться</span>
          </button>
        </div>
      </div>

      {/* Program Conditions */}
      <div className="rounded-2xl bg-[#0f1422] border border-white/5 p-4 space-y-3">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider">Как это работает?</h3>

        <div className="space-y-2.5 text-xs">
          <div className="flex items-start space-x-2.5">
            <span className="w-5 h-5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800 flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
              1
            </span>
            <p className="text-slate-300">
              Отправьте свою ссылку другу в Telegram.
            </p>
          </div>

          <div className="flex items-start space-x-2.5">
            <span className="w-5 h-5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800 flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
              2
            </span>
            <p className="text-slate-300">
              Друг получает <strong>3 дня пробного периода</strong> + быстрый старт.
            </p>
          </div>

          <div className="flex items-start space-x-2.5">
            <span className="w-5 h-5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800 flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
              3
            </span>
            <p className="text-slate-300">
              При каждой оплате тарифа вам сразу начисляется <strong>15% от суммы</strong> на основной баланс. Средства можно тратить на продление подписки!
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
