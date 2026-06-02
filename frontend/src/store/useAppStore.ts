import { create } from 'zustand';
import { DatasetInfo, ModelConfig, RunHistoryItem, LossData } from './types';
import { PRESETS } from '../constants';

interface AppState {
  dataset: DatasetInfo | null;
  selectedPreset: string;
  config: ModelConfig;
  training: boolean;
  modelReady: boolean;
  lossHistory: LossData[];
  stepTimes: number[];
  currentStep: number;
  currentLoss: number;
  currentSample: string;
  stepTime: number;
  totalTime: number;
  finalSamples: string[];
  genPrompt: string;
  genTemp: number;
  genResults: string[];
  generating: boolean;
  runHistory: RunHistoryItem[];
}

interface AppActions {
  initWorker: () => void;
  destroyWorker: () => void;
  loadPreset: (key: string) => Promise<void>;
  loadCustomDataset: (text: string) => void;
  setConfig: (configOrUpdater: ModelConfig | ((c: ModelConfig) => ModelConfig)) => void;
  startTraining: () => void;
  stopTraining: () => void;
  setGenPrompt: (prompt: string) => void;
  setGenTemp: (temp: number) => void;
  doGenerate: () => void;
  saveRunHistory: () => void;
}

let workerInstance: Worker | null = null;

export const useAppStore = create<AppState & AppActions>((set, get) => ({
  // State
  dataset: null,
  selectedPreset: '',
  config: { n_embd: 16, n_head: 4, n_layer: 1, block_size: 16, num_steps: 1000, learning_rate: 0.01, seed: 42 },
  training: false,
  modelReady: false,
  lossHistory: [],
  stepTimes: [],
  currentStep: 0,
  currentLoss: 0,
  currentSample: '',
  stepTime: 0,
  totalTime: 0,
  finalSamples: [],
  genPrompt: '',
  genTemp: 0.8,
  genResults: [],
  generating: false,
  runHistory: [],

  // Actions
  initWorker: () => {
    if (workerInstance) return;
    workerInstance = new Worker('/microgpt-worker.js');
    workerInstance.onmessage = (e: MessageEvent) => {
      const { type, data } = e.data;
      if (type === 'dataset_loaded') {
        const suggested = Math.min(3000, Math.max(500, data.numDocs * 3));
        set((state) => ({
          dataset: data,
          config: { ...state.config, num_steps: Math.round(suggested / 50) * 50 }
        }));
      }
      if (type === 'step') {
        set((state) => ({
          currentStep: data.step,
          currentLoss: data.loss,
          stepTime: data.stepTimeMs,
          totalTime: data.elapsed,
          lossHistory: [...state.lossHistory, { step: data.step, loss: data.loss }],
          stepTimes: [...state.stepTimes, data.stepTimeMs],
          currentSample: data.sample || state.currentSample
        }));
      }
      if (type === 'complete') {
        set({
          training: false,
          modelReady: true,
          finalSamples: data.samples,
          totalTime: data.totalTimeMs
        });
      }
      if (type === 'stopped') {
        set({ training: false });
      }
      if (type === 'generated') {
        set({ genResults: data.samples, generating: false });
      }
    };
  },

  destroyWorker: () => {
    if (workerInstance) {
      workerInstance.terminate();
      workerInstance = null;
    }
  },

  loadPreset: async (key: string) => {
    set({ selectedPreset: key });
    if (!key || !PRESETS[key]) return;
    set({ modelReady: false, lossHistory: [], stepTimes: [], currentStep: 0, finalSamples: [], genResults: [] });

    let text = PRESETS[key].data;
    if (!text && PRESETS[key].file) {
      try {
        const res = await fetch(PRESETS[key].file);
        text = await res.text();
      } catch (err) {
        console.error('Failed to load dataset:', err);
        return;
      }
    }
    if (text && workerInstance) {
      workerInstance.postMessage({ type: 'load_dataset', data: { text } });
    }
  },

  loadCustomDataset: (text: string) => {
    set({ selectedPreset: 'custom', modelReady: false, lossHistory: [], stepTimes: [], finalSamples: [], genResults: [] });
    if (workerInstance) {
      workerInstance.postMessage({ type: 'load_dataset', data: { text } });
    }
  },

  setConfig: (configOrUpdater) => {
    set((state) => ({
      config: typeof configOrUpdater === 'function' ? configOrUpdater(state.config) : configOrUpdater
    }));
  },

  startTraining: () => {
    const state = get();
    if (!state.dataset) return;
    set({
      training: true,
      modelReady: false,
      lossHistory: [],
      stepTimes: [],
      currentStep: 0,
      currentSample: '',
      finalSamples: [],
      genResults: []
    });
    if (workerInstance) {
      workerInstance.postMessage({ type: 'init_model', data: { config: state.config } });
      setTimeout(() => workerInstance?.postMessage({ type: 'train' }), 50);
    }
  },

  stopTraining: () => {
    if (workerInstance) {
      workerInstance.postMessage({ type: 'stop' });
    }
  },

  setGenPrompt: (prompt: string) => set({ genPrompt: prompt }),
  
  setGenTemp: (temp: number) => set({ genTemp: temp }),

  doGenerate: () => {
    const state = get();
    set({ generating: true });
    if (workerInstance) {
      workerInstance.postMessage({
        type: 'generate',
        data: { prompt: state.genPrompt, temperature: state.genTemp, count: 8 }
      });
    }
  },

  saveRunHistory: () => {
    set((state) => {
      if (state.modelReady && state.lossHistory.length > 0) {
        const finalLoss = state.lossHistory[state.lossHistory.length - 1].loss;
        const newRun = {
          id: Date.now(),
          config: { ...state.config },
          finalLoss,
          totalTime: state.totalTime,
          samples: state.finalSamples.slice(0, 3)
        };
        return { runHistory: [...state.runHistory, newRun] };
      }
      return state;
    });
  }
}));
