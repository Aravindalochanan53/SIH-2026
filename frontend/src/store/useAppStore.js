import { create } from 'zustand';

const TOKEN_KEY = 'translara_auth_token';
const USER_KEY = 'translara_user';

function loadPersistedAuth() {
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    const userStr = localStorage.getItem(USER_KEY);
    if (token && userStr) {
      return { token, user: JSON.parse(userStr), isAuthenticated: true };
    }
  } catch (e) {}
  return { token: null, user: null, isAuthenticated: false };
}

const persisted = loadPersistedAuth();

export const useAppStore = create((set, get) => ({
  // Authentication
  user: persisted.user,
  token: persisted.token,
  isAuthenticated: persisted.isAuthenticated,

  login: (token, user) => {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    set({ token, user, isAuthenticated: true });
  },
  logout: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    set({ token: null, user: null, isAuthenticated: false });
  },
  setUser: (user) => {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    set({ user });
  },

  // Global Languages
  sourceLang: 'ta',
  targetLang: 'ml',
  setSourceLang: (lang) => set({ sourceLang: lang }),
  setTargetLang: (lang) => set({ targetLang: lang }),
  swapLanguages: () =>
    set((state) => ({
      sourceLang: state.targetLang,
      targetLang: state.sourceLang,
    })),

  // Global Flags
  isSimulatedOffline: false,
  setSimulatedOffline: (val) => set({ isSimulatedOffline: val }),
  capabilities: null,
  setCapabilities: (caps) => set({ capabilities: caps }),

  // Voice Translator State
  voiceState: {
    status: 'idle', // 'idle' | 'listening' | 'processing' | 'speaking' | 'error'
    transcript: 'வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?',
    translation: 'നമസ്കാരം, സുഖമാണോ?',
    detectedLang: null,
    entities: [],
    latencyMs: 1650,
    stageLatencies: { asr_ms: 620, entity_lock_ms: 18, nmt_ms: 710, unmask_ms: 10 },
    warning: null,
    isOffline: false,
  },
  setVoiceState: (updates) =>
    set((state) => ({
      voiceState: { ...state.voiceState, ...updates },
    })),

  // Video Translator State
  activeVideoJob: null,
  setActiveVideoJob: (job) => set({ activeVideoJob: job }),

  // History State
  savedTranslations: [
    {
      id: 'h_01',
      type: 'voice',
      sourceLang: 'ta',
      targetLang: 'ml',
      sourceText: 'வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?',
      targetText: 'നമസ്കാരം, സുഖമാണോ?',
      date: 'Today, 2:45 PM',
    },
    {
      id: 'h_02',
      type: 'video',
      sourceLang: 'ta',
      targetLang: 'ml',
      sourceText: 'Classroom Lesson 01 (Counting Numbers)',
      targetText: '14 seconds video with dual subtitles',
      date: 'Today, 1:15 PM',
    },
    {
      id: 'h_03',
      type: 'chat',
      sourceLang: 'ta',
      targetLang: 'ml',
      sourceText: 'Explain body parts in simple Malayalam',
      targetText: 'പ്രധാന ശരീരഭാഗങ്ങളുടെ പേരുകൾ: കണ്ണ്, ചെവി, മൂക്ക്...',
      date: 'Yesterday',
    },
  ],
  addHistoryItem: (item) =>
    set((state) => ({
      savedTranslations: [item, ...state.savedTranslations],
    })),
}));
