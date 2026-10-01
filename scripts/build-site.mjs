#!/usr/bin/env node

import { spawnSync } from "node:child_process";

const telemetryPreview = process.argv.includes("--telemetry");
const rubyCompatibility = [
  "class Object",
  "  def tainted?; false; end unless method_defined?(:tainted?)",
  "  def untaint; self; end unless method_defined?(:untaint)",
  "end",
  'ARGV.replace(["build"])',
  'load Gem.bin_path("jekyll", "jekyll")',
].join("; ");

run("bundle", ["exec", "ruby", "-e", rubyCompatibility], {
  ...process.env,
  JEKYLL_ENV: telemetryPreview ? "production" : process.env.JEKYLL_ENV || "development",
});
run(process.execPath, ["scripts/build-agent-files.mjs"], process.env);

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
