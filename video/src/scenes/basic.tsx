import React from 'react';
import {useCurrentFrame} from 'remotion';
import {BOX, DISPLAY, FONT, card, enter, fit, fmt, num, progress, str, useShort} from '../util';
import type {Visual} from '../types';

type P = {v: Visual; durationInFrames: number};

const Center: React.FC<{children: React.ReactNode; gap?: number}> = ({children, gap = 36}) => (
  <div style={{position: 'absolute', ...BOX, display: 'flex', flexDirection: 'column', alignItems: 'center',
    justifyContent: 'center', gap, textAlign: 'center'}}>{children}</div>
);

// Big headline, words spring in one by one.
export const TitleScene: React.FC<P> = ({v}) => {
  const frame = useCurrentFrame();
  const {theme, fps} = useShort();
  const text = str(v.text);
  const words = text.split(' ');
  const size = fit(text, 112, 64, 22);
  const emoji = str(v.emoji);
  const e = enter(frame, fps, 0, 9);
  return (
    <Center>
      {emoji && <div style={{fontSize: 200, transform: `scale(${e}) rotate(${(1 - e) * -25}deg)`}}>{emoji}</div>}
      <div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: size, lineHeight: 1.05, color: theme.ink,
        letterSpacing: -2, display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '0 0.25em'}}>
        {words.map((w, i) => {
          const s = enter(frame, fps, 4 + i * 3);
          const accent = (v.accentWords as string[] | undefined)?.some((a) => w.toLowerCase().includes(a.toLowerCase()));
          return (
            <span key={i} style={{display: 'inline-block', opacity: s, transform: `translateY(${(1 - s) * 60}px)`,
              background: accent ? theme.accent : 'transparent', color: accent ? theme.accentInk : theme.ink,
              padding: accent ? '0 12px' : 0, borderRadius: 12}}>{w}</span>
          );
        })}
      </div>
      {str(v.sub) && (
        <div style={{fontFamily: FONT, fontWeight: 600, fontSize: fit(str(v.sub), 48, 34, 40), color: theme.muted,
          opacity: progress(frame, 18, 30)}}>{str(v.sub)}</div>
      )}
    </Center>
  );
};

// Counter that runs from `from` to `to`, with label and footnote.
export const BigNumberScene: React.FC<P> = ({v, durationInFrames}) => {
  const frame = useCurrentFrame();
  const {theme, locale, fps} = useShort();
  const from = num(v.from), to = num(v.to);
  const run = progress(frame, 6, Math.max(20, durationInFrames * 0.55));
  const value = from + (to - from) * run;
  const text = fmt(value, locale, num(v.decimals), str(v.prefix), str(v.suffix));
  const finalText = fmt(to, locale, num(v.decimals), str(v.prefix), str(v.suffix));
  const size = Math.min(230, Math.floor(BOX.width / (0.62 * Math.max(1, finalText.length))));
  const pop = enter(frame, fps, 0, 10);
  const underline = progress(frame, Math.max(20, durationInFrames * 0.55), Math.max(28, durationInFrames * 0.55 + 12));
  return (
    <Center gap={28}>
      {str(v.label) && (
        <div style={{fontFamily: FONT, fontWeight: 800, fontSize: fit(str(v.label), 60, 40, 26), color: theme.ink,
          opacity: pop, textTransform: 'uppercase', letterSpacing: 2}}>{str(v.emoji)} {str(v.label)}</div>
      )}
      <div style={{position: 'relative', transform: `scale(${0.6 + pop * 0.4})`}}>
        <div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: size, color: theme.ink, letterSpacing: -4,
          fontVariantNumeric: 'tabular-nums', lineHeight: 1, whiteSpace: 'nowrap'}}>{text}</div>
        <div style={{position: 'absolute', left: 0, bottom: -18, height: 26, width: `${underline * 100}%`,
          background: theme.accent, borderRadius: 13, zIndex: -1}} />
      </div>
      {str(v.sub) && (
        <div style={{fontFamily: FONT, fontWeight: 600, fontSize: fit(str(v.sub), 46, 32, 40), color: theme.muted,
          maxWidth: 860, opacity: underline}}>{str(v.sub)}</div>
      )}
    </Center>
  );
};

export const QuoteScene: React.FC<P> = ({v}) => {
  const frame = useCurrentFrame();
  const {theme, fps} = useShort();
  const text = str(v.text);
  const words = text.split(' ');
  const c = enter(frame, fps, 0, 12);
  return (
    <Center>
      <div style={{...card(theme, {padding: '70px 64px', maxWidth: 900, transform: `rotate(${-1.5 * c}deg) scale(${0.85 + 0.15 * c})`}), opacity: c}}>
        <div style={{fontFamily: "Georgia, 'DejaVu Serif', serif", fontWeight: 700, fontSize: 220, lineHeight: 0.7, height: 110,
          color: theme.accent, textAlign: 'left', textShadow: `5px 5px 0 ${theme.ink}`}}>“</div>
        <div style={{fontFamily: DISPLAY, fontWeight: 800, fontSize: fit(text, 64, 40, 60), color: theme.ink, lineHeight: 1.2}}>
          {words.map((w, i) => (
            <span key={i} style={{opacity: progress(frame, 6 + i * 1.6, 12 + i * 1.6)}}>{w} </span>
          ))}
        </div>
        {str(v.by) && <div style={{marginTop: 30, fontFamily: FONT, fontWeight: 700, fontSize: 38, color: theme.muted,
          opacity: progress(frame, 10 + words.length * 1.6, 20 + words.length * 1.6)}}>— {str(v.by)}</div>}
      </div>
    </Center>
  );
};

// Numbered points revealed evenly across the scene.
export const ListScene: React.FC<P> = ({v, durationInFrames}) => {
  const frame = useCurrentFrame();
  const {theme, fps} = useShort();
  const items = (v.items as string[]) ?? [];
  const step = Math.max(8, (durationInFrames * 0.8) / Math.max(1, items.length));
  return (
    <div style={{position: 'absolute', ...BOX, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 28}}>
      {str(v.title) && <div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: fit(str(v.title), 76, 48, 22),
        color: theme.ink, marginBottom: 12, opacity: enter(frame, fps)}}>{str(v.title)}</div>}
      {items.map((item, i) => {
        const s = enter(frame, fps, 6 + i * step);
        return (
          <div key={i} style={{...card(theme, {padding: '26px 30px', display: 'flex', alignItems: 'center', gap: 28,
            boxShadow: `8px 8px 0 ${theme.ink}`}), opacity: s, transform: `translateX(${(1 - s) * 120}px)`}}>
            <div style={{flex: '0 0 84px', height: 84, borderRadius: 42, background: theme.accent, border: `5px solid ${theme.ink}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: DISPLAY, fontWeight: 900,
              fontSize: 46, color: theme.accentInk}}>{i + 1}</div>
            <div style={{fontFamily: FONT, fontWeight: 700, fontSize: fit(item, 50, 34, 30), color: theme.ink, lineHeight: 1.2}}>{item}</div>
          </div>
        );
      })}
    </div>
  );
};

// A row of emoji "icons" with an optional arrow flow and label.
export const EmojiScene: React.FC<P> = ({v, durationInFrames}) => {
  const frame = useCurrentFrame();
  const {theme, fps} = useShort();
  const emojis = (v.emojis as string[]) ?? [];
  const flow = v.flow !== false;
  const size = emojis.length > 3 ? 150 : 210;
  const step = Math.max(6, (durationInFrames * 0.4) / Math.max(1, emojis.length));
  return (
    <Center gap={60}>
      <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
        {emojis.map((e, i) => {
          const s = enter(frame, fps, i * step, 8);
          const bob = Math.sin((frame + i * 9) / 9) * 6;
          return (
            <React.Fragment key={i}>
              {flow && i > 0 && <div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: 90, color: theme.ink,
                opacity: s}}>→</div>}
              <div style={{fontSize: size, transform: `scale(${s}) translateY(${bob}px)`}}>{e}</div>
            </React.Fragment>
          );
        })}
      </div>
      {str(v.label) && <div style={{fontFamily: DISPLAY, fontWeight: 900, fontSize: fit(str(v.label), 84, 50, 20),
        color: theme.ink, opacity: progress(frame, step * emojis.length, step * emojis.length + 10),
        background: theme.accent, padding: '8px 28px', borderRadius: 18, border: `5px solid ${theme.ink}`}}>{str(v.label)}</div>}
    </Center>
  );
};

