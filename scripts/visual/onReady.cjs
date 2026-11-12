// Runs once a page has loaded: wait for web fonts and lazy images, so a
// capture never shows the fallback font or an empty image box.
module.exports = async (page) => {
  await page.evaluate(async () => {
    if (document.fonts) await document.fonts.ready;
    document.querySelectorAll('img[loading="lazy"]').forEach((img) => { img.loading = 'eager'; });
    await Promise.all([...document.images].filter((img) => !img.complete).map((img) =>
      new Promise((done) => { img.onload = img.onerror = done; setTimeout(done, 3000); })));
  });
};
