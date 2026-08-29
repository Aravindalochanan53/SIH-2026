import { create } from 'zustand';

export const useAppStore = create((set, get) => ({
  // Navigation & Shell
  activeTab: 'home',
  setActiveTab: (tab) => set({ activeTab: tab }),

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
