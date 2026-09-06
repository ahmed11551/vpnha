import { ServerLocation, SubscriptionPlan, UserAccount, ActiveSubscription, ReferralStats, PaymentItem, PromoCodeResult } from './types';

const getInitData = (): string => {
  return typeof window !== 'undefined' ? window.Telegram?.WebApp?.initData || '' : '';
};

const authHeaders = (): Record<string, string> => {
  const initData = getInitData();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (initData) {
    headers['X-Telegram-Init-Data'] = initData;
  }
  return headers;
};

export const api = {
  async authTelegram(refCode?: string) {
    const initData = getInitData();
    const res = await fetch('/api/auth/telegram', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ init_data: initData || 'dev_preview_mode', ref_code: refCode }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getPlans(): Promise<SubscriptionPlan[]> {
    const res = await fetch('/api/plans');
    if (!res.ok) throw new Error('Failed to fetch plans');
    const data = await res.json();
    return data.plans;
  },

  async getLocations(): Promise<ServerLocation[]> {
    const res = await fetch('/api/locations');
    if (!res.ok) throw new Error('Failed to fetch locations');
    const data = await res.json();
    return data.locations;
  },

  async getSubscriptionStatus(): Promise<{ has_active: boolean; subscription?: any }> {
    const res = await fetch('/api/subscription/status', {
      headers: authHeaders(),
    });
    if (!res.ok) throw new Error('Failed to fetch subscription status');
    return res.json();
  },

  async activateTrial(): Promise<{ success: boolean; vless_link?: string; subscription_url?: string; end_date?: string }> {
    const res = await fetch('/api/subscription/trial', {
      method: 'POST',
      headers: authHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Ошибка сервера' }));
      throw new Error(err.detail || 'Не удалось активировать пробный период');
    }
    return res.json();
  },

  async purchaseSubscription(planId: string, promoCode?: string) {
    const res = await fetch('/api/subscription/purchase', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ plan_id: planId, promo_code: promoCode }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Ошибка покупки' }));
      throw new Error(err.detail || 'Не удалось оформить подписку');
    }
    return res.json();
  },

  async revokeKey() {
    const res = await fetch('/api/subscription/revoke', {
      method: 'POST',
      headers: authHeaders(),
    });
    if (!res.ok) throw new Error('Не удалось перевыпустить ключ');
    return res.json();
  },

  async getReferralStats(): Promise<ReferralStats> {
    const res = await fetch('/api/referral/stats', {
      headers: authHeaders(),
    });
    if (!res.ok) throw new Error('Failed to fetch referral stats');
    return res.json();
  },

  async createPayment(amount: number, gateway: string, planId?: string, promoCode?: string) {
    const res = await fetch('/api/pay/create', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        amount,
        gateway,
        plan_id: planId,
        promo_code: promoCode,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Ошибка создания платежа' }));
      throw new Error(err.detail || 'Не удалось создать платеж');
    }
    return res.json();
  },

  async activatePromoCode(code: string): Promise<PromoCodeResult> {
    const res = await fetch('/api/promocode/activate', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ code }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Неверный промокод' }));
      throw new Error(err.detail || 'Ошибка активации промокода');
    }
    return res.json();
  },

  async getPaymentHistory(): Promise<PaymentItem[]> {
    const res = await fetch('/api/pay/history', {
      headers: authHeaders(),
    });
    if (!res.ok) return [];
    const data = await res.json();
    return data.payments || [];
  },

  async sandboxTopUp(amount: number) {
    const res = await fetch('/api/sandbox/topup', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ amount }),
    });
    if (!res.ok) throw new Error('Top up failed');
    return res.json();
  },
};
