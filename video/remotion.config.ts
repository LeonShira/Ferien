import {Config} from '@remotion/cli/config';
import {existsSync} from 'fs';

// Reuse the Chromium that ships in the cloud image instead of downloading one.
const preinstalled = '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell';
const browser = process.env.REMOTION_BROWSER ?? (existsSync(preinstalled) ? preinstalled : null);
if (browser) {
  Config.setBrowserExecutable(browser);
}
Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(92);
Config.setOverwriteOutput(true);
// 'angle' renders ~3x faster than 'swangle' on CPU-only cloud machines.
Config.setChromiumOpenGlRenderer('angle');
