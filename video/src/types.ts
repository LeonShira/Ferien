// Props contract between the Python pipeline (shorts/render.py) and the composition.
// Times are in seconds on the master timeline; the composition converts to frames.

export type Caption = {start: number; end: number; text: string};

export type Visual = {type: string; [key: string]: unknown};

export type SceneSpec = {
  start: number;
  duration: number;
  visual: Visual;
  captions: Caption[];
};

export type Theme = {
  paper: string;
  card: string;
  ink: string;
  muted: string;
  accent: string;
  accentInk: string;
  good: string;
  bad: string;
};

export type ShortProps = {
  fps: number;
  width: number;
  height: number;
  duration: number;
  locale: string;
  theme: Theme;
  seriesLabel: string;
  hookText: string;
  disclaimer: string;
  cta: string;
  scenes: SceneSpec[];
};
