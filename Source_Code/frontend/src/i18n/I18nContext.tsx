import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import type { Language, I18nContextValue } from './types';
import { zhDict, zhModules } from './zh';
import { enDict, enModules } from './en';

const I18nContext = createContext<I18nContextValue | null>(null);

const STORAGE_KEY = 'app_language';

const CATEGORY_MAP: Record<string, { zh: string; en: string }> = {
  '全部': { zh: '全部', en: 'All' },
  'All': { zh: '全部', en: 'All' },
  '⚡ 协同电源设计 (Co-Design)': { zh: '⚡ 协同电源设计 (Co-Design)', en: '⚡ Power Co-Design' },
  '⚡ Power Co-Design': { zh: '⚡ 协同电源设计 (Co-Design)', en: '⚡ Power Co-Design' },
  '🧲 磁件与拓扑基础': { zh: '🧲 磁件与拓扑基础', en: '🧲 Magnetics & Basics' },
  '🧲 Magnetics & Basics': { zh: '🧲 磁件与拓扑基础', en: '🧲 Magnetics & Basics' },
  '🔥 功率器件与热力': { zh: '🔥 功率器件与热力', en: '🔥 Power & Thermal' },
  '🔥 Power & Thermal': { zh: '🔥 功率器件与热力', en: '🔥 Power & Thermal' },
  '📈 环路控制与信号': { zh: '📈 环路控制与信号', en: '📈 Loop & Signals' },
  '📈 Loop & Signals': { zh: '📈 环路控制与信号', en: '📈 Loop & Signals' },
  '🛡️ 无源元器件与安规': { zh: '🛡️ 无源元器件与安规', en: '🛡️ Passives & Safety' },
  '🛡️ Passives & Safety': { zh: '🛡️ 无源元器件与安规', en: '🛡️ Passives & Safety' }
};

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [lang, setLangState] = useState<Language>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === 'en') return saved;
      if (saved === 'zh') {
        localStorage.setItem(STORAGE_KEY, 'en');
      }
    } catch (e) {
      console.warn('Failed to read language preference from localStorage:', e);
    }
    return 'en';
  });

  const setLang = useCallback((newLang: Language) => {
    setLangState(newLang);
    try {
      localStorage.setItem(STORAGE_KEY, newLang);
    } catch (e) {
      console.warn('Failed to save language preference to localStorage:', e);
    }
  }, []);

  const t = useCallback((key: string, fallbackOrParams?: string | Record<string, string | number>): string => {
    let text: string | undefined;
    let params: Record<string, string | number> | undefined;

    if (typeof fallbackOrParams === 'object') {
      params = fallbackOrParams;
    }

    if (lang === 'en') {
      text = enDict[key] ?? zhDict[key];
    } else {
      text = zhDict[key] ?? enDict[key];
    }

    if (!text && typeof fallbackOrParams === 'string') {
      text = fallbackOrParams;
    }

    if (!text) {
      text = key;
    }

    if (params) {
      text = text.replace(/\{(\w+)\}/g, (_, k) => String(params![k] ?? {}));
    }

    return text;
  }, [lang]);

  const getModuleInfo = useCallback((moduleId: string, defaultName?: string, defaultDesc?: string) => {
    if (lang === 'en') {
      const mod = enModules[moduleId];
      if (mod) {
        return { name: mod.name, description: mod.description };
      }
    } else {
      const mod = zhModules[moduleId];
      if (mod) {
        return { name: mod.name, description: mod.description };
      }
    }
    return {
      name: defaultName ?? moduleId,
      description: defaultDesc ?? ''
    };
  }, [lang]);

  const getCategoryName = useCallback((cat: string): string => {
    const entry = CATEGORY_MAP[cat];
    if (entry) {
      return lang === 'en' ? entry.en : entry.zh;
    }
    return cat;
  }, [lang]);

  const value = useMemo<I18nContextValue>(() => ({
    lang,
    setLang,
    t,
    getModuleInfo,
    getCategoryName
  }), [lang, setLang, t, getModuleInfo, getCategoryName]);

  return (
    <I18nContext.Provider value={value}>
      {children}
    </I18nContext.Provider>
  );
};

export const useTranslation = (): I18nContextValue => {
  const context = useContext(I18nContext);
  if (!context) {
    return {
      lang: 'en',
      setLang: () => {},
      t: (k, fb) => (typeof fb === 'string' ? fb : k),
      getModuleInfo: (id, name, desc) => ({ name: name ?? id, description: desc ?? '' }),
      getCategoryName: (c) => c
    };
  }
  return context;
};
