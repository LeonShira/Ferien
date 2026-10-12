import React from 'react';
import type {Visual} from '../types';
import {custom} from '../custom';
import {BigNumberScene, EmojiScene, ListScene, QuoteScene, TitleScene} from './basic';
import {BarCompareScene, DotGridScene, LineChartScene, RingScene} from './charts';
import {ImageScene, MythFactScene, SplitCompareScene, TimelineScene} from './story';

type SceneComponent = React.FC<{v: Visual; durationInFrames: number}>;

// The scene vocabulary the script writer can use. Keep in sync with
// shorts/visuals.py (validation) and docs/VISUALS.md (reference for writers).
export const scenes: Record<string, SceneComponent> = {
  title: TitleScene,
  big_number: BigNumberScene,
  quote: QuoteScene,
  list: ListScene,
  emoji: EmojiScene,
  line_chart: LineChartScene,
  bar_compare: BarCompareScene,
  ring: RingScene,
  dot_grid: DotGridScene,
  myth_fact: MythFactScene,
  split_compare: SplitCompareScene,
  timeline: TimelineScene,
  image: ImageScene,
};

export const SceneView: React.FC<{v: Visual; durationInFrames: number}> = ({v, durationInFrames}) => {
  if (v.type === 'custom') {
    const C = custom[String(v.component)];
    if (!C) throw new Error(`custom scene ${String(v.component)} is not registered in src/custom/index.ts`);
    return <C v={v} durationInFrames={durationInFrames} />;
  }
  const C = scenes[v.type];
  if (!C) throw new Error(`unknown scene type ${v.type}`);
  return <C v={v} durationInFrames={durationInFrames} />;
};
