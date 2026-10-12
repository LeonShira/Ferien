import React from 'react';
import {Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {BOX, DISPLAY, FONT, card, enter, fit, progress, str, useShort} from '../util';
import type {Visual} from '../types';

type P = {v: Visual; durationInFrames: number};

// Myth card gets stamped and struck out, then the fact slides in.
export const MythFactScene: React.FC<P> = ({v, durationInFrames}) => {
  const frame = useCurrentFrame();
  const {theme, fps} = useShort();
  const flip = Math.round(durationInFrames * 0.42);
  const myth = str(v.myth), fact = str(v.fact);
  const m = enter(frame, fps, 0, 12);
  const strike = progress(frame, flip - 14, flip - 4);
  const f = enter(frame, fps, flip, 12);
  const stamp = (label: string, color: string, s: number) => (
    <div style={{position: 'absolute', top: -38, left: 40, padding: '6px 26px', background: color, color: '#fff',
      fontFamily: DISPLAY, fontWeight: 900, fontSize: 52, letterSpacing: 4, border: `5px solid ${theme.ink}`,
      borderRadius: 14, transform: `rotate(-6deg) scale(${s})`}}>{label}</div>
  );
  return (
    <div style={{position: 'absolute', ...BOX, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 70}}>
      <div style={{position: 'relative', ...card(theme, {padding: '64px 48px 48px'}), opacity: interpolate(f, [0, 1], [1, 0.45]),
        transform: `scale(${0.85 + 0.15 * m}) translateY(${(1 - m) * 60}px)`}}>
        {stamp(str(v.mythLabel, 'MYTH'), theme.bad, enter(frame, fps, 6, 8))}
        <div style={{position: 'relative', fontFamily: DISPLAY, fontWeight: 800, fontSize: fit(myth, 60, 38, 50), color: theme.ink, lineHeight: 1.2}}>
          {myth}
          <div style={{position: 'absolute', left: -10, top: '50%', height: 10, width: `${strike * 104}%`, background: theme.bad,
            borderRadius: 5, transform: 'rotate(-3deg)'}} />
        </div>
      </div>
      <div style={{position: 'relative', ...card(theme, {padding: '64px 48px 48px', background: theme.accent}), opacity: f,
        transform: `translateX(${(1 - f) * 600}px) rotate(${(1 - f) * 8}deg)`}}>
        {stamp(str(v.factLabel, 'FACT'), theme.good, f)}
        <div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: fit(fact, 62, 38, 50), color: theme.accentInk, lineHeight: 1.2}}>{fact}</div>
      </div>
    </div>
  );
};

type Side = {title: string; emoji?: string; rows?: string[]; highlight?: boolean};

// Two options side by side; the better one lifts at the end.
export const SplitCompareScene: React.FC<P> = ({v, durationInFrames}) => {
  const frame = useCurrentFrame();
  const {theme, fps} = useShort();
  const sides = [v.left as Side, v.right as Side].filter(Boolean);
  const rowsN = Math.max(...sides.map((s) => s.rows?.length ?? 0), 0);
  const step = Math.max(6, (durationInFrames * 0.55) / Math.max(1, rowsN));
  const lift = progress(frame, durationInFrames * 0.7, durationInFrames * 0.8);
  return (
    <div style={{position: 'absolute', ...BOX, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 34}}>
      {str(v.title) && <div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: fit(str(v.title), 68, 44, 24), color: theme.ink,
        textAlign: 'center', opacity: enter(frame, fps)}}>{str(v.title)}</div>}
      <div style={{display: 'flex', gap: 34, alignItems: 'stretch'}}>
        {sides.map((s, i) => {
          const e = enter(frame, fps, i * 5, 13);
          const hi = s.highlight ? lift : 0;
          return (
            <div key={i} style={{flex: 1, ...card(theme, {padding: '36px 28px', background: hi > 0.5 ? theme.accent : theme.card}),
              transform: `translateX(${(1 - e) * (i ? 500 : -500)}px) translateY(${-hi * 24}px) scale(${1 + hi * 0.04})`,
              display: 'flex', flexDirection: 'column', gap: 22}}>
              {s.emoji && <div style={{fontSize: 110, textAlign: 'center'}}>{s.emoji}</div>}
              <div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: fit(s.title, 56, 34, 12), color: theme.ink, textAlign: 'center'}}>{s.title}</div>
              {(s.rows ?? []).map((r, j) => (
                <div key={j} style={{fontFamily: FONT, fontWeight: 700, fontSize: fit(r, 38, 26, 18), color: theme.ink,
                  opacity: progress(frame, 10 + j * step, 18 + j * step), borderTop: `4px dashed ${theme.ink}33`, paddingTop: 16}}>{r}</div>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
};

type Event = {year: string | number; label: string};

// Vertical timeline drawn top to bottom.
export const TimelineScene: React.FC<P> = ({v, durationInFrames}) => {
  const frame = useCurrentFrame();
  const {theme, fps} = useShort();
  const events = (v.events as Event[]) ?? [];
  const step = Math.max(8, (durationInFrames * 0.75) / Math.max(1, events.length));
  const line = progress(frame, 0, step * events.length);
  return (
    <div style={{position: 'absolute', ...BOX, display: 'flex', flexDirection: 'column', justifyContent: 'center'}}>
      {str(v.title) && <div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: fit(str(v.title), 66, 44, 24), color: theme.ink,
        marginBottom: 30, opacity: enter(frame, fps)}}>{str(v.title)}</div>}
      <div style={{position: 'relative', paddingLeft: 90, display: 'flex', flexDirection: 'column', gap: 34}}>
        <div style={{position: 'absolute', left: 34, top: 10, width: 10, height: `${line * 100}%`, background: theme.ink, borderRadius: 5}} />
        {events.map((e, i) => {
          const s = enter(frame, fps, i * step, 12);
          return (
            <div key={i} style={{position: 'relative', opacity: s, transform: `translateX(${(1 - s) * 80}px)`}}>
              <div style={{position: 'absolute', left: -78, top: 12, width: 46, height: 46, borderRadius: 23, background: theme.accent,
                border: `6px solid ${theme.ink}`}} />
              <div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: 60, color: theme.ink, lineHeight: 1}}>{e.year}</div>
              <div style={{fontFamily: FONT, fontWeight: 700, fontSize: fit(e.label, 42, 30, 34), color: theme.muted, marginTop: 6}}>{e.label}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// A still (e.g. a generated illustration) in a paper frame with slow Ken Burns motion.
export const ImageScene: React.FC<P> = ({v, durationInFrames}) => {
  const frame = useCurrentFrame();
  const {theme, fps} = useShort();
  const src = str(v.src);
  const t = frame / Math.max(1, durationInFrames);
  const motion = str(v.motion, 'zoom_in');
  const scale = motion === 'zoom_out' ? 1.14 - 0.14 * t : 1 + 0.14 * t;
  const pan = motion === 'pan' ? (t - 0.5) * 60 : 0;
  const e = enter(frame, fps, 0, 14);
  if (!src) return null;
  return (
    <div style={{position: 'absolute', ...BOX, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 30}}>
      <div style={{...card(theme, {padding: 16, width: 820, height: 820, overflow: 'hidden'}),
        transform: `rotate(${(1 - e) * -4 + 1}deg) scale(${0.9 + 0.1 * e})`}}>
        <div style={{width: '100%', height: '100%', overflow: 'hidden', borderRadius: 20}}>
          <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover',
            transform: `scale(${scale}) translateX(${pan}px)`}} />
        </div>
      </div>
      {str(v.label) && <div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: fit(str(v.label), 56, 36, 26), color: theme.ink,
        background: theme.accent, border: `5px solid ${theme.ink}`, borderRadius: 16, padding: '6px 24px',
        opacity: progress(frame, 10, 20)}}>{str(v.label)}</div>}
    </div>
  );
};
