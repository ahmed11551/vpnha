import React, { useState, useEffect } from 'react';
import {
  Shield,
  Zap,
  CheckCircle2,
  Copy,
  QrCode,
  Globe2,
  CreditCard,
  Users,
  Smartphone,
  ExternalLink,
  RefreshCw,
  Plus,
  Share2,
  Sparkles,
  Server
} from 'lucide-react';
import { ServerLocation, SubscriptionPlan, UserAccount, ActiveSubscription } from '../types';

interface MiniAppSimulatorProps {
  onEventLog?: (log: string) => void;
}

export const MiniAppSimulator: React.FC<MiniAppSimulatorProps> = ({ onEventLog }) => {
  const [activeTab, setActiveTab] = useState<'home' | 'servers' | 'plans' | 'referrals' | 'guide'>('home');
  const [guidePlatform, setGuidePlatform] = useState<'happ' | 'amnezia' | 'v2rayng'>('happ');
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [showQrModal, setShowQrModal] = useState(false);
  const [showTopUpModal, setShowTopUpModal] = useState(false);
  const [topUpAmount, setTopUpAmount] = useState<number>(499);

  // User simulated state
  const [user, setUser] = useState<UserAccount>({
    id: 1,
    telegramId: 749102384,
    username: 'alex_cyber',
    firstName: 'Алексей',
    balance: 550.0,
    refCode: 'cyber77',
    refLink: 'https://t.me/asbvpn_bot?start=ref_cyber77',
    freeTrialUsed: false,
    marzbanUsername: 'tg_749102384',
  });

  const [activeSub, setActiveSub] = useState<ActiveSubscription | null>({
    id: 101,
    planName: 'Оптимальный 3 Месяца',
    startDate: new Date().toISOString(),
    endDate: new Date(Date.now() + 87 * 86400000).toISOString(),
    daysLeft: 87,
    vlessLink: 'vless://9e14a27c-3f94-4d2b-b6d8-7711ab3c9902@nl-ams-01.nexusvpn.network:443?type=tcp&security=reality&pbk=7K3sW2y9vXqL9ZmN4jR1Pq8tY3uW0eA2bC5dE7fG8hI&fp=chrome&sni=dl.google.com&sid=a4b8c9d0&spx=%2F&flow=xtls-rprx-vision#NexusVPN-Netherlands-Reality',
    subscriptionUrl: 'https://marzban.nexusvpn.network/sub/nexus_alex_cyber_9e14a27c',
    usedTrafficBytes: 1420500000, // 1.42 GB
    trafficLimitBytes: 0, // Unlimited
  });

  // Countdown timer state
  const [timeLeft, setTimeLeft] = useState({ days: 87, hours: 14, minutes: 22, seconds: 40 });

  useEffect(() => {
    // Initialize Telegram WebApp SDK if running inside Telegram
    try {
      const tg = (window as any).Telegram?.WebApp;
      if (tg) {
        tg.ready();
        tg.expand();
        if (tg.setHeaderColor) tg.setHeaderColor('#0b0f19');
        if (tg.setBackgroundColor) tg.setBackgroundColor('#07090e');
        if (tg.initDataUnsafe?.user) {
          const u = tg.initDataUnsafe.user;
          setUser(prev => ({
            ...prev,
            telegramId: u.id || prev.telegramId,
            username: u.username || prev.username,
            firstName: u.first_name || prev.firstName,
            refCode: u.username ? `ref_${u.username}` : `ref_${u.id}`,
            refLink: `https://t.me/asbvpn_bot?start=${u.username ? `ref_${u.username}` : `ref_${u.id}`}`,
            marzbanUsername: `tg_${u.id || prev.telegramId}`,
          }));
        }
      }
    } catch (e) {
      console.warn('Telegram WebApp init notice:', e);
    }

    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev.seconds > 0) return { ...prev, seconds: prev.seconds - 1 };
        if (prev.minutes > 0) return { ...prev, minutes: 59, seconds: 59 };
        if (prev.hours > 0) return { ...prev, hours: prev.hours - 1, minutes: 59, seconds: 59 };
        if (prev.days > 0) return { ...prev, days: prev.days - 1, hours: 23, minutes: 59, seconds: 59 };
        return prev;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const servers: ServerLocation[] = [
    { id: 'nl-ams', country: 'Нидерланды', countryCode: 'NL', city: 'Амстердам', flag: '🇳🇱', pingMs: 28, protocol: 'VLESS + Reality (XTLS Vision)', status: 'online', loadPercent: 34 },
    { id: 'de-fra', country: 'Германия', countryCode: 'DE', city: 'Франкфурт', flag: '🇩🇪', pingMs: 32, protocol: 'VLESS + Reality (XTLS Vision)', status: 'online', loadPercent: 48 },
    { id: 'fi-hel', country: 'Финляндия', countryCode: 'FI', city: 'Хельсинки', flag: '🇫🇮', pingMs: 19, protocol: 'VLESS + Reality (XTLS Vision)', status: 'online', loadPercent: 22 },
    { id: 'us-nyc', country: 'США', countryCode: 'US', city: 'Нью-Йорк', flag: '🇺🇸', pingMs: 95, protocol: 'VLESS + Reality (XTLS Vision)', status: 'online', loadPercent: 55 },
    { id: 'tr-ist', country: 'Турция', countryCode: 'TR', city: 'Стамбул', flag: '🇹🇷', pingMs: 42, protocol: 'VLESS + Reality (XTLS Vision)', status: 'online', loadPercent: 40 },
    { id: 'se-sto', country: 'Швеция', countryCode: 'SE', city: 'Стокгольм', flag: '🇸🇪', pingMs: 25, protocol: 'VLESS + Reality (XTLS Vision)', status: 'online', loadPercent: 18 },
  ];

  const [currentServer, setCurrentServer] = useState<ServerLocation>(servers[0]);

  const plans: SubscriptionPlan[] = [
    { id: '1m', name: 'Стандарт', days: 30, price: 199, description: '30 дней доступа на 5 устройств' },
    { id: '3m', name: 'Оптимальный', days: 90, price: 499, description: '90 дней скоростного VLESS туннеля', popular: true, badge: 'Выгодно' },
    { id: '6m', name: 'Премиум', days: 180, price: 899, description: '180 дней максимальной приватности', badge: '-25%' },
    { id: '12m', name: 'Ультра Год', days: 365, price: 1599, description: '365 дней без ограничений и блокировок', badge: 'Макс выгода' },
  ];

  const [invitedFriends, setInvitedFriends] = useState([
    { name: 'Дмитрий', username: 'dmitry_v', date: '02.09.2026', rewarded: true },
    { name: 'Елена', username: 'elena_art', date: '04.09.2026', rewarded: true },
  ]);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    if (onEventLog) onEventLog(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const copyText = (text: string, label: string) => {
    navigator.clipboard?.writeText(text);
    showToast(`✓ ${label} скопирован в буфер!`);
  };

  const handleActivateTrial = () => {
    if (user.freeTrialUsed) {
      showToast('❌ Пробный период уже использован!');
      return;
    }
    const newEnd = new Date(Date.now() + 3 * 86400000).toISOString();
    setUser(prev => ({ ...prev, freeTrialUsed: true }));
    setActiveSub({
      id: 999,
      planName: 'Пробный период (3 дня)',
      startDate: new Date().toISOString(),
      endDate: newEnd,
      daysLeft: 3,
      vlessLink: `vless://trial-${Math.random().toString(36).substring(2, 10)}@nl-ams-01.nexusvpn.network:443?type=tcp&security=reality&pbk=7K3sW2y9vXqL9ZmN4jR1Pq8tY3uW0eA2bC5dE7fG8hI&fp=chrome&sni=dl.google.com&sid=a4b8c9d0&spx=%2F&flow=xtls-rprx-vision#NexusVPN-Trial`,
      subscriptionUrl: `https://marzban.nexusvpn.network/sub/nexus_${user.username}_trial`,
      usedTrafficBytes: 50000000,
      trafficLimitBytes: 5 * 1024 * 1024 * 1024,
    });
    setTimeLeft({ days: 3, hours: 0, minutes: 0, seconds: 0 });
    showToast('🎁 Пробный VLESS Reality туннель активирован на 3 дня!');
    setActiveTab('home');
  };

  const handlePurchasePlan = (plan: SubscriptionPlan) => {
    if (user.balance < plan.price) {
      setTopUpAmount(plan.price);
      setShowTopUpModal(true);
      showToast(`Недостаточно средств. Пополните баланс на ${plan.price - user.balance} ₽`);
      return;
    }

    setUser(prev => ({ ...prev, balance: prev.balance - plan.price }));
    const newDays = (activeSub?.daysLeft || 0) + plan.days;
    const newEnd = new Date(Date.now() + newDays * 86400000).toISOString();

    setActiveSub({
      id: Math.floor(Math.random() * 10000),
      planName: plan.name,
      startDate: new Date().toISOString(),
      endDate: newEnd,
      daysLeft: newDays,
      vlessLink: `vless://${Math.random().toString(36).substring(2, 10)}-${Math.random().toString(36).substring(2, 8)}@${currentServer.id}-01.nexusvpn.network:443?type=tcp&security=reality&pbk=7K3sW2y9vXqL9ZmN4jR1Pq8tY3uW0eA2bC5dE7fG8hI&fp=chrome&sni=dl.google.com&sid=a4b8c9d0&spx=%2F&flow=xtls-rprx-vision#NexusVPN-${currentServer.country}`,
      subscriptionUrl: `https://marzban.nexusvpn.network/sub/nexus_${user.username}_sub`,
      usedTrafficBytes: activeSub?.usedTrafficBytes || 0,
      trafficLimitBytes: 0,
    });
    setTimeLeft({ days: newDays, hours: 12, minutes: 30, seconds: 0 });
    showToast(`✓ Тариф «${plan.name}» успешно активирован на ${plan.days} дней!`);
    setActiveTab('home');
  };

  const handleTopUpConfirm = () => {
    setUser(prev => ({ ...prev, balance: prev.balance + topUpAmount }));
    setShowTopUpModal(false);
    showToast(`✓ Баланс пополнен на +${topUpAmount} ₽!`);
  };

  const simulateFriendPurchase = () => {
    const friendName = `Гость_${Math.floor(Math.random() * 900 + 100)}`;
    setInvitedFriends(prev => [
      { name: friendName, username: `friend_${Math.floor(Math.random() * 1000)}`, date: 'Сегодня', rewarded: true },
      ...prev
    ]);
    setUser(prev => ({ ...prev, balance: prev.balance + 100.0 }));
    showToast(`🎉 Реферальный бонус! Друг ${friendName} оформил подписку (+100.00 ₽)`);
  };

  return (
    <div className="w-full min-h-screen bg-[#07090e] text-slate-100 flex flex-col font-sans select-none antialiased">
      <div className="w-full max-w-md mx-auto min-h-screen flex flex-col bg-[#07090e] relative border-x border-slate-900/60 shadow-2xl">
      
      {/* Header Profile Bar */}
      <div className="bg-[#0b0f19] px-4 py-3 border-b border-slate-800 flex items-center justify-between sticky top-0 z-30">
        <div className="flex items-center space-x-2.5">
          <div className="relative">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-500 to-cyan-500 p-[2px]">
              <div className="w-full h-full bg-slate-900 rounded-[10px] flex items-center justify-center font-bold text-xs text-emerald-400">
                {user.firstName.charAt(0)}
              </div>
            </div>
            <span className={`absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-[#07090e] ${activeSub ? 'bg-emerald-400' : 'bg-slate-500'}`} />
          </div>
          <div>
            <div className="flex items-center space-x-1">
              <span className="font-semibold text-xs text-white">{user.firstName}</span>
              <span className="text-[9px] px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-400 font-mono border border-emerald-800/60">VLESS</span>
            </div>
            <div className="text-[10px] text-slate-400 font-mono">@{user.username}</div>
          </div>
        </div>

        {/* Balance & Top up */}
        <div className="flex items-center space-x-1.5">
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl px-2.5 py-1 text-right">
            <div className="text-[8px] uppercase tracking-wider text-slate-400">Баланс</div>
            <div className="text-xs font-bold text-white font-mono">{user.balance.toFixed(2)} ₽</div>
          </div>
          <button
            id="topup-header-btn"
            onClick={() => setShowTopUpModal(true)}
            className="w-7 h-7 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/40 rounded-xl flex items-center justify-center transition-all active:scale-90"
            title="Пополнить баланс"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Mini App Content Area (Scrollable) */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 pb-20 custom-scrollbar">

        {/* TAB: HOME */}
        {activeTab === 'home' && (
          <div className="space-y-3">
            
            {/* Active Subscription Card */}
            <div className="relative overflow-hidden rounded-2xl bg-gradient-to-b from-slate-900 via-slate-900/90 to-[#0b0f19] border border-slate-800 p-4 shadow-xl">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <span className={`text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-md ${activeSub ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-slate-800 text-slate-400'}`}>
                    {activeSub ? '● Подписка активна' : '○ Нет подписки'}
                  </span>
                  <h3 className="text-base font-bold text-white mt-1.5">{activeSub ? activeSub.planName : 'Не подключен'}</h3>
                </div>
                <div className="w-9 h-9 rounded-xl bg-slate-800/80 border border-slate-700 flex items-center justify-center text-emerald-400">
                  <Shield className="w-5 h-5" />
                </div>
              </div>

              {activeSub ? (
                <div className="space-y-3">
                  {/* Timer grid */}
                  <div className="grid grid-cols-4 gap-1.5 py-1">
                    <div className="bg-black/40 border border-slate-800/80 rounded-xl p-1.5 text-center">
                      <div className="text-base font-bold font-mono text-emerald-400">{String(timeLeft.days).padStart(2, '0')}</div>
                      <div className="text-[9px] uppercase text-slate-500">Дней</div>
                    </div>
                    <div className="bg-black/40 border border-slate-800/80 rounded-xl p-1.5 text-center">
                      <div className="text-base font-bold font-mono text-emerald-400">{String(timeLeft.hours).padStart(2, '0')}</div>
                      <div className="text-[9px] uppercase text-slate-500">Часов</div>
                    </div>
                    <div className="bg-black/40 border border-slate-800/80 rounded-xl p-1.5 text-center">
                      <div className="text-base font-bold font-mono text-emerald-400">{String(timeLeft.minutes).padStart(2, '0')}</div>
                      <div className="text-[9px] uppercase text-slate-500">Мин</div>
                    </div>
                    <div className="bg-black/40 border border-slate-800/80 rounded-xl p-1.5 text-center">
                      <div className="text-base font-bold font-mono text-emerald-400">{String(timeLeft.seconds).padStart(2, '0')}</div>
                      <div className="text-[9px] uppercase text-slate-500">Сек</div>
                    </div>
                  </div>

                  {/* Traffic & Speed bar */}
                  <div className="bg-black/30 border border-slate-800/60 rounded-xl px-3 py-2 flex justify-between items-center text-[10px]">
                    <span className="text-slate-400">Трафик: <strong className="text-white font-mono">1.42 GB / ∞</strong></span>
                    <span className="text-emerald-400 font-mono">1 Гбит/с Reality</span>
                  </div>
                </div>
              ) : (
                <div className="py-2 space-y-2 text-xs">
                  <p className="text-slate-300">Защитите ваш интернет от блокировок с помощью маскировки Reality под обычный HTTPS трафик.</p>
                  {!user.freeTrialUsed && (
                    <button
                      id="trial-activate-btn"
                      onClick={handleActivateTrial}
                      className="w-full bg-emerald-500 hover:bg-emerald-400 text-black font-bold py-2 rounded-xl text-xs shadow-md transition-all active:scale-95"
                    >
                      🎁 Активировать 3 дня бесплатно
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Current Server Badge */}
            <div className="bg-[#0b0f19] border border-slate-800 rounded-2xl p-3 flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <span className="text-2xl">{currentServer.flag}</span>
                <div>
                  <div className="text-xs font-bold text-white flex items-center space-x-1.5">
                    <span>{currentServer.country}</span>
                    <span className="text-[10px] text-slate-400 font-mono">({currentServer.city})</span>
                  </div>
                  <div className="text-[10px] text-emerald-400 font-mono flex items-center space-x-1 mt-0.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                    <span>{currentServer.pingMs} ms</span>
                    <span className="text-slate-600">•</span>
                    <span className="text-slate-400">XTLS Vision</span>
                  </div>
                </div>
              </div>
              <button
                id="switch-server-btn"
                onClick={() => setActiveTab('servers')}
                className="text-[11px] text-emerald-400 bg-emerald-950/40 border border-emerald-800/50 px-2.5 py-1 rounded-lg"
              >
                Сменить
              </button>
            </div>

            {/* VLESS Reality Key Box */}
            {activeSub && (
              <div className="bg-[#0b0f19] border border-slate-800 rounded-2xl p-3.5 space-y-2.5">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="font-semibold text-slate-300 uppercase tracking-wider">Ключ VLESS Reality</span>
                  <span className="text-[9px] text-emerald-400 bg-emerald-950 px-1.5 py-0.5 rounded border border-emerald-900">TCP + Reality</span>
                </div>

                <div className="bg-black/50 border border-slate-800/80 rounded-xl p-2.5 font-mono text-[10px] text-slate-300 break-all select-all flex items-center justify-between">
                  <span className="truncate mr-2">{activeSub.vlessLink.substring(0, 36)}...</span>
                  <button onClick={() => copyText(activeSub.vlessLink, 'Ключ VLESS')} className="text-emerald-400 hover:text-emerald-300">
                    <Copy className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-2 pt-1">
                  <button
                    id="copy-vless-btn"
                    onClick={() => copyText(activeSub.vlessLink, 'Ключ VLESS Reality')}
                    className="bg-emerald-500 hover:bg-emerald-400 text-black font-bold py-2 px-2.5 rounded-xl text-[11px] flex items-center justify-center space-x-1.5 shadow-md active:scale-95 transition-all"
                  >
                    <Copy className="w-3.5 h-3.5" />
                    <span>Скопировать</span>
                  </button>

                  <button
                    id="qr-modal-btn"
                    onClick={() => setShowQrModal(true)}
                    className="bg-slate-800 hover:bg-slate-700 text-white font-medium py-2 px-2.5 rounded-xl text-[11px] border border-slate-700 flex items-center justify-center space-x-1.5 active:scale-95 transition-all"
                  >
                    <QrCode className="w-3.5 h-3.5 text-cyan-400" />
                    <span>QR-код</span>
                  </button>
                </div>

                <button
                  id="copy-sub-url-btn"
                  onClick={() => copyText(activeSub.subscriptionUrl, 'Ссылка на подписку')}
                  className="w-full text-[10px] text-slate-400 hover:text-slate-200 py-1 flex items-center justify-center space-x-1 border border-dashed border-slate-800 rounded-lg mt-1"
                >
                  <ExternalLink className="w-3 h-3" />
                  <span>Скопировать ссылку автообновления серверов</span>
                </button>
              </div>
            )}

            {/* Client quick launcher */}
            <div className="bg-[#0b0f19] border border-slate-800 rounded-2xl p-3 space-y-2">
              <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Подключение за 1 минуту:</div>
              <div className="grid grid-cols-3 gap-1.5">
                <button onClick={() => { setActiveTab('guide'); setGuidePlatform('happ'); }} className="bg-slate-900 border border-slate-800 p-2 rounded-xl text-center hover:border-slate-700">
                  <div className="text-sm mb-0.5">⚡</div>
                  <div className="font-bold text-[11px] text-white">Happ</div>
                  <div className="text-[8px] text-slate-500">iOS / Android</div>
                </button>
                <button onClick={() => { setActiveTab('guide'); setGuidePlatform('amnezia'); }} className="bg-slate-900 border border-slate-800 p-2 rounded-xl text-center hover:border-slate-700">
                  <div className="text-sm mb-0.5">🛡️</div>
                  <div className="font-bold text-[11px] text-white">Amnezia</div>
                  <div className="text-[8px] text-slate-500">ПК / Мобильные</div>
                </button>
                <button onClick={() => { setActiveTab('guide'); setGuidePlatform('v2rayng'); }} className="bg-slate-900 border border-slate-800 p-2 rounded-xl text-center hover:border-slate-700">
                  <div className="text-sm mb-0.5">🤖</div>
                  <div className="font-bold text-[11px] text-white">v2rayNG</div>
                  <div className="text-[8px] text-slate-500">Android</div>
                </button>
              </div>
            </div>

          </div>
        )}

        {/* TAB: SERVERS */}
        {activeTab === 'servers' && (
          <div className="space-y-2.5">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">Серверные узлы</h3>
                <p className="text-[10px] text-slate-400">Канал 10 Гбит/с, нулевое логирование</p>
              </div>
              <span className="text-[10px] text-emerald-400 font-mono">Reality VLESS</span>
            </div>

            <div className="space-y-2">
              {servers.map(server => (
                <div
                  key={server.id}
                  onClick={() => {
                    setCurrentServer(server);
                    showToast(`Локация изменена на ${server.country}`);
                  }}
                  className={`border rounded-2xl p-3 flex items-center justify-between cursor-pointer transition-all ${currentServer.id === server.id ? 'border-emerald-500 bg-emerald-950/20' : 'border-slate-800 bg-[#0b0f19] hover:border-slate-700'}`}
                >
                  <div className="flex items-center space-x-2.5">
                    <span className="text-2xl">{server.flag}</span>
                    <div>
                      <div className="flex items-center space-x-1.5">
                        <span className="font-bold text-xs text-white">{server.country}</span>
                        <span className="text-[10px] text-slate-400 font-mono">{server.city}</span>
                      </div>
                      <div className="text-[9px] text-slate-400 flex items-center space-x-1 mt-0.5">
                        <span className="text-emerald-400 font-medium">{server.protocol.split('(')[0]}</span>
                        <span className="text-slate-600">•</span>
                        <span>Загрузка {server.loadPercent}%</span>
                      </div>
                    </div>
                  </div>

                  <div className="text-right">
                    <div className={`text-xs font-mono font-bold ${server.pingMs < 35 ? 'text-emerald-400' : 'text-amber-400'}`}>
                      {server.pingMs} ms
                    </div>
                    <div className="text-[8px] uppercase text-slate-500">
                      {currentServer.id === server.id ? 'Выбран' : 'Подключить'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB: PLANS */}
        {activeTab === 'plans' && (
          <div className="space-y-3">
            <div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">Тарифные планы</h3>
              <p className="text-[10px] text-slate-400">Безлимитный трафик на всех тарифах</p>
            </div>

            <div className="space-y-2.5">
              {plans.map(plan => (
                <div
                  key={plan.id}
                  className={`relative bg-[#0b0f19] border rounded-2xl p-3.5 transition-all ${plan.popular ? 'border-emerald-500/80 bg-gradient-to-b from-emerald-950/20 to-[#0b0f19]' : 'border-slate-800'}`}
                >
                  {plan.badge && (
                    <span className="absolute -top-2 right-3 text-[9px] font-bold uppercase tracking-wider bg-gradient-to-r from-emerald-500 to-cyan-500 text-black px-2 py-0.2 rounded-full">
                      {plan.badge}
                    </span>
                  )}
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-bold text-sm text-white">{plan.name}</h4>
                      <p className="text-[10px] text-slate-400 mt-0.5">{plan.description}</p>
                      <div className="text-[9px] text-emerald-400 mt-1">✓ До 5 устройств одновременно</div>
                    </div>
                    <div className="text-right">
                      <div className="text-base font-extrabold font-mono text-white">{plan.price} ₽</div>
                      <div className="text-[9px] text-slate-400">{Math.round(plan.price / (plan.days / 30))} ₽/мес</div>
                    </div>
                  </div>

                  <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between">
                    <span className="text-[10px] text-slate-400">Срок: {plan.days} дней</span>
                    <button
                      onClick={() => handlePurchasePlan(plan)}
                      className="bg-emerald-500 hover:bg-emerald-400 text-black font-bold px-3.5 py-1.5 rounded-xl text-xs shadow-md transition-all active:scale-95"
                    >
                      Оформить подписку
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB: REFERRALS */}
        {activeTab === 'referrals' && (
          <div className="space-y-3">
            <div className="bg-gradient-to-tr from-cyan-950/30 via-[#0b0f19] to-emerald-950/30 border border-cyan-800/40 rounded-2xl p-3.5 space-y-2.5">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-xl bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                  <Users className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="font-bold text-xs text-white">100 ₽ + 15% с каждой покупки</h4>
                  <p className="text-[10px] text-slate-400">Деньги начисляются на баланс мгновенно</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-1">
                <div className="bg-black/40 border border-slate-800 rounded-xl p-2 text-center">
                  <div className="text-base font-bold font-mono text-white">{invitedFriends.length}</div>
                  <div className="text-[9px] text-slate-400">Приглашено</div>
                </div>
                <div className="bg-black/40 border border-slate-800 rounded-xl p-2 text-center">
                  <div className="text-base font-bold font-mono text-emerald-400">{(invitedFriends.length * 100).toFixed(2)} ₽</div>
                  <div className="text-[9px] text-slate-400">Заработано</div>
                </div>
              </div>
            </div>

            {/* Ref link */}
            <div className="bg-[#0b0f19] border border-slate-800 rounded-2xl p-3 space-y-2">
              <div className="text-[10px] font-semibold text-slate-300 uppercase tracking-wider">Ваша ссылка:</div>
              <div className="bg-black/50 border border-slate-800 rounded-xl p-2 font-mono text-[10px] text-slate-300 truncate select-all flex items-center justify-between">
                <span className="truncate mr-2">{user.refLink}</span>
                <button onClick={() => copyText(user.refLink, 'Реферальная ссылка')} className="text-emerald-400 hover:text-emerald-300 text-[10px] font-bold">
                  Копировать
                </button>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-1">
                <button
                  onClick={() => copyText(user.refLink, 'Реферальная ссылка')}
                  className="bg-cyan-600 hover:bg-cyan-500 text-white font-bold py-2 rounded-xl text-[10px] flex items-center justify-center space-x-1"
                >
                  <Share2 className="w-3 h-3" />
                  <span>Поделиться</span>
                </button>
                <button
                  onClick={simulateFriendPurchase}
                  className="bg-slate-800 hover:bg-slate-700 text-emerald-400 font-bold py-2 rounded-xl text-[10px] border border-emerald-900/60 flex items-center justify-center space-x-1"
                  title="Симулировать регистрацию и покупку друга для теста начисления бонуса"
                >
                  <Sparkles className="w-3 h-3" />
                  <span>Тест бонуса (+100₽)</span>
                </button>
              </div>
            </div>

            {/* List */}
            <div className="bg-[#0b0f19] border border-slate-800 rounded-2xl p-3 space-y-2">
              <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Приглашенные друзья:</div>
              <div className="space-y-1.5 max-h-36 overflow-y-auto custom-scrollbar">
                {invitedFriends.map((f, i) => (
                  <div key={i} className="bg-black/30 border border-slate-800/80 rounded-xl p-2 flex items-center justify-between text-[11px]">
                    <div>
                      <div className="font-semibold text-white">{f.name}</div>
                      <div className="text-[9px] text-slate-400 font-mono">@{f.username}</div>
                    </div>
                    <div className="text-right">
                      <span className="text-[9px] text-emerald-400 font-mono">+100.00 ₽</span>
                      <div className="text-[8px] text-slate-500">{f.date}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB: GUIDE */}
        {activeTab === 'guide' && (
          <div className="space-y-3">
            <div className="flex space-x-1.5">
              <button
                onClick={() => setGuidePlatform('happ')}
                className={`flex-1 py-1.5 rounded-xl text-[10px] font-semibold ${guidePlatform === 'happ' ? 'bg-emerald-500 text-black' : 'bg-slate-900 text-slate-400 border border-slate-800'}`}
              >
                Happ (iOS/Android)
              </button>
              <button
                onClick={() => setGuidePlatform('amnezia')}
                className={`flex-1 py-1.5 rounded-xl text-[10px] font-semibold ${guidePlatform === 'amnezia' ? 'bg-emerald-500 text-black' : 'bg-slate-900 text-slate-400 border border-slate-800'}`}
              >
                Amnezia (ПК)
              </button>
              <button
                onClick={() => setGuidePlatform('v2rayng')}
                className={`flex-1 py-1.5 rounded-xl text-[10px] font-semibold ${guidePlatform === 'v2rayng' ? 'bg-emerald-500 text-black' : 'bg-slate-900 text-slate-400 border border-slate-800'}`}
              >
                v2rayNG
              </button>
            </div>

            <div className="bg-[#0b0f19] border border-slate-800 rounded-2xl p-3.5 text-[11px] text-slate-300 space-y-2">
              {guidePlatform === 'happ' && (
                <>
                  <div className="font-bold text-white flex items-center space-x-1 text-xs">
                    <span className="text-emerald-400">⚡</span>
                    <span>Happ Proxy Utility (Рекомендуем)</span>
                  </div>
                  <ol className="list-decimal list-inside space-y-1.5 text-slate-300">
                    <li>Установите <strong>Happ</strong> из App Store или Google Play.</li>
                    <li>Скопируйте ваш VLESS ключ из вкладки <strong>«Главная»</strong>.</li>
                    <li>В приложении Happ нажмите <strong>«+»</strong> вверху экрана.</li>
                    <li>Выберите <strong>«Add from Clipboard»</strong> и нажмите <strong>«Connect»</strong>.</li>
                  </ol>
                </>
              )}

              {guidePlatform === 'amnezia' && (
                <>
                  <div className="font-bold text-white flex items-center space-x-1 text-xs">
                    <span className="text-emerald-400">🛡️</span>
                    <span>AmneziaVPN (Windows / Mac / Linux)</span>
                  </div>
                  <ol className="list-decimal list-inside space-y-1.5 text-slate-300">
                    <li>Скачайте AmneziaVPN с сайта <strong>amnezia.org</strong>.</li>
                    <li>Скопируйте VLESS Reality ключ.</li>
                    <li>В Amnezia выберите <strong>«У меня есть данные для подключения»</strong> → <strong>«Вставить ключ»</strong>.</li>
                    <li>Нажмите круглую кнопку <strong>«Подключиться»</strong>.</li>
                  </ol>
                </>
              )}

              {guidePlatform === 'v2rayng' && (
                <>
                  <div className="font-bold text-white flex items-center space-x-1 text-xs">
                    <span className="text-emerald-400">🤖</span>
                    <span>v2rayNG (Android)</span>
                  </div>
                  <ol className="list-decimal list-inside space-y-1.5 text-slate-300">
                    <li>Установите v2rayNG из Google Play или GitHub.</li>
                    <li>Скопируйте VLESS ключ или нажмите «Показать QR-код».</li>
                    <li>В v2rayNG нажмите значок <strong>«+»</strong> сверху → <strong>«Импортировать из буфера»</strong>.</li>
                    <li>Нажмите круглую кнопку подключения в правом нижнем углу.</li>
                  </ol>
                </>
              )}
            </div>
          </div>
        )}

      </div>

      {/* Bottom Navigation Bar */}
      <div className="bg-[#0b0f19]/95 backdrop-blur-xl border-t border-slate-800/80 px-2 py-2 flex justify-around items-center z-20">
        <button
          onClick={() => setActiveTab('home')}
          className={`flex flex-col items-center py-1 ${activeTab === 'home' ? 'text-emerald-400 font-semibold' : 'text-slate-400 hover:text-slate-200'}`}
        >
          <Shield className="w-4 h-4" />
          <span className="text-[9px] mt-0.5">Главная</span>
        </button>

        <button
          onClick={() => setActiveTab('servers')}
          className={`flex flex-col items-center py-1 ${activeTab === 'servers' ? 'text-emerald-400 font-semibold' : 'text-slate-400 hover:text-slate-200'}`}
        >
          <Globe2 className="w-4 h-4" />
          <span className="text-[9px] mt-0.5">Серверы</span>
        </button>

        <button
          onClick={() => setActiveTab('plans')}
          className={`flex flex-col items-center py-1 ${activeTab === 'plans' ? 'text-emerald-400 font-semibold' : 'text-slate-400 hover:text-slate-200'}`}
        >
          <CreditCard className="w-4 h-4" />
          <span className="text-[9px] mt-0.5">Тарифы</span>
        </button>

        <button
          onClick={() => setActiveTab('referrals')}
          className={`flex flex-col items-center py-1 ${activeTab === 'referrals' ? 'text-emerald-400 font-semibold' : 'text-slate-400 hover:text-slate-200'}`}
        >
          <Users className="w-4 h-4" />
          <span className="text-[9px] mt-0.5">Рефералы</span>
        </button>

        <button
          onClick={() => setActiveTab('guide')}
          className={`flex flex-col items-center py-1 ${activeTab === 'guide' ? 'text-emerald-400 font-semibold' : 'text-slate-400 hover:text-slate-200'}`}
        >
          <Smartphone className="w-4 h-4" />
          <span className="text-[9px] mt-0.5">Помощь</span>
        </button>
      </div>

      {/* MODAL: QR CODE */}
      {showQrModal && (
        <div className="absolute inset-0 bg-black/85 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#0b0f19] border border-slate-700 rounded-3xl p-5 max-w-[280px] w-full text-center space-y-3 shadow-2xl">
            <h4 className="font-bold text-white text-sm">QR-код VLESS Reality</h4>
            <div className="bg-white p-3 rounded-2xl inline-block shadow-inner">
              {/* Render visual QR mockup */}
              <div className="w-40 h-40 bg-white flex flex-col items-center justify-center border-2 border-black p-1">
                <div className="grid grid-cols-5 gap-1 w-full h-full p-2">
                  <div className="bg-black rounded-xs col-span-2 row-span-2"></div>
                  <div className="bg-black rounded-xs"></div>
                  <div className="bg-black rounded-xs col-span-2 row-span-2"></div>
                  <div className="bg-black rounded-xs"></div>
                  <div className="bg-black rounded-xs"></div>
                  <div className="bg-black rounded-xs"></div>
                  <div className="bg-black rounded-xs col-span-2 row-span-2"></div>
                  <div className="bg-black rounded-xs"></div>
                  <div className="bg-black rounded-xs"></div>
                </div>
              </div>
            </div>
            <p className="text-[10px] text-slate-400">Отсканируйте камерой в Happ, Amnezia или v2rayNG</p>
            <button
              onClick={() => setShowQrModal(false)}
              className="w-full bg-slate-800 hover:bg-slate-700 text-white font-bold py-2 rounded-xl text-xs"
            >
              Закрыть
            </button>
          </div>
        </div>
      )}

      {/* MODAL: TOP UP BALANCE */}
      {showTopUpModal && (
        <div className="absolute inset-0 bg-black/85 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#0b0f19] border border-slate-700 rounded-3xl p-5 max-w-[310px] w-full space-y-3 shadow-2xl">
            <div className="flex justify-between items-center">
              <h4 className="font-bold text-white text-sm">Пополнение баланса</h4>
              <button onClick={() => setShowTopUpModal(false)} className="text-slate-400 hover:text-white text-xs">✕</button>
            </div>
            <p className="text-[10px] text-slate-400">Выберите сумму для быстрого пополнения (карты РФ, СБП, крипта):</p>
            <div className="grid grid-cols-3 gap-1.5">
              {[199, 499, 899].map(amt => (
                <button
                  key={amt}
                  onClick={() => setTopUpAmount(amt)}
                  className={`border py-1.5 rounded-xl text-center text-xs font-mono font-bold ${topUpAmount === amt ? 'border-emerald-500 bg-emerald-950/40 text-emerald-400' : 'border-slate-800 bg-slate-900 text-slate-300'}`}
                >
                  {amt} ₽
                </button>
              ))}
            </div>
            <div>
              <label className="text-[9px] text-slate-400 block mb-1">Сумма пополнения (руб):</label>
              <input
                type="number"
                value={topUpAmount}
                onChange={e => setTopUpAmount(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-2.5 py-1.5 text-white font-mono text-xs focus:outline-none focus:border-emerald-500"
              />
            </div>
            <button
              onClick={handleTopUpConfirm}
              className="w-full bg-emerald-500 hover:bg-emerald-400 text-black font-bold py-2.5 rounded-xl text-xs shadow-md transition-all active:scale-95"
            >
              Оплатить {topUpAmount} ₽
            </button>
          </div>
        </div>
      )}

      {/* TOAST ALERT */}
      {toastMessage && (
        <div className="absolute bottom-16 left-3 right-3 z-50 bg-slate-900/95 border border-emerald-500/60 text-white px-3 py-2 rounded-xl text-[11px] shadow-2xl flex items-center justify-between animate-fade-in">
          <div className="flex items-center space-x-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
            <span className="truncate">{toastMessage}</span>
          </div>
          <button onClick={() => setToastMessage(null)} className="text-slate-400 hover:text-white text-xs ml-2">✕</button>
        </div>
      )}

      </div>
    </div>
  );
};
