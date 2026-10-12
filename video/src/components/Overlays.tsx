import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Caption} from '../types';
import {DISPLAY, FONT, enter, fit, progress, useShort} from '../util';

const NUMBERISH = /[\d%€$£]/;

// Warm paper with grain, a soft vignette and two slow-drifting accent shapes,
// so even a held frame keeps moving.
export const Background: React.FC = () => {
  const frame = useCurrentFrame();
  const {theme} = useShort();
  const grain = `url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.09 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>")`;
  const a = Math.sin(frame / 90) * 40, b = Math.cos(frame / 110) * 50;
  return (
    <AbsoluteFill style={{background: theme.paper, overflow: 'hidden'}}>
      <div style={{position: 'absolute', width: 900, height: 900, borderRadius: 450, background: theme.accent, opacity: 0.18,
        left: -380 + a, top: 120 + b}} />
      <div style={{position: 'absolute', width: 640, height: 640, borderRadius: 120, background: theme.ink, opacity: 0.05,
        right: -260 - b, bottom: 380 + a, transform: `rotate(${frame / 12}deg)`}} />
      <AbsoluteFill style={{backgroundImage: grain, opacity: 0.9}} />
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, transparent 55%, rgba(20,33,61,0.16) 100%)'}} />
    </AbsoluteFill>
  );
};

// Caption chunks pop in under the visual; numbers are highlighted.
export const Captions: React.FC<{captions: Caption[]}> = ({captions}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {theme} = useShort();
  const t = frame / fps;
  const cur = captions.find((c) => t >= c.start && t < c.end);
  if (!cur) return null;
  const local = Math.round((t - cur.start) * fps);
  const s = enter(local, fps, 0, 10);
  const outline = [...Array(16)].map((_, i) => {
    const a = (i / 16) * Math.PI * 2;
    return `${(Math.cos(a) * 6).toFixed(1)}px ${(Math.sin(a) * 6).toFixed(1)}px 0 ${theme.card}`;
  }).join(', ');
  return (
    <div style={{position: 'absolute', left: 60, right: 60, top: 1215, height: 240, display: 'flex', alignItems: 'flex-start',
      justifyContent: 'center', textAlign: 'center'}}>
      <div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: fit(cur.text, 86, 62, 16), lineHeight: 1.1, color: theme.ink,
        textShadow: outline, transform: `scale(${0.86 + 0.14 * s})`, letterSpacing: -1}}>
        {cur.text.split(' ').map((w, i) => (
          <span key={i} style={{color: NUMBERISH.test(w) ? theme.bad : theme.ink}}>{w} </span>
        ))}
      </div>
    </div>
  );
};

// Accent banner that slams in for the first seconds.
export const Banner: React.FC<{text: string; from: number; to: number; tilt?: number}> = ({text, from, to, tilt = -2}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {theme} = useShort();
  if (!text || frame < from * fps || frame >= to * fps) return null;
  const local = frame - from * fps;
  const s = enter(local, fps, 0, 9);
  const out = interpolate(frame, [to * fps - 6, to * fps], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <div style={{position: 'absolute', left: 0, right: 0, top: 300, display: 'flex', justifyContent: 'center', opacity: out}}>
      <div style={{maxWidth: 940, background: theme.accent, color: theme.accentInk, border: `6px solid ${theme.ink}`,
        boxShadow: `10px 10px 0 ${theme.ink}`, borderRadius: 22, padding: '14px 34px', fontFamily: DISPLAY, fontWeight: 900,
        fontSize: fit(text, 72, 46, 22), textTransform: 'uppercase', textAlign: 'center', lineHeight: 1.05,
        transform: `rotate(${tilt}deg) scale(${0.5 + 0.5 * s})`}}>{text}</div>
    </div>
  );
};

export const TopLine: React.FC<{disclaimer: string; seriesLabel: string; duration: number}> = ({disclaimer, seriesLabel, duration}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {theme} = useShort();
  const t = frame / fps;
  const showDisclaimer = t < 4 || t > duration - 3;
  const label = showDisclaimer ? disclaimer : seriesLabel;
  const fade = showDisclaimer
    ? Math.min(progress(frame, 0, 6), t < 4 ? 1 - progress(frame, 3.6 * fps, 4 * fps) : progress(frame, (duration - 3) * fps, (duration - 2.7) * fps))
    : Math.min(progress(frame, 4 * fps, 4.4 * fps), 1 - progress(frame, (duration - 3.4) * fps, (duration - 3) * fps));
  if (!label) return null;
  return (
    <div style={{position: 'absolute', left: 0, right: 0, top: 218, display: 'flex', justifyContent: 'center', opacity: fade}}>
      <div style={{fontFamily: FONT, fontWeight: showDisclaimer ? 600 : 800, fontSize: showDisclaimer ? 30 : 32,
        color: showDisclaimer ? theme.muted : theme.ink, background: showDisclaimer ? 'transparent' : theme.card,
        border: showDisclaimer ? 'none' : `4px solid ${theme.ink}`, borderRadius: 40, padding: showDisclaimer ? 0 : '6px 22px',
        letterSpacing: showDisclaimer ? 0 : 2, textTransform: showDisclaimer ? 'none' : 'uppercase'}}>{label}</div>
    </div>
  );
};

export const ProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const {theme} = useShort();
  return (
    <div style={{position: 'absolute', left: 0, bottom: 0, height: 14, width: `${(frame / durationInFrames) * 100}%`,
      background: theme.accent, borderTop: `3px solid ${theme.ink}`}} />
  );
};
