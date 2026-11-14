#!/usr/bin/env node

import { spawnSync } from "node:child_process";

const telemetryPreview = process.argv.includes("--telemetry");
const serve = process.argv.includes("--serve");
const jekyllArgs = serve
  ? ["serve", "--baseurl", "", "--host", process.env.JEKYLL_HOST || "127.0.0.1", "--livereload", "--force_polling"]
  : ["build"];
const rubyCompatibility = [
  "class Object",
  "  def tainted?; false; end unless method_defined?(:tainted?)",
  "  def untaint; self; end unless method_defined?(:untaint)",
  "end",
  ...(serve ? [
    'require "jekyll"',
    'Jekyll::Hooks.register(:site, :post_write) do |_site|',
    '  abort "Agent file generation failed" unless system(ENV.fetch("JEKYLL_NODE_EXECUTABLE"), "scripts/build-agent-files.mjs")',
    'end',
  ] : []),
  `ARGV.replace(${JSON.stringify(jekyllArgs)})`,
  'load Gem.bin_path("jekyll", "jekyll")',
].join("; ");

run("ruby", ["-S", "bundle", "exec", "ruby", "-e", rubyCompatibility], {
  ...process.env,
  JEKYLL_NODE_EXECUTABLE: process.execPath,
  JEKYLL_ENV: telemetryPreview ? "production" : process.env.JEKYLL_ENV || "development",
});
if (!serve) {
  run(process.execPath, ["scripts/build-agent-files.mjs"], process.env);
}

function run(command, args, env) {
  const result = spawnSync(command, args, {
    env,
    stdio: "inherit",
  });
  if (result.error) {
    throw result.error;
  }
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}
