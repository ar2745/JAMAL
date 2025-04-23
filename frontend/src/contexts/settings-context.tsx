import { createContext, ReactNode, useContext, useEffect, useState } from 'react';
import { useTheme } from '../components/theme-provider';

type Theme = 'light' | 'dark' | 'system';
type FontSize = 'small' | 'medium' | 'large';
type MessageDisplay = 'compact' | 'normal' | 'comfortable';
type TimestampFormat = '12h' | '24h';

interface Settings {
  theme: Theme;
  fontSize: FontSize;
  messageDisplay: MessageDisplay;
  timestampFormat: TimestampFormat;
}

interface SettingsContextType {
  settings: Settings;
  updateSetting: <K extends keyof Settings>(key: K, value: Settings[K]) => void;
}

const defaultSettings: Settings = {
  theme: 'system',
  fontSize: 'medium',
  messageDisplay: 'normal',
  timestampFormat: '12h',
};

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const { setTheme } = useTheme();
  const [settings, setSettings] = useState<Settings>(() => {
    const savedSettings = localStorage.getItem('settings');
    return savedSettings ? JSON.parse(savedSettings) : defaultSettings;
  });

  // Sync theme with ThemeProvider
  useEffect(() => {
    if (settings.theme !== 'system') {
      setTheme(settings.theme);
    }
  }, [settings.theme, setTheme]);

  // Apply font size class to root element
  useEffect(() => {
    const root = document.documentElement;
    // Remove all font size classes
    root.classList.remove('font-size-small', 'font-size-medium', 'font-size-large');
    // Add the current font size class
    root.classList.add(`font-size-${settings.fontSize}`);
  }, [settings.fontSize]);

  // Apply message display class to root element
  useEffect(() => {
    const root = document.documentElement;
    // Remove all message display classes
    root.classList.remove('message-display-compact', 'message-display-normal', 'message-display-comfortable');
    // Add the current message display class
    root.classList.add(`message-display-${settings.messageDisplay}`);
  }, [settings.messageDisplay]);

  const updateSetting = <K extends keyof Settings>(key: K, value: Settings[K]) => {
    setSettings((prev) => {
      const newSettings = { ...prev, [key]: value };
      localStorage.setItem('settings', JSON.stringify(newSettings));
      return newSettings;
    });
  };

  return (
    <SettingsContext.Provider value={{ settings, updateSetting }}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
} 