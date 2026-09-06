export interface ServerLocation {
  id: string;
  country: string;
  countryCode: string;
  city: string;
  flag: string;
  pingMs: number;
  protocol: string;
  status: 'online' | 'degraded' | 'maintenance';
  loadPercent: number;
}

export interface SubscriptionPlan {
  id: string;
  name: string;
  days: number;
  price: number;
  popular?: boolean;
  badge?: string | null;
  price_per_month?: number;
}

export interface UserAccount {
  id: number;
  telegramId: number;
  username?: string;
  firstName: string;
  balance: number;
  refCode: string;
  refLink: string;
  freeTrialUsed: boolean;
  marzbanUsername: string;
  invitedBy?: number | null;
}

export interface ActiveSubscription {
  id: number;
  planName: string;
  startDate: string;
  endDate: string;
  daysLeft: number;
  timeLeftSeconds?: number;
  vlessLink?: string;
  subscriptionUrl?: string;
  usedTrafficBytes: number;
  trafficLimitBytes: number;
  isActive: boolean;
}

export interface ReferralStats {
  refCode: string;
  refLink: string;
  invitedCount: number;
  totalEarnedRub: number;
  commissionPercent: number;
  fixedBonusRub: number;
}

export interface PaymentItem {
  order_id: string;
  amount: number;
  currency: string;
  gateway: string;
  status: 'pending' | 'paid' | 'expired' | 'failed';
  plan_id?: string | null;
  created_at: string;
  paid_at?: string | null;
}

export interface PromoCodeResult {
  valid: boolean;
  code: string;
  discount_percent: number;
  bonus_days: number;
  bonus_rub: number;
  message: string;
  new_balance?: number;
}

export interface CodeFile {
  name: string;
  filename: string;
  category: string;
  language: string;
  description: string;
  code: string;
  path?: string;
}
