import React from 'react';
import {useCurrentFrame} from 'remotion';
import {BOX, DISPLAY, FONT, card, enter, fit, fmt, num, progress, str, useShort} from '../util';
import type {Visual} from '../types';

type P = {v: Visual; durationInFrames: number};
type Series = {label: string; points: [number, number][]; color?: string};

const niceMax = (v: number) => {
  if (v <= 0) return 1;
  const p = Math.pow(10, Math.floor(Math.log10(v)));
  for (const m of [1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10]) if (m * p >= v) return m * p;
  return 10 * p;
};

const compact = (v: number, locale: string, prefix: string, suffix: string) =>
  `${prefix}${new Intl.NumberFormat(locale, {notation: 'compact', maximumFractionDigits: 1}).format(v)}${suffix}`;

// Lines draw left to right; the end value of each line counts up with it.
export const LineChartScene: React.FC<P> = ({v, durationInFrames}) => {
  const frame = useCurrentFrame();
  const {theme, locale, fps} = useShort();
  const series = ((v.series as Series[]) ?? []).filter((s) => s.points?.length > 1);
  const prefix = str(v.prefix), suffix = str(v.suffix);
  const W = BOX.width - 40, H = 560, padL = 120, padB = 70, padT = 30, padR = 40;
  const xs = series.flatMap((s) => s.points.map((p) => p[0]));
  const ys = series.flatMap((s) => s.points.map((p) => p[1]));
  const xMin = Math.min(...xs), xMax = Math.max(...xs);
  const yMax = niceMax(Math.max(...ys));
  const X = (x: number) => padL + ((x - xMin) / (xMax - xMin || 1)) * (W - padL - padR);
  const Y = (y: number) => H - padB - (y / yMax) * (H - padB - padT);
  const draw = progress(frame, 8, Math.max(30, durationInFrames * 0.75));
  const colors = [theme.ink, theme.accent, theme.good, theme.bad];
  const c = enter(frame, fps, 0, 14);
  return (
    <div style={{position: 'absolute', ...BOX, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 26}}>
      {str(v.title) && <div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: fit(str(v.title), 70, 46, 24),
        color: theme.ink, textAlign: 'center', opacity: c}}>{str(v.title)}</div>}
      <div style={{...card(theme, {padding: 20}), opacity: c, transform: `translateY(${(1 - c) * 50}px)`}}>
        <svg width={W} height={H}>
          {[0, 0.25, 0.5, 0.75, 1].map((t) => (
            <g key={t}>
              <line x1={padL} x2={W - padR} y1={Y(t * yMax)} y2={Y(t * yMax)} stroke={theme.muted} strokeOpacity={0.25} strokeWidth={2} />
              <text x={padL - 16} y={Y(t * yMax) + 10} textAnchor="end" fontFamily="Inter" fontWeight={700} fontSize={28} fill={theme.muted}>
                {compact(t * yMax, locale, prefix, suffix)}</text>
            </g>
          ))}
          {[xMin, (xMin + xMax) / 2, xMax].map((x) => (
            <text key={x} x={X(x)} y={H - padB + 46} textAnchor="middle" fontFamily="Inter" fontWeight={700} fontSize={28} fill={theme.muted}>
              {Math.round(x)}{str(v.xSuffix)}</text>
          ))}
          {series.map((s, i) => {
            const pts = s.points;
            const upto = xMin + (xMax - xMin) * draw;
            const visible = pts.filter((p) => p[0] <= upto);
            const last = pts.find((p) => p[0] > upto);
            const prev = visible[visible.length - 1];
            if (last && prev) {
              const t = (upto - prev[0]) / (last[0] - prev[0]);
              visible.push([upto, prev[1] + (last[1] - prev[1]) * t]);
            }
            const d = visible.map((p, j) => `${j ? 'L' : 'M'}${X(p[0])},${Y(p[1])}`).join(' ');
            const color = s.color ?? colors[i % colors.length];
            const end = visible[visible.length - 1];
            return (
              <g key={i}>
                <path d={d} fill="none" stroke={theme.ink} strokeWidth={14} strokeLinejoin="round" strokeLinecap="round" />
                <path d={d} fill="none" stroke={color} strokeWidth={8} strokeLinejoin="round" strokeLinecap="round" />
                {end && <circle cx={X(end[0])} cy={Y(end[1])} r={14} fill={color} stroke={theme.ink} strokeWidth={5} />}
                {end && (
                  <text x={Math.min(X(end[0]), W - padR - 10)} y={Y(end[1]) - 30} textAnchor="end" fontFamily="Inter Display"
                    fontWeight={900} fontSize={40} fill={theme.ink}>{fmt(end[1], locale, num(v.decimals), prefix, suffix)}</text>
                )}
              </g>
            );
          })}
        </svg>
        <div style={{display: 'flex', gap: 34, justifyContent: 'center', marginTop: 6}}>
          {series.map((s, i) => (
            <div key={i} style={{display: 'flex', alignItems: 'center', gap: 12, fontFamily: FONT, fontWeight: 700,
              fontSize: 32, color: theme.ink}}>
              <div style={{width: 34, height: 14, borderRadius: 7, background: s.color ?? colors[i % colors.length],
                border: `3px solid ${theme.ink}`}} />{s.label}</div>
          ))}
        </div>
      </div>
    </div>
  );
};

type Bar = {label: string; value: number; highlight?: boolean};

// Bars grow one after another; values count with them.
export const BarCompareScene: React.FC<P> = ({v, durationInFrames}) => {
  const frame = useCurrentFrame();
  const {theme, locale, fps} = useShort();
  const bars = (v.bars as Bar[]) ?? [];
  const max = Math.max(...bars.map((b) => b.value), 1);
  const step = Math.max(6, (durationInFrames * 0.5) / Math.max(1, bars.length));
  const maxH = 520;
  const barW = Math.min(220, (BOX.width - 80) / Math.max(1, bars.length) - 40);
  return (
    <div style={{position: 'absolute', ...BOX, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 30}}>
      {str(v.title) && <div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: fit(str(v.title), 70, 46, 24),
        color: theme.ink, textAlign: 'center', opacity: enter(frame, fps)}}>{str(v.title)}</div>}
      <div style={{display: 'flex', alignItems: 'flex-end', justifyContent: 'center', gap: 40, height: maxH + 150}}>
        {bars.map((b, i) => {
          const g = progress(frame, 6 + i * step, 6 + i * step + 22);
          const h = Math.max(8, (b.value / max) * maxH * g);
          const fill = b.highlight ? theme.accent : theme.card;
          return (
            <div key={i} style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14, width: barW}}>
              <div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: fit(fmt(b.value, locale, num(v.decimals), str(v.prefix), str(v.suffix)), 52, 30, 7),
                color: theme.ink, opacity: g, fontVariantNumeric: 'tabular-nums'}}>
                {fmt(b.value * g, locale, num(v.decimals), str(v.prefix), str(v.suffix))}</div>
              <div style={{width: '100%', height: h, background: fill, border: `6px solid ${theme.ink}`, borderRadius: '22px 22px 6px 6px',
                boxShadow: `10px 10px 0 ${theme.ink}`}} />
              <div style={{fontFamily: FONT, fontWeight: 800, fontSize: fit(b.label, 36, 24, 12), color: theme.ink,
                textAlign: 'center', height: 90, lineHeight: 1.15}}>{b.label}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// Circular gauge for a percentage.
export const RingScene: React.FC<P> = ({v, durationInFrames}) => {
  const frame = useCurrentFrame();
  const {theme, locale, fps} = useShort();
  const value = Math.max(0, Math.min(100, num(v.value)));
  const g = progress(frame, 6, Math.max(26, durationInFrames * 0.5));
  const R = 260, C = 2 * Math.PI * R;
  const c = enter(frame, fps, 0, 12);
  return (
    <div style={{position: 'absolute', ...BOX, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 30}}>
      {str(v.title) && <div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: fit(str(v.title), 66, 44, 24),
        color: theme.ink, textAlign: 'center', opacity: c}}>{str(v.title)}</div>}
      <div style={{position: 'relative', width: 2 * R + 80, height: 2 * R + 80, transform: `scale(${0.7 + 0.3 * c})`}}>
        <svg width={2 * R + 80} height={2 * R + 80} style={{transform: 'rotate(-90deg)'}}>
          <circle cx={R + 40} cy={R + 40} r={R} fill={theme.card} stroke={theme.ink} strokeWidth={60} />
          <circle cx={R + 40} cy={R + 40} r={R} fill="none" stroke={theme.card} strokeWidth={44} />
          <circle cx={R + 40} cy={R + 40} r={R} fill="none" stroke={v.bad ? theme.bad : theme.accent} strokeWidth={44}
            strokeDasharray={C} strokeDashoffset={C * (1 - (value / 100) * g)} strokeLinecap="round" />
        </svg>
        <div style={{position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'}}>
          <div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: 150, color: theme.ink, letterSpacing: -4}}>
            {fmt(value * g, locale, num(v.decimals), '', '%')}</div>
          {str(v.label) && <div style={{fontFamily: FONT, fontWeight: 800, fontSize: fit(str(v.label), 40, 28, 18),
            color: theme.muted, maxWidth: 380, textAlign: 'center'}}>{str(v.label)}</div>}
        </div>
      </div>
    </div>
  );
};

// "N in 100" style probability grid.
export const DotGridScene: React.FC<P> = ({v, durationInFrames}) => {
  const frame = useCurrentFrame();
  const {theme, fps} = useShort();
  const total = Math.min(400, Math.max(1, num(v.total, 100)));
  const highlight = Math.min(total, Math.max(0, num(v.highlight, 1)));
  const cols = num(v.cols, total <= 100 ? 10 : 20);
  const rows = Math.ceil(total / cols);
  const reserved = (str(v.title) ? 120 : 0) + (str(v.label) ? 110 : 0);
  const size = Math.max(10, Math.floor(Math.min((BOX.width - 60) / cols, (BOX.height - reserved) / rows)) - 8);
  const fill = progress(frame, 10, Math.max(30, durationInFrames * 0.6));
  const lit = Math.round(highlight * fill);
  return (
    <div style={{position: 'absolute', ...BOX, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 30}}>
      {str(v.title) && <div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: fit(str(v.title), 66, 44, 24),
        color: theme.ink, textAlign: 'center', opacity: enter(frame, fps)}}>{str(v.title)}</div>}
      <div style={{display: 'grid', gridTemplateColumns: `repeat(${cols}, ${size}px)`, gap: 8}}>
        {Array.from({length: total}).map((_, i) => {
          const s = enter(frame, fps, (i % cols) * 0.6 + Math.floor(i / cols) * 0.6, 16);
          const on = i < lit;
          return <div key={i} style={{width: size, height: size, borderRadius: size / 2, transform: `scale(${s})`,
            background: on ? (v.bad ? theme.bad : theme.accent) : theme.card, border: `4px solid ${theme.ink}`}} />;
        })}
      </div>
      {str(v.label) && <div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: fit(str(v.label), 64, 40, 22),
        color: theme.ink, opacity: progress(frame, durationInFrames * 0.5, durationInFrames * 0.6)}}>{str(v.label)}</div>}
    </div>
  );
};

