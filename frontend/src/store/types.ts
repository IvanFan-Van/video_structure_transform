export interface Preset {
  label: string;
  desc: string;
  file: string;
  data: string | null;
}

export interface DatasetInfo {
  numDocs: number;
  vocabSize: number;
  chars: string[];
  sampleDocs: string[];
}

export interface ModelConfig {
  n_embd: number;
  n_head: number;
  n_layer: number;
  block_size: number;
  num_steps: number;
  learning_rate: number;
  seed: number;
  [key: string]: number;
}

export interface RunHistoryItem {
  id: number;
  config: ModelConfig;
  finalLoss: number;
  totalTime: number;
  samples: string[];
}

export interface LossData {
  step: number;
  loss: number;
}

export interface Pos {
  x: number;
  y: number;
  w: number;
  h: number;
}
