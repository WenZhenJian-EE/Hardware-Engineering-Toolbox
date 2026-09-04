export type Language = 'zh' | 'en';

export interface ModuleTranslation {
  name: string;
  description: string;
  category?: string;
}

export interface I18nContextValue {
  lang: Language;
  setLang: (lang: Language) => void;
  t: (key: string, fallbackOrParams?: string | Record<string, string | number>) => string;
  getModuleInfo: (moduleId: string, defaultName?: string, defaultDesc?: string) => { name: string; description: string };
  getCategoryName: (cat: string) => string;
}
