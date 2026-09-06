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
  description: string;
  popular?: boolean;
  badge?: string;
}

export interface UserAccount {
  id: number;
  telegramId: number;
  username: string;
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
  vlessLink: string;
  subscriptionUrl: string;
  usedTrafficBytes: number;
  trafficLimitBytes: number;
}

export interface CodeFile {
  name: string;
  filename: string;
  category: 'core' | 'bot' | 'database' | 'frontend' | 'deployment';
  language: string;
  description: string;
  code: string;
}
