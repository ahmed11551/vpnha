import { useEffect, useCallback } from 'react';

declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        ready: () => void;
        expand: () => void;
        close: () => void;
        initData: string;
        initDataUnsafe?: {
          user?: {
            id: number;
            first_name: string;
            last_name?: string;
            username?: string;
            language_code?: string;
          };
          start_param?: string;
        };
        themeParams?: Record<string, string>;
        colorScheme?: 'light' | 'dark';
        isExpanded?: boolean;
        viewportHeight?: number;
        viewportStableHeight?: number;
        headerColor?: string;
        backgroundColor?: string;
        setHeaderColor?: (color: string) => void;
        setBackgroundColor?: (color: string) => void;
        openLink?: (url: string) => void;
        openTelegramLink?: (url: string) => void;
        HapticFeedback?: {
          impactOccurred: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft') => void;
          notificationOccurred: (type: 'error' | 'success' | 'warning') => void;
          selectionChanged: () => void;
        };
      };
    };
  }
}

export function useTelegram() {
  const tg = typeof window !== 'undefined' ? window.Telegram?.WebApp : undefined;

  useEffect(() => {
    if (tg) {
      tg.ready();
      tg.expand();
      try {
        tg.setHeaderColor?.('#07090e');
        tg.setBackgroundColor?.('#07090e');
      } catch {
        // Safe ignore
      }
    }
  }, [tg]);

  const hapticImpact = useCallback((style: 'light' | 'medium' | 'heavy' = 'light') => {
    try {
      tg?.HapticFeedback?.impactOccurred(style);
    } catch {
      // Ignore if not in Telegram
    }
  }, [tg]);

  const hapticNotification = useCallback((type: 'success' | 'warning' | 'error' = 'success') => {
    try {
      tg?.HapticFeedback?.notificationOccurred(type);
    } catch {
      // Ignore if not in Telegram
    }
  }, [tg]);

  const hapticSelection = useCallback(() => {
    try {
      tg?.HapticFeedback?.selectionChanged();
    } catch {
      // Ignore
    }
  }, [tg]);

  return {
    tg,
    user: tg?.initDataUnsafe?.user,
    startParam: tg?.initDataUnsafe?.start_param,
    initData: tg?.initData || '',
    hapticImpact,
    hapticNotification,
    hapticSelection,
    isAvailable: Boolean(tg?.initData),
  };
}
