import React from 'react';
import {AbsoluteFill, Sequence, useVideoConfig} from 'remotion';
import {Background, Banner, Captions, ProgressBar, TopLine} from './components/Overlays';
import {SceneView} from './scenes';
import type {ShortProps} from './types';
import {ShortContext} from './util';

export const Short: React.FC<ShortProps> = (props) => {
  const {fps} = useVideoConfig();
  const captions = props.scenes.flatMap((s) => s.captions);
  const firstEnd = props.scenes[0] ? props.scenes[0].start + props.scenes[0].duration : 3;
  const lastSpeech = captions.length ? captions[captions.length - 1].end : props.duration;
  const ctaStart = Math.max(lastSpeech - 0.2, props.duration - 3);
  return (
    <ShortContext.Provider value={{theme: props.theme, locale: props.locale, fps}}>
      <AbsoluteFill>
        <Background />
        {props.scenes.map((s, i) => {
          const from = Math.round(s.start * fps);
          const len = Math.max(1, Math.round((s.start + s.duration) * fps) - from);
          return (
            <Sequence key={i} from={from} durationInFrames={len} layout="none">
              <SceneView v={s.visual} durationInFrames={len} />
            </Sequence>
          );
        })}
        <TopLine disclaimer={props.disclaimer} seriesLabel={props.seriesLabel} duration={props.duration} />
        <Banner text={props.hookText} from={0} to={Math.min(firstEnd, 3.2)} />
        <Banner text={props.cta} from={ctaStart} to={props.duration + 1} tilt={2} />
        <Captions captions={captions} />
        <ProgressBar />
      </AbsoluteFill>
    </ShortContext.Provider>
  );
};
