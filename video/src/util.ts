import {Easing, interpolate, spring} from 'remotion';
import {createContext, useContext} from 'react';
import type {Theme} from './types';

export const FONT = "'Inter', 'Noto Color Emoji', sans-serif";
export const DISPLAY = "'Inter Display', 'Inter', 'Noto Color Emoji', sans-serif";

// Content box for scene visuals: inside the TikTok/Shorts safe zone, above the captions.
export const BOX = {left: 70, top: 320, width: 940, height: 860};

export type Ctx = {theme: Theme; locale: string; fps: number};
export const ShortContext = createContext<Ctx>({
  theme: {
    paper: '#F3EDE2', card: '#FFFDF8', ink: '#14213D', muted: '#5B6478',
    accent: '#FFD84D', accentInk: '#14213D', good: '#2A9D8F', bad: '#E63946',
  },
  locale: 'en-US',
  fps: 30,
});
export const useShort = () => useContext(ShortContext);

export const enter = (frame: number, fps: number, delay = 0, damping = 14) =>
  spring({frame: frame - delay, fps, config: {damping, mass: 0.8, stiffness: 140}});

export const progress = (frame: number, start: number, end: number, ease = Easing.out(Easing.cubic)) =>
  interpolate(frame, [start, end], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});

export const fmt = (value: number, locale: string, decimals = 0, prefix = '', suffix = '') => {
  const s = new Intl.NumberFormat(locale, {minimumFractionDigits: decimals, maximumFractionDigits: decimals}).format(value);
  return `${prefix}${s}${suffix}`;
};

// Shrink type for longer strings so nothing overflows the box.
export const fit = (text: string, max: number, min: number, comfortableChars: number) => {
  const n = Math.max(1, (text ?? '').length);
  if (n <= comfortableChars) return max;
  return Math.max(min, Math.round(max * Math.sqrt(comfortableChars / n)));
};

export const card = (theme: Theme, extra: React.CSSProperties = {}): React.CSSProperties => ({
  background: theme.card,
  border: `6px solid ${theme.ink}`,
  borderRadius: 32,
  boxShadow: `12px 12px 0 ${theme.ink}`,
  ...extra,
});

export const num = (v: unknown, fallback = 0) => (typeof v === 'number' && isFinite(v) ? v : fallback);
export const str = (v: unknown, fallback = '') => (typeof v === 'string' ? v : fallback);
