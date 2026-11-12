// Visual diff for PRs with BackstopJS (MIT). The PR workflow serves the base
// branch's build and the PR's build side by side; `backstop reference` captures
// each page from the base, `backstop test` captures it from the PR and compares.
// Nothing is committed: both sides are built fresh in the same job.
//
// Environment: BASE_URL, PR_URL (no trailing slash), OUT_DIR, CHROME_PATH.
// Pages are the ones that exist on every branch so far; add a path here to
// cover a new page.

const PAGES = [
  ['Home', '/'],
  ['Prompt page', '/build/javascript-app.html'],
  ['All prompts', '/prompts.html'],
  ['Privacy', '/privacy.html'],
];
const base = process.env.BASE_URL || 'http://localhost:8081';
const pr = process.env.PR_URL || 'http://localhost:8080';
const out = process.env.OUT_DIR || 'backstop_data';

module.exports = {
  id: 'hub',
  viewports: [
    { label: 'desktop', width: 1280, height: 800 },
    { label: 'phone', width: 390, height: 844 },
  ],
  onBeforeScript: 'onBefore.cjs',
  onReadyScript: 'onReady.cjs',
  scenarios: PAGES.map(([label, path]) => ({
    label,
    url: pr + path,
    referenceUrl: base + path,
    selectors: ['document'],
    // Video thumbnails come from YouTube and can differ run to run.
    hideSelectors: ['.vid-thumb img'],
    delay: 400,
    misMatchThreshold: 0.1,
    requireSameDimensions: false,
  })),
  paths: {
    engine_scripts: __dirname,
    bitmaps_reference: `${out}/reference`,
    bitmaps_test: `${out}/test`,
    html_report: `${out}/html`,
    json_report: `${out}/json`,
  },
  report: ['json'],
  engine: 'puppeteer',
  engineOptions: {
    executablePath: process.env.CHROME_PATH || undefined,
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  },
  asyncCaptureLimit: 4,
  asyncCompareLimit: 20,
  debug: false,
};
