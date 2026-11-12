// Runs before each page loads. Reduced motion keeps every animation on its
// finished frame (see the .motion class in the layouts), so two captures of
// the same page match instead of catching the hero demo mid-type.
module.exports = async (page) => {
  await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
};
