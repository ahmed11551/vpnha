import React from 'react';
import { Shield, Bot, Server, Database, Globe, Smartphone, ArrowRight, ArrowDown, Key, CheckCircle2, Lock } from 'lucide-react';

export const ArchitectureView: React.FC = () => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl space-y-6">
      
      {/* Header */}
      <div>
        <div className="flex items-center space-x-2 text-emerald-400 text-xs font-bold uppercase tracking-wider">
          <Shield className="w-4 h-4" />
          <span>Архитектура коммерческой экосистемы</span>
        </div>
        <h2 className="text-xl font-bold text-white mt-1">NexusVPN: Единая платформа на базе Marzban</h2>
        <p className="text-sm text-slate-400 mt-1">
          Telegram Mini App, aiogram 3 бот и веб-сервис работают на единой базе данных SQLAlchemy и общаются с Marzban по REST API.
        </p>
      </div>

      {/* Interactive Flow Diagram */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        
        {/* Step 1: Clients */}
        <div className="bg-slate-950/80 border border-slate-800 rounded-2xl p-4 flex flex-col justify-between">
          <div>
            <div className="w-10 h-10 rounded-xl bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400 mb-3">
              <Smartphone className="w-5 h-5" />
            </div>
            <span className="text-[10px] font-mono text-cyan-400 uppercase font-bold">Уровень интерфейса</span>
            <h3 className="font-bold text-white text-base mt-1">Клиенты экосистемы</h3>
            <ul className="text-xs text-slate-400 mt-2 space-y-1.5">
              <li className="flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
                <span>Telegram Mini App (Alpine.js)</span>
              </li>
              <li className="flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
                <span>Telegram Bot (aiogram 3.x)</span>
              </li>
              <li className="flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
                <span>Приложения Happ, Amnezia, v2rayNG</span>
              </li>
            </ul>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-500 flex items-center justify-between">
            <span>HMAC initData</span>
            <ArrowRight className="w-3.5 h-3.5 text-cyan-400" />
          </div>
        </div>

        {/* Step 2: FastAPI Gateway */}
        <div className="bg-slate-950/80 border border-emerald-500/50 rounded-2xl p-4 flex flex-col justify-between relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/10 rounded-full blur-2xl"></div>
          <div>
            <div className="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 mb-3">
              <Server className="w-5 h-5" />
            </div>
            <span className="text-[10px] font-mono text-emerald-400 uppercase font-bold">API Gateway</span>
            <h3 className="font-bold text-white text-base mt-1">FastAPI Backend</h3>
            <ul className="text-xs text-slate-400 mt-2 space-y-1.5">
              <li className="flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                <span>Валидация HMAC-SHA256 подписи</span>
              </li>
              <li className="flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                <span>Выдача 3-дневного триала</span>
              </li>
              <li className="flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                <span>Покупка и реферальный бонус</span>
              </li>
            </ul>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-emerald-400 flex items-center justify-between font-mono">
            <span>REST API</span>
            <ArrowRight className="w-3.5 h-3.5 text-emerald-400" />
          </div>
        </div>

        {/* Step 3: Marzban API Client */}
        <div className="bg-slate-950/80 border border-slate-800 rounded-2xl p-4 flex flex-col justify-between">
          <div>
            <div className="w-10 h-10 rounded-xl bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400 mb-3">
              <Key className="w-5 h-5" />
            </div>
            <span className="text-[10px] font-mono text-indigo-400 uppercase font-bold">VPN Управление</span>
            <h3 className="font-bold text-white text-base mt-1">Marzban API</h3>
            <ul className="text-xs text-slate-400 mt-2 space-y-1.5">
              <li className="flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>
                <span>Кэширование JWT-токена админа</span>
              </li>
              <li className="flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>
                <span>Генерация UUID и Reality ключей</span>
              </li>
              <li className="flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>
                <span>Продление и блокировка (/api/user)</span>
              </li>
            </ul>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-500 flex items-center justify-between">
            <span>gRPC / Xray</span>
            <ArrowRight className="w-3.5 h-3.5 text-indigo-400" />
          </div>
        </div>

        {/* Step 4: Xray Core VPN */}
        <div className="bg-slate-950/80 border border-slate-800 rounded-2xl p-4 flex flex-col justify-between">
          <div>
            <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 mb-3">
              <Shield className="w-5 h-5" />
            </div>
            <span className="text-[10px] font-mono text-amber-400 uppercase font-bold">Сетевое ядро</span>
            <h3 className="font-bold text-white text-base mt-1">Xray VLESS + Reality</h3>
            <ul className="text-xs text-slate-400 mt-2 space-y-1.5">
              <li className="flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                <span>XTLS-Vision маскировка</span>
              </li>
              <li className="flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                <span>Неотличим от TLS 1.3 к dl.google.com</span>
              </li>
              <li className="flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                <span>Устойчив к блокировкам DPI</span>
              </li>
            </ul>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-emerald-400 font-bold flex items-center justify-between">
            <span>10 Гбит/с трафик</span>
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          </div>
        </div>

      </div>

      {/* Feature Matrix */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
        <div className="bg-slate-950/50 border border-slate-800 rounded-2xl p-4">
          <h4 className="font-bold text-white text-sm flex items-center space-x-2">
            <Lock className="w-4 h-4 text-emerald-400" />
            <span>Защита от мошенничества</span>
          </h4>
          <p className="text-xs text-slate-400 mt-1.5">
            Флаг <code>free_trial_used</code> в PostgreSQL/SQLite фиксирует использование триала. Повторная выдача невозможна даже при переустановке приложения.
          </p>
        </div>

        <div className="bg-slate-950/50 border border-slate-800 rounded-2xl p-4">
          <h4 className="font-bold text-white text-sm flex items-center space-x-2">
            <Bot className="w-4 h-4 text-cyan-400" />
            <span>Сквозная реферальная цепочка</span>
          </h4>
          <p className="text-xs text-slate-400 mt-1.5">
            Хвост <code>/start ref_xxx</code> в боте сохраняет связь между пригласившим и рефералом. Бонус (100 ₽ + 15%) автоматически падает на баланс при первой оплате.
          </p>
        </div>

        <div className="bg-slate-950/50 border border-slate-800 rounded-2xl p-4">
          <h4 className="font-bold text-white text-sm flex items-center space-x-2">
            <Globe className="w-4 h-4 text-indigo-400" />
            <span>Автоматическое обновление серверов</span>
          </h4>
          <p className="text-xs text-slate-400 mt-1.5">
            Ссылка автообновления <code>/sub/...</code> позволяет клиентам Happ и v2rayNG мгновенно подгружать новые серверы при добавлении узлов в Marzban.
          </p>
        </div>
      </div>

    </div>
  );
};
