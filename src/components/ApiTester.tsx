import React, { useState } from 'react';
import { Terminal, Play, CheckCircle2, AlertCircle, RefreshCw, Key, Shield, UserCheck, Send } from 'lucide-react';

export const ApiTester: React.FC = () => {
  const [activeEndpoint, setActiveEndpoint] = useState<string>('auth');
  const [responseOutput, setResponseOutput] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [statusCode, setStatusCode] = useState<number | null>(null);

  // Test parameters
  const [testTgId, setTestTgId] = useState<number>(749102384);
  const [testUsername, setTestUsername] = useState<string>('alex_cyber');
  const [testRefCode, setTestRefCode] = useState<string>('cyber77');
  const [testPlanId, setTestPlanId] = useState<string>('3m');

  const runTest = async () => {
    setIsLoading(true);
    setResponseOutput(null);

    // Simulate network delay and execute endpoint response
    setTimeout(() => {
      setIsLoading(false);
      setStatusCode(200);

      switch (activeEndpoint) {
        case 'auth':
          setResponseOutput(JSON.stringify({
            success: true,
            user: {
              id: 1,
              telegram_id: testTgId,
              username: testUsername,
              first_name: "Алексей",
              balance: 550.00,
              ref_code: testRefCode,
              ref_link: `https://t.me/asbvpn_bot?start=ref_${testRefCode}`,
              free_trial_used: false,
              marzban_username: `tg_${testTgId}`
            },
            active_subscription: {
              plan_name: "Оптимальный 3 Месяца",
              days_left: 87,
              subscription_url: `https://marzban.nexusvpn.network/sub/nexus_${testUsername}`,
              vless_link: "vless://9e14a27c-3f94-4d2b-b6d8-7711ab3c9902@nl-ams-01.nexusvpn.network:443?type=tcp&security=reality&pbk=7K3sW2y9vXqL9ZmN4jR1Pq8tY3uW0eA2bC5dE7fG8hI&fp=chrome&sni=dl.google.com&sid=a4b8c9d0&spx=%2F&flow=xtls-rprx-vision#NexusVPN-NL"
            },
            referral_stats: {
              total_invited: 2,
              total_earned: 200.00,
              bonus_per_ref: 100.00,
              commission_percent: 15.0
            }
          }, null, 2));
          break;

        case 'trial':
          setResponseOutput(JSON.stringify({
            success: true,
            message: "Пробный период на 3 дня успешно активирован в Marzban Xray!",
            subscription: {
              id: 42,
              plan_name: "Пробный период 3 дня",
              end_date: new Date(Date.now() + 3 * 86400000).toISOString(),
              vless_link: `vless://c5d2b781-9b1e-45fa-92cf-e317bb892c90@nl-ams-01.nexusvpn.network:443?type=tcp&security=reality&pbk=7K3sW2y9vXqL9ZmN4jR1Pq8tY3uW0eA2bC5dE7fG8hI&fp=chrome&sni=dl.google.com&sid=a4b8c9d0&spx=%2F&flow=xtls-rprx-vision#NexusVPN-Trial-3Days`,
              subscription_url: `https://marzban.nexusvpn.network/sub/nexus_trial_${testTgId}`
            }
          }, null, 2));
          break;

        case 'purchase':
          setResponseOutput(JSON.stringify({
            success: true,
            message: `Подписка успешно активирована на ${testPlanId === '1m' ? '30' : testPlanId === '3m' ? '90' : '180'} дней!`,
            new_balance: 51.00,
            end_date: new Date(Date.now() + 90 * 86400000).toISOString(),
            subscription_url: `https://marzban.nexusvpn.network/sub/nexus_${testUsername}`,
            vless_link: `vless://e18b8f21-72da-4b05-b31c-34582f0bc8a1@de-fra-01.nexusvpn.network:443?type=tcp&security=reality&pbk=7K3sW2y9vXqL9ZmN4jR1Pq8tY3uW0eA2bC5dE7fG8hI&fp=chrome&sni=dl.google.com&sid=a4b8c9d0&spx=%2F&flow=xtls-rprx-vision#NexusVPN-Premium`,
            referral_bonus_triggered: true,
            referral_payout_rub: 100.00
          }, null, 2));
          break;

        case 'marzban':
          setResponseOutput(JSON.stringify({
            marzban_auth: "OK (Bearer JWT cached)",
            user_exists: true,
            username: `tg_${testTgId}`,
            status: "active",
            used_traffic: 1420500000,
            data_limit: 0,
            expire: Math.floor(Date.now() / 1000) + 90 * 86400,
            proxies: {
              vless: {
                id: "9e14a27c-3f94-4d2b-b6d8-7711ab3c9902",
                flow: "xtls-rprx-vision"
              }
            },
            inbounds: {
              vless: ["VLESS TCP REALITY", "VLESS gRPC REALITY"]
            }
          }, null, 2));
          break;

        default:
          break;
      }
    }, 400);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl space-y-6">
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2 text-emerald-400 text-xs font-bold uppercase tracking-wider">
            <Terminal className="w-4 h-4" />
            <span>Интерактивное тестирование API & Marzban</span>
          </div>
          <h2 className="text-xl font-bold text-white mt-1">Тестовая консоль бэкенда</h2>
          <p className="text-sm text-slate-400 mt-0.5">
            Проверка логики аутентификации Telegram WebApp, выдачи триала, покупок и синхронизации с Marzban.
          </p>
        </div>
      </div>

      {/* Endpoints Selector */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {[
          { id: 'auth', name: 'POST /api/auth/telegram-webapp', desc: 'HMAC WebApp валидация' },
          { id: 'trial', name: 'POST /api/subscription/trial', desc: 'Выдача 3-х дней триала' },
          { id: 'purchase', name: 'POST /api/subscription/purchase', desc: 'Покупка + реферальный бонус' },
          { id: 'marzban', name: 'GET /api/user/{username}', desc: 'Marzban Xray состояние' },
        ].map(ep => (
          <button
            key={ep.id}
            onClick={() => {
              setActiveEndpoint(ep.id);
              setResponseOutput(null);
            }}
            className={`p-3 rounded-2xl text-left border transition-all ${activeEndpoint === ep.id ? 'bg-emerald-500/15 border-emerald-500/60 text-white' : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-300'}`}
          >
            <div className="font-mono text-xs font-bold truncate text-emerald-400">{ep.name}</div>
            <div className="text-[11px] text-slate-400 mt-1">{ep.desc}</div>
          </button>
        ))}
      </div>

      {/* Parameter Inputs & Execute */}
      <div className="bg-slate-950/80 border border-slate-800 rounded-2xl p-4 space-y-4">
        <div className="text-xs font-bold text-white uppercase tracking-wider">Входные параметры запроса:</div>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div>
            <label className="text-[11px] text-slate-400 block mb-1">Telegram ID</label>
            <input
              type="number"
              value={testTgId}
              onChange={e => setTestTgId(Number(e.target.value))}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-white font-mono focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="text-[11px] text-slate-400 block mb-1">Username</label>
            <input
              type="text"
              value={testUsername}
              onChange={e => setTestUsername(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-white font-mono focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="text-[11px] text-slate-400 block mb-1">Реферальный код</label>
            <input
              type="text"
              value={testRefCode}
              onChange={e => setTestRefCode(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-white font-mono focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="text-[11px] text-slate-400 block mb-1">Тарифный план</label>
            <select
              value={testPlanId}
              onChange={e => setTestPlanId(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-white font-mono focus:border-emerald-500 focus:outline-none"
            >
              <option value="1m">1 Месяц (199 ₽)</option>
              <option value="3m">3 Месяца (499 ₽)</option>
              <option value="6m">6 Месяцев (899 ₽)</option>
              <option value="12m">12 Месяцев (1599 ₽)</option>
            </select>
          </div>
        </div>

        <button
          onClick={runTest}
          disabled={isLoading}
          className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold px-5 py-2.5 rounded-xl text-xs flex items-center space-x-2 shadow-md transition-all active:scale-95"
        >
          {isLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current" />}
          <span>Отправить запрос к эндпоинту</span>
        </button>
      </div>

      {/* Response Box */}
      {responseOutput && (
        <div className="bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden">
          <div className="bg-slate-900 px-4 py-2 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              <span className="text-xs font-mono font-bold text-white">HTTP {statusCode} OK</span>
            </div>
            <span className="text-[10px] font-mono text-slate-400">application/json</span>
          </div>
          <pre className="p-4 text-xs font-mono text-emerald-300 overflow-x-auto max-h-72 leading-relaxed">
            {responseOutput}
          </pre>
        </div>
      )}

    </div>
  );
};
