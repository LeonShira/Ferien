import type React from 'react';
import type {Visual} from '../types';

// Bespoke, one-off scenes written for a specific episode live in this folder
// (e.g. src/custom/CardSwipe.tsx) and are registered here by name. An episode
// uses one with `visual: {type: custom, component: CardSwipe, ...params}`.
export const custom: Record<string, React.FC<{v: Visual; durationInFrames: number}>> = {};
