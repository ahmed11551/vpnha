import React, { useState, useEffect } from 'react';
import {
  Shield,
  Zap,
  Globe,
  Users,
  Wallet,
  Check,
  Sparkles,
  ExternalLink,
  ChevronRight,
  Loader2,
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import {
  ActiveSubscription,
  PaymentItem,
  ReferralStats,
  ServerLocation,
  SubscriptionPlan,
  UserAccount,
} from '../types';
import { useTelegram } from '../hooks/useTelegram';
import { api } from '../api';
import { HomeTab } from './tabs/HomeTab';
import { PlansTab } from './tabs/PlansTab';
import { LocationsTab } from './tabs/LocationsTab';
import { ReferralTab } from './tabs/ReferralTab';
import { BalanceTab } from './tabs/BalanceTab';
import { QrModal } from './QrModal';
import { Toast } from './Toast';

const DEFAULT_LOCATIONS: ServerLocation[] = [
  { id: 'de-fra', country: 'Германия', countryCode: 'DE', city: 'Франкфурт', flag: '🇩🇪', pingMs: 32, protocol: 'VLESS Reality', status: 'online', loadPercent: 42 },
  { id: 'nl-ams', country: 'Нидерланды', countryCode: 'NL', city: 'Амстердам', flag: '🇳🇱', pingMs: 38, protocol: 'VLESS Reality', status: 'online', loadPercent: 56 },
  { id: 'fi-hel', country: 'Финляндия', countryCode: 'FI', city: 'Хельсинки', flag: '🇫🇮', pingMs: 24, protocol: 'VLESS Reality', status: 'online', loadPercent: 28 },
  { id: 'se-sto', country: 'Швеция', countryCode: 'SE', city: 'Стокгольм', flag: '🇸🇪', pingMs: 29, protocol: 'VLESS Reality', status: 'online', loadPercent: 35 },
  { id: 'kz-ala', country: 'Казахстан', countryCode: 'KZ', city: 'Алматы', flag: '🇰🇿', pingMs: 45, protocol: 'VLESS Reality', status: 'online', loadPercent: 61 },
  { id: 'tr-ist', country: 'Турция', countryCode: 'TR', city: 'Стамбул', flag: '🇹🇷', pingMs: 52, protocol: 'VLESS Reality', status: 'online', loadPercent: 49 },
  { id: 'us-nyc', country: 'США', countryCode: 'US', city: 'Нью-Йорк', flag: '🇺🇸', pingMs: 115, protocol: 'VLESS Reality', status: 'online', loadPercent: 39 },
];

const DEFAULT_PLANS: SubscriptionPlan[] = [
  { id: '1m', name: '1 Месяц', days: 30, price: 199, popular: false },
  { id: '3m', name: '3 Месяца', days: 90, price: 499, popular: false },
  { id: '6m', name: '6 Месяцев', days: 180, price: 899, popular: true, badge: 'ХИТ ПРОДАЖ' },
  { id: '12m', name: '12 Месяцев', days: 365, price: 1499, popular: false },
];

export const MiniAppSimulator: React.FC = () => {
  const { tg, user: tgUser, startParam, hapticImpact, hapticNotification, hapticSelection } = useTelegram();

  const [activeTab, setActiveTab] = useState<'home' | 'plans' | 'locations' | 'referral' | 'balance'>('home');
  const [locations, setLocations] = useState<ServerLocation[]>(DEFAULT_LOCATIONS);
  const [currentServer, setCurrentServer] = useState<ServerLocation>(DEFAULT_LOCATIONS[0]);
  const [plans, setPlans] = useState<SubscriptionPlan[]>(DEFAULT_PLANS);
  const [paymentHistory, setPaymentHistory] = useState<PaymentItem[]>([]);
  const [referralStats, setReferralStats] = useState<ReferralStats | null>(null);

  const [user, setUser] = useState<UserAccount>({
    id: 1,
    telegramId: tgUser?.id || 98765432,
    username: tgUser?.username || 'tg_user',
    firstName: tgUser?.first_name || 'Пользователь',
    balance: 0.0,
    refCode: 'NX77',
    refLink: 'https://t.me/NexusVpnBot?start=ref_NX77',
    freeTrialUsed: false,
    marzbanUsername: `tg_${tgUser?.id || 98765432}_nx77`,
  });

  const [activeSub, setActiveSub] = useState<ActiveSubscription | null>({
    id: 101,
    planName: '6 Месяцев',
    startDate: new Date(Date.now() - 5 * 86400000).toISOString(),
    endDate: new Date(Date.now() + 175 * 86400000).toISOString(),
    daysLeft: 175,
    vlessLink: 'vless://a4b8c9d0-1234-4567-89ab-cdef01234567@fra-01.nexusvpn.network:443?type=tcp&security=reality&pbk=7K3sW2y9vXqL9ZmN4jR1Pq8tY3uW0eA2bC5dE7fG8hI&fp=chrome&sni=dl.google.com&sid=a4b8c9d0&spx=%2F&flow=xtls-rprx-vision#NexusVPN-Germany-Reality',
    subscriptionUrl: 'https://vpn.nexusvpn.network/sub/a4b8c9d0-1234-4567-89ab-cdef01234567',
    usedTrafficBytes: 14.8 * 1024 * 1024 * 1024,
    trafficLimitBytes: 0,
    isActive: true,
  });

  // Modals & Feedback
  const [isQrOpen, setIsQrOpen] = useState(false);
  const [hasCopiedKey, setHasCopiedKey] = useState(false);
  const [hasCopiedRef, setHasCopiedRef] = useState(false);
  const [isActivatingTrial, setIsActivatingTrial] = useState(false);
  const [isRevokingKey, setIsRevokingKey] = useState(false);
  const [isProcessingPayment, setIsProcessingPayment] = useState(false);

  // Toast
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);

  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'success') => {
    setToast({ message, type });
    setTimeout(() => {
      setToast((prev) => (prev?.message === message ? null : prev));
    }, 4000);
  };

  // Initial Data Fetch
  useEffect(() => {
    const initAppData = async () => {
      try {
        const [plansData, locsData] = await Promise.all([
          api.getPlans().catch(() => DEFAULT_PLANS),
          api.getLocations().catch(() => DEFAULT_LOCATIONS),
        ]);
        if (plansData?.length) setPlans(plansData);
        if (locsData?.length) {
          setLocations(locsData);
          setCurrentServer(locsData[0]);
        }

        // Try authenticating with backend
        const authRes = await api.authTelegram(startParam).catch(() => null);
        if (authRes?.user) {
          setUser({
            id: authRes.user.id,
            telegramId: authRes.user.telegram_id,
            username: authRes.user.username,
            firstName: authRes.user.first_name,
            balance: authRes.user.balance,
            refCode: authRes.user.ref_code,
            refLink: authRes.user.ref_link,
            freeTrialUsed: authRes.user.free_trial_used,
            marzbanUsername: authRes.user.marzban_username,
          });

          if (authRes.subscription) {
            setActiveSub({
              id: authRes.subscription.id,
              planName: authRes.subscription.plan_name,
              startDate: authRes.subscription.start_date,
              endDate: authRes.subscription.end_date,
              daysLeft: Math.max(0, Math.floor(authRes.subscription.time_left_seconds / 86400)),
              timeLeftSeconds: authRes.subscription.time_left_seconds,
              vlessLink: authRes.subscription.vless_link,
              subscriptionUrl: authRes.subscription.subscription_url,
              usedTrafficBytes: authRes.subscription.used_traffic_bytes,
              trafficLimitBytes: authRes.subscription.traffic_limit_bytes,
              isActive: authRes.subscription.is_active,
            });
          }
        }

        // Fetch history & referral
        const [history, ref] = await Promise.all([
          api.getPaymentHistory().catch(() => []),
          api.getReferralStats().catch(() => null),
        ]);
        setPaymentHistory(history);
        if (ref) setReferralStats(ref);
      } catch (err) {
        console.log('App init error:', err);
      }
    };

    initAppData();
  }, [startParam]);

  // Tab navigation with haptic
  const handleTabChange = (tab: typeof activeTab) => {
    hapticSelection();
    setActiveTab(tab);
  };

  // Copy Key Action
  const handleCopyKey = () => {
    if (!activeSub?.vlessLink) return;
    navigator.clipboard.writeText(activeSub.vlessLink);
    setHasCopiedKey(true);
    hapticNotification('success');
    showToast('Ключ VLESS скопирован в буфер обмена!');
    setTimeout(() => setHasCopiedKey(false), 2500);
  };

  // Copy Referral Link
  const handleCopyRefLink = () => {
    const link = referralStats?.refLink || user.refLink;
    navigator.clipboard.writeText(link);
    setHasCopiedRef(true);
    hapticNotification('success');
    showToast('Реферальная ссылка скопирована!');
    setTimeout(() => setHasCopiedRef(false), 2500);
  };

  // Trial Activation
  const handleActivateTrial = async () => {
    setIsActivatingTrial(true);
    hapticImpact('medium');
    try {
      const res = await api.activateTrial();
      setActiveSub({
        id: Date.now(),
        planName: 'Пробный (3 дня)',
        startDate: new Date().toISOString(),
        endDate: res.end_date || new Date(Date.now() + 3 * 86400000).toISOString(),
        daysLeft: 3,
        vlessLink: res.vless_link || currentServer.protocol,
        subscriptionUrl: res.subscription_url,
        usedTrafficBytes: 0,
        trafficLimitBytes: 0,
        isActive: true,
      });
      setUser((prev) => ({ ...prev, freeTrialUsed: true }));
      hapticNotification('success');
      showToast('3 дня бесплатного VPN успешно активированы!');
    } catch (err: any) {
      hapticNotification('error');
      showToast(err.message || 'Ошибка активации пробного периода', 'error');
    } finally {
      setIsActivatingTrial(false);
    }
  };

  // Revoke Key
  const handleRevokeKey = async () => {
    setIsRevokingKey(true);
    hapticImpact('heavy');
    try {
      const res = await api.revokeKey();
      if (res.vless_link) {
        setActiveSub((prev) =>
          prev
            ? {
                ...prev,
                vlessLink: res.vless_link,
                subscriptionUrl: res.subscription_url || prev.subscriptionUrl,
              }
            : null
        );
      }
      hapticNotification('success');
      showToast('Старый ключ аннулирован. Выпущен новый VLESS Reality!');
    } catch (err) {
      // Local fallback
      const newUuid = `a${Math.random().toString(16).substring(2, 10)}-4b8c-4211-b0e9-${Math.random().toString(16).substring(2, 14)}`;
      const newVless = `vless://${newUuid}@${currentServer.city.toLowerCase()}-01.nexusvpn.network:443?type=tcp&security=reality&pbk=7K3sW2y9vXqL9ZmN4jR1Pq8tY3uW0eA2bC5dE7fG8hI&fp=chrome&sni=dl.google.com&sid=a4b8c9d0&spx=%2F&flow=xtls-rprx-vision#NexusVPN-${currentServer.country}-Reality`;
      setActiveSub((prev) => (prev ? { ...prev, vlessLink: newVless } : null));
      hapticNotification('success');
      showToast('Ключ перевыпущен (новый UUID)!');
    } finally {
      setIsRevokingKey(false);
    }
  };

  // Purchase with Balance
  const handlePurchaseWithBalance = async (planId: string, promoCode?: string) => {
    setIsProcessingPayment(true);
    hapticImpact('heavy');
    try {
      const res = await api.purchaseSubscription(planId, promoCode);
      const plan = plans.find((p) => p.id === planId);
      setActiveSub({
        id: Date.now(),
        planName: plan?.name || 'Тариф',
        startDate: new Date().toISOString(),
        endDate: res.end_date || new Date(Date.now() + (plan?.days || 30) * 86400000).toISOString(),
        daysLeft: plan?.days || 30,
        vlessLink: res.vless_link || activeSub?.vlessLink,
        subscriptionUrl: res.subscription_url || activeSub?.subscriptionUrl,
        usedTrafficBytes: 0,
        trafficLimitBytes: 0,
        isActive: true,
      });
      if (res.balance !== undefined) {
        setUser((prev) => ({ ...prev, balance: res.balance }));
      }
      hapticNotification('success');
      showToast(res.message || 'Подписка успешно продлена!');
      setActiveTab('home');
    } catch (err: any) {
      hapticNotification('error');
      showToast(err.message || 'Не удалось оплатить подписку', 'error');
    } finally {
      setIsProcessingPayment(false);
    }
  };

  // Direct Payment / Invoice
  const handleDirectPayment = async (planId: string, amount: number, promoCode?: string) => {
    setIsProcessingPayment(true);
    hapticImpact('medium');
    try {
      const res = await api.createPayment(amount, 'cryptobot', planId, promoCode);
      if (res.pay_url) {
        window.open(res.pay_url, '_blank');
        showToast('Счет на оплату сформирован! Открываем шлюз...');
      }
    } catch (err: any) {
      hapticNotification('error');
      showToast(err.message || 'Ошибка создания счета', 'error');
    } finally {
      setIsProcessingPayment(false);
    }
  };

  // Top Up Balance
  const handleTopUp = async (amount: number, gateway: string) => {
    setIsProcessingPayment(true);
    hapticImpact('medium');
    try {
      const res = await api.createPayment(amount, gateway);
      if (res.pay_url) {
        window.open(res.pay_url, '_blank');
        showToast(`Счёт на ${amount} ₽ создан! Ожидание оплаты...`);
      }
    } catch (err: any) {
      hapticNotification('error');
      showToast(err.message || 'Ошибка создания счета', 'error');
    } finally {
      setIsProcessingPayment(false);
    }
  };

  // Sandbox Top Up
  const handleSandboxTopUp = async (amount: number) => {
    try {
      const res = await api.sandboxTopUp(amount);
      setUser((prev) => ({ ...prev, balance: res.new_balance }));
      hapticNotification('success');
      showToast(`Тестовый баланс пополнен на +${amount} ₽!`);
    } catch {
      setUser((prev) => ({ ...prev, balance: prev.balance + amount }));
      hapticNotification('success');
      showToast(`Баланс пополнен на +${amount} ₽!`);
    }
  };

  // Validate Promo Code
  const handleValidatePromo = async (code: string) => {
    hapticImpact('light');
    return await api.activatePromoCode(code);
  };

  // Server selection
  const handleSelectServer = (server: ServerLocation) => {
    setCurrentServer(server);
    hapticSelection();
    showToast(`Сервер переключён на ${server.country} (${server.city})`);
    setActiveTab('home');
  };

  return (
    <div className="min-h-screen bg-[#07090e] text-slate-100 flex flex-col justify-between selection:bg-cyan-500 selection:text-black">
      {/* Toast Notification */}
      <Toast message={toast?.message || null} type={toast?.type} onClose={() => setToast(null)} />

      {/* QR Code Modal */}
      <QrModal
        isOpen={isQrOpen}
        onClose={() => setIsQrOpen(false)}
        vlessLink={activeSub?.vlessLink || ''}
        serverName={`${currentServer.country}, ${currentServer.city}`}
        onCopy={handleCopyKey}
        hasCopied={hasCopiedKey}
      />

      {/* Top App Header */}
      <header className="sticky top-0 z-30 bg-[#07090e]/80 backdrop-blur-xl border-b border-white/5 px-4 py-3">
        <div className="max-w-md mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-500 to-emerald-400 flex items-center justify-center text-black font-black text-xs shadow-lg shadow-cyan-950/50">
              NV
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="text-xs font-bold text-white tracking-wide">NexusVPN</span>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              </div>
              <p className="text-[10px] text-slate-400 font-mono">@{user.username || 'user'}</p>
            </div>
          </div>

          {/* Quick Balance Button */}
          <button
            id="header-balance-btn"
            onClick={() => handleTabChange('balance')}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-[#0f1422] hover:bg-[#161f33] border border-white/10 transition-all text-xs font-mono active:scale-95"
            title="Перейти к пополнению баланса"
          >
            <Wallet className="w-3.5 h-3.5 text-cyan-400" />
            <span className="font-bold text-white">{user.balance.toFixed(2)} ₽</span>
          </button>
        </div>
      </header>

      {/* Main Tab Screen Viewport */}
      <main className="flex-1 max-w-md w-full mx-auto p-4 pb-24">
        <AnimatePresence mode="wait">
          {activeTab === 'home' && (
            <HomeTab
              key="home"
              user={user}
              activeSub={activeSub}
              currentServer={currentServer}
              onOpenLocations={() => handleTabChange('locations')}
              onOpenPlans={() => handleTabChange('plans')}
              onOpenQr={() => setIsQrOpen(true)}
              onCopyKey={handleCopyKey}
              hasCopied={hasCopiedKey}
              onActivateTrial={handleActivateTrial}
              isActivatingTrial={isActivatingTrial}
              onRevokeKey={handleRevokeKey}
              isRevokingKey={isRevokingKey}
            />
          )}

          {activeTab === 'plans' && (
            <PlansTab
              key="plans"
              plans={plans}
              user={user}
              onPurchaseWithBalance={handlePurchaseWithBalance}
              onDirectPayment={handleDirectPayment}
              isProcessing={isProcessingPayment}
              onValidatePromo={handleValidatePromo}
            />
          )}

          {activeTab === 'locations' && (
            <LocationsTab
              key="locations"
              locations={locations}
              currentServer={currentServer}
              onSelectServer={handleSelectServer}
            />
          )}

          {activeTab === 'referral' && (
            <ReferralTab
              key="referral"
              user={user}
              stats={referralStats}
              onCopyRefLink={handleCopyRefLink}
              hasCopied={hasCopiedRef}
            />
          )}

          {activeTab === 'balance' && (
            <BalanceTab
              key="balance"
              user={user}
              paymentHistory={paymentHistory}
              onTopUp={handleTopUp}
              onSandboxTopUp={handleSandboxTopUp}
              isProcessing={isProcessingPayment}
            />
          )}
        </AnimatePresence>
      </main>

      {/* Bottom Floating Navigation Bar */}
      <nav className="fixed bottom-0 left-0 right-0 z-40 bg-[#07090e]/90 backdrop-blur-2xl border-t border-white/5 py-2 px-3">
        <div className="max-w-md mx-auto grid grid-cols-5 gap-1">
          <button
            id="tab-home-btn"
            onClick={() => handleTabChange('home')}
            className={`flex flex-col items-center justify-center py-1.5 rounded-xl transition-all ${
              activeTab === 'home' ? 'text-cyan-400' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Shield className="w-5 h-5" />
            <span className="text-[10px] font-medium mt-1">Главная</span>
          </button>

          <button
            id="tab-plans-btn"
            onClick={() => handleTabChange('plans')}
            className={`flex flex-col items-center justify-center py-1.5 rounded-xl transition-all ${
              activeTab === 'plans' ? 'text-cyan-400' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Zap className="w-5 h-5" />
            <span className="text-[10px] font-medium mt-1">Тарифы</span>
          </button>

          <button
            id="tab-locations-btn"
            onClick={() => handleTabChange('locations')}
            className={`flex flex-col items-center justify-center py-1.5 rounded-xl transition-all ${
              activeTab === 'locations' ? 'text-cyan-400' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Globe className="w-5 h-5" />
            <span className="text-[10px] font-medium mt-1">Серверы</span>
          </button>

          <button
            id="tab-referral-btn"
            onClick={() => handleTabChange('referral')}
            className={`flex flex-col items-center justify-center py-1.5 rounded-xl transition-all ${
              activeTab === 'referral' ? 'text-cyan-400' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Users className="w-5 h-5" />
            <span className="text-[10px] font-medium mt-1">Рефералы</span>
          </button>

          <button
            id="tab-balance-btn"
            onClick={() => handleTabChange('balance')}
            className={`flex flex-col items-center justify-center py-1.5 rounded-xl transition-all ${
              activeTab === 'balance' ? 'text-cyan-400' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Wallet className="w-5 h-5" />
            <span className="text-[10px] font-medium mt-1">Баланс</span>
          </button>
        </div>
      </nav>
    </div>
  );
};
