import React, { useState } from 'react';
import { Check, Zap, Sparkles, Tag, Shield, Globe, Lock, ArrowRight, Loader2 } from 'lucide-react';
import { motion } from 'motion/react';
import { SubscriptionPlan, UserAccount } from '../../types';

interface PlansTabProps {
  plans: SubscriptionPlan[];
  user: UserAccount;
  onPurchaseWithBalance: (planId: string, promoCode?: string) => void;
  onDirectPayment: (planId: string, amount: number, promoCode?: string) => void;
  isProcessing: boolean;
  onValidatePromo: (code: string) => Promise<any>;
}

export const PlansTab: React.FC<PlansTabProps> = ({
  plans,
  user,
  onPurchaseWithBalance,
  onDirectPayment,
  isProcessing,
  onValidatePromo,
}) => {
  const [selectedPlanId, setSelectedPlanId] = useState<string>('6m');
  const [promoInput, setPromoInput] = useState<string>('');
  const [promoResult, setPromoResult] = useState<{
    code: string;
    discountPercent: number;
    bonusDays: number;
    message: string;
  } | null>(null);
  const [isValidatingPromo, setIsValidatingPromo] = useState(false);
  const [promoError, setPromoError] = useState<string>('');

  const selectedPlan = plans.find((p) => p.id === selectedPlanId) || plans[0];

  const handleApplyPromo = async () => {
    if (!promoInput.trim()) return;
    setIsValidatingPromo(true);
    setPromoError('');
    try {
      const res = await onValidatePromo(promoInput.trim());
      setPromoResult({
        code: res.code,
        discountPercent: res.discount_percent || 0,
        bonusDays: res.bonus_days || 0,
        message: res.message,
      });
    } catch (err: any) {
      setPromoError(err.message || 'Не удалось применить промокод');
      setPromoResult(null);
    } finally {
      setIsValidatingPromo(false);
    }
  };

  const calculateFinalPrice = (basePrice: number) => {
    if (!promoResult || promoResult.discountPercent <= 0) return basePrice;
    return Math.round(basePrice * (1 - promoResult.discountPercent / 100));
  };

  const finalPrice = selectedPlan ? calculateFinalPrice(selectedPlan.price) : 0;
  const canAffordWithBalance = user.balance >= finalPrice;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="space-y-4"
    >
      <div className="text-center pb-1">
        <h2 className="text-lg font-bold text-white">Тарифные планы NexusVPN</h2>
        <p className="text-xs text-slate-400">
          Максимальная скорость, отсутствие ограничений по устройствам и трафику
        </p>
      </div>

      {/* Plan Selection Cards Grid */}
      <div className="grid grid-cols-2 gap-3">
        {plans.map((plan) => {
          const isSelected = selectedPlanId === plan.id;
          const discountedPrice = calculateFinalPrice(plan.price);
          const perMonth = Math.round(discountedPrice / (plan.days / 30));

          return (
            <div
              key={plan.id}
              onClick={() => setSelectedPlanId(plan.id)}
              className={`relative cursor-pointer rounded-2xl p-4 transition-all duration-300 ${
                isSelected
                  ? 'bg-gradient-to-b from-[#162035] to-[#0f172a] border-2 border-cyan-400 shadow-lg shadow-cyan-950/40 scale-[1.02]'
                  : 'bg-[#0f1422]/90 border border-white/5 hover:border-white/15'
              }`}
            >
              {plan.popular && (
                <span className="absolute -top-2.5 right-3 bg-gradient-to-r from-amber-500 to-orange-500 text-[9px] font-black text-black px-2 py-0.5 rounded-full shadow">
                  ХИТ ПРОДАЖ
                </span>
              )}

              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                {plan.name}
              </h3>

              <div className="flex items-baseline space-x-1 mb-1">
                <span className="text-2xl font-black text-white font-mono">{discountedPrice} ₽</span>
                {promoResult && promoResult.discountPercent > 0 && (
                  <span className="text-xs text-slate-500 line-through font-mono">{plan.price} ₽</span>
                )}
              </div>

              <p className="text-[11px] text-cyan-400 font-medium">~{perMonth} ₽ / месяц</p>

              {isSelected && (
                <div className="absolute bottom-3 right-3 text-cyan-400">
                  <Check className="w-4 h-4" />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Promo Code Input Box */}
      <div className="rounded-2xl bg-[#0f1422] border border-white/10 p-3.5 space-y-2">
        <label className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5">
          <Tag className="w-3.5 h-3.5 text-cyan-400" />
          <span>Есть промокод?</span>
        </label>

        <div className="flex space-x-2">
          <input
            type="text"
            id="promo-input"
            value={promoInput}
            onChange={(e) => setPromoInput(e.target.value.toUpperCase())}
            placeholder="Например: NEXUS2026"
            className="flex-1 bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors uppercase font-mono"
          />
          <button
            id="apply-promo-btn"
            disabled={isValidatingPromo || !promoInput.trim()}
            onClick={handleApplyPromo}
            className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/15 text-white text-xs font-semibold border border-white/10 disabled:opacity-50 transition-colors flex items-center space-x-1"
          >
            {isValidatingPromo ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <span>Применить</span>}
          </button>
        </div>

        {promoResult && (
          <p className="text-xs text-emerald-400 flex items-center space-x-1">
            <Check className="w-3 h-3" />
            <span>{promoResult.message}</span>
          </p>
        )}
        {promoError && <p className="text-xs text-rose-400">{promoError}</p>}
      </div>

      {/* Checkout Action Card */}
      {selectedPlan && (
        <div className="rounded-2xl bg-gradient-to-b from-[#111827] to-[#0b0f19] border border-cyan-500/20 p-4 space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">Выбранный тариф:</span>
            <span className="font-bold text-white">{selectedPlan.name} ({selectedPlan.days} дней)</span>
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">Ваш текущий баланс:</span>
            <span className={`font-bold ${canAffordWithBalance ? 'text-emerald-400' : 'text-amber-400'}`}>
              {user.balance.toFixed(2)} ₽
            </span>
          </div>

          {canAffordWithBalance ? (
            <button
              id="buy-plan-balance-btn"
              disabled={isProcessing}
              onClick={() => onPurchaseWithBalance(selectedPlan.id, promoResult?.code)}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-black font-bold text-sm flex items-center justify-center space-x-2 shadow-lg shadow-emerald-950/40 transition-all active:scale-98"
            >
              {isProcessing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <Zap className="w-4 h-4" />
                  <span>Оплатить с баланса ({finalPrice} ₽)</span>
                </>
              )}
            </button>
          ) : (
            <div className="space-y-2">
              <button
                id="direct-pay-btn"
                disabled={isProcessing}
                onClick={() => onDirectPayment(selectedPlan.id, finalPrice, promoResult?.code)}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-emerald-500 hover:from-cyan-400 hover:to-emerald-400 text-black font-bold text-sm flex items-center justify-center space-x-2 shadow-lg shadow-cyan-950/40 transition-all active:scale-98"
              >
                {isProcessing ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <Zap className="w-4 h-4" />
                    <span>Купить сразу за {finalPrice} ₽</span>
                  </>
                )}
              </button>
              <p className="text-[11px] text-center text-slate-400">
                Оплата через Telegram Stars, CryptoBot или банковскую карту
              </p>
            </div>
          )}
        </div>
      )}

      {/* Feature Bullet Points */}
      <div className="grid grid-cols-2 gap-2 text-xs text-slate-300">
        <div className="flex items-center space-x-2 p-2.5 rounded-xl bg-white/5 border border-white/5">
          <Shield className="w-4 h-4 text-cyan-400 shrink-0" />
          <span>VLESS + Reality маскировка</span>
        </div>
        <div className="flex items-center space-x-2 p-2.5 rounded-xl bg-white/5 border border-white/5">
          <Globe className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>7 стран на выбор</span>
        </div>
        <div className="flex items-center space-x-2 p-2.5 rounded-xl bg-white/5 border border-white/5">
          <Lock className="w-4 h-4 text-purple-400 shrink-0" />
          <span>Zero Logs (строго без логов)</span>
        </div>
        <div className="flex items-center space-x-2 p-2.5 rounded-xl bg-white/5 border border-white/5">
          <Zap className="w-4 h-4 text-amber-400 shrink-0" />
          <span>До 1 Гбит/с YouTube 4K</span>
        </div>
      </div>
    </motion.div>
  );
};
