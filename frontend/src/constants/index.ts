import { Preset } from "../store/types";

export const PRESETS: Record<string, Preset> = {
    ycstartups: {
        label: "YC Startups",
        desc: "5,000+ startup names",
        file: "/datasets/ycstartups.txt",
        data: null,
    },
    names: {
        label: "Baby Names",
        desc: "2,000+ popular names",
        file: "/datasets/names.txt",
        data: null,
    },
    dinos: {
        label: "Dinosaurs",
        desc: "1,500+ species names",
        file: "/datasets/dinos.txt",
        data: null,
    },
    words: {
        label: "English Words",
        desc: "10,000 common words",
        file: "/datasets/words.txt",
        data: null,
    },
};

export const WIRES: [string, string][] = [
    // ['dataset', 'tokenizer'],
    // ['tokenizer', 'config'],
    // ['config', 'training'],
    // ['training', 'metrics'],
    // ['training', 'generate'],
    ["reference", "compress_config"],
    ["compress_config", "compress"],
    ["compress", "extracting"],
    ["extracting", "script_analysis"],
    ["extracting", "audio_analysis"],
];

export const SESSION_KEYS = {
    NODE_POSITIONS: "hf-node-positions",
    ZOOM: "hf-zoom",
};
