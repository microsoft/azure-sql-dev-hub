#!/usr/bin/env node
// Serves a built site the way GitHub Pages does, so checks that fetch it over
// HTTP see what visitors will: /page finds page.html, a folder finds its
// index.html, a missing path gets 404.html with a 404 status, and every request
// gets the same HTML back whatever its Accept header asks for, because Pages
// cannot negotiate content. No dependencies.
//
//   node scripts/serve-site.mjs [dir=_site] [port=8080]

import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { join, normalize, extname, sep } from 'node:path';

const ROOT = normalize(process.argv[2] || '_site');
const PORT = Number(process.argv[3] || 8080);
const TYPES = {
  '.html': 'text/html; charset=utf-8', '.md': 'text/markdown; charset=utf-8', '.txt': 'text/plain; charset=utf-8',
  '.xml': 'application/xml', '.json': 'application/json', '.css': 'text/css', '.js': 'text/javascript',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp',
  '.gif': 'image/gif', '.ico': 'image/x-icon', '.woff2': 'font/woff2', '.mp4': 'video/mp4', '.webm': 'video/webm',
};

const isFile = async (p) => { try { return (await stat(p)).isFile(); } catch { return false; } };
const isDir = async (p) => { try { return (await stat(p)).isDirectory(); } catch { return false; } };

async function resolve(urlPath) {
  const rel = decodeURIComponent(urlPath.split('?')[0]).replace(/^\/+/, '');
  const p = normalize(join(ROOT, rel));
  if (p !== ROOT && !p.startsWith(ROOT + sep)) return null; // no climbing out of the site
  if (await isFile(p)) return { file: p };
  if (await isDir(p)) {
    // Pages redirects /folder to /folder/ before serving its index.
    if (!urlPath.split('?')[0].endsWith('/')) return { redirect: urlPath.split('?')[0] + '/' };
    if (await isFile(join(p, 'index.html'))) return { file: join(p, 'index.html') };
  }
  if (await isFile(p + '.html')) return { file: p + '.html' };
  return null;
}

createServer(async (req, res) => {
  try {
    const hit = await resolve(req.url || '/');
    if (hit && hit.redirect) {
      res.writeHead(301, { location: hit.redirect }).end();
      return;
    }
    const file = hit ? hit.file : join(ROOT, '404.html');
    const status = hit ? 200 : 404;
    const body = hit || (await isFile(file)) ? await readFile(file) : Buffer.from('Not found\n');
    res.writeHead(status, {
      'content-type': hit || (await isFile(file)) ? TYPES[extname(file).toLowerCase()] || 'application/octet-stream' : 'text/plain',
      'content-length': body.length,
      'cache-control': 'max-age=600',
    });
    res.end(req.method === 'HEAD' ? undefined : body);
  } catch (e) {
    res.writeHead(500, { 'content-type': 'text/plain' }).end(String(e));
  }
}).listen(PORT, () => console.log(`serving ${ROOT} on http://localhost:${PORT}`));
