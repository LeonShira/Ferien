import React from 'react';
import {Composition} from 'remotion';
import sample from './sample.json';
import {Short} from './Short';
import type {ShortProps} from './types';

export const Root: React.FC = () => (
  <Composition
    id="Short"
    component={Short}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={Math.round((sample as ShortProps).duration * 30)}
    defaultProps={sample as ShortProps}
    calculateMetadata={({props}) => ({
      durationInFrames: Math.round(props.duration * props.fps),
      fps: props.fps,
      width: props.width,
      height: props.height,
    })}
  />
);
