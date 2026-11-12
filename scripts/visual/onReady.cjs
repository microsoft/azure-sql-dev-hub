// Runs once a page has loaded: load the web fonts and lazy images before the
// capture. A font only starts loading when text first uses it, so
// document.fonts.ready alone can resolve before Inter arrives; a capture in
// the fallback font wraps headings differently and shifts the whole page.
// Each face the site uses is asked for explicitly, with a time limit.
module.exports = async (page) => {
  await page.evaluate(async () => {
    const faces = ['400 16px Inter', '500 16px Inter', '600 16px Inter', '700 16px Inter',
      '400 16px "JetBrains Mono"', '500 16px "JetBrains Mono"'];
    const limit = (ms) => new Promise((done) => setTimeout(done, ms));
    if (document.fonts) {
      await Promise.race([Promise.all(faces.map((f) => document.fonts.load(f).catch(() => null))), limit(8000)]);
      await Promise.race([document.fonts.ready, limit(2000)]);
    }
    document.querySelectorAll('img[loading="lazy"]').forEach((img) => { img.loading = 'eager'; });
    await Promise.race([Promise.all([...document.images].filter((img) => !img.complete).map((img) =>
      new Promise((done) => { img.onload = img.onerror = done; }))), limit(5000)]);
  });
};
