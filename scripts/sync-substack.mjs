#!/usr/bin/env node
// Pulls new posts from tutuadetunmbi.substack.com/feed and creates
// markdown files in src/content/memos/. Skips posts that already exist
// (by slug). Safe to run repeatedly — idempotent.

import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import Parser from 'rss-parser';
import TurndownService from 'turndown';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const FEED_URL = 'https://tutuadetunmbi.substack.com/feed';
const MEMOS_DIR = path.join(__dirname, '..', 'src', 'content', 'memos');

const parser = new Parser({
  customFields: {
    item: [
      ['content:encoded', 'contentEncoded'],
      ['media:content', 'mediaContent', { keepArray: true }],
      ['enclosure', 'enclosureRaw'],
    ],
  },
});

const turndown = new TurndownService({
  headingStyle: 'atx',
  codeBlockStyle: 'fenced',
  bulletListMarker: '-',
  emDelimiter: '*',
});

// Bold + italic combined
turndown.addRule('boldItalic', {
  filter: (node) =>
    (node.nodeName === 'STRONG' && node.firstChild && node.firstChild.nodeName === 'EM') ||
    (node.nodeName === 'EM' && node.firstChild && node.firstChild.nodeName === 'STRONG'),
  replacement: (content) => `***${content}***`,
});

// Strip Substack CTA blocks + subscribe buttons + share widgets
turndown.addRule('stripSubstackCTAs', {
  filter: (node) => {
    if (node.nodeName === 'DIV' || node.nodeName === 'P') {
      const txt = (node.textContent || '').trim();
      if (/^(Leave a comment|Share|Subscribe|Thanks for reading)/i.test(txt)) return true;
    }
    if (node.nodeName === 'A') {
      const href = node.getAttribute && node.getAttribute('href');
      if (href && (href.includes('/subscribe') || href.includes('/comments'))) return true;
    }
    return false;
  },
  replacement: () => '',
});

function slugFromUrl(url) {
  const m = url && url.match(/\/p\/([^/?#]+)/);
  return m ? m[1] : null;
}

function extractCover(item) {
  // Prefer enclosure
  if (item.enclosureRaw && item.enclosureRaw.url) return item.enclosureRaw.url;
  if (item.enclosure && item.enclosure.url) return item.enclosure.url;
  // Then media:content
  if (Array.isArray(item.mediaContent) && item.mediaContent[0] && item.mediaContent[0].$) {
    return item.mediaContent[0].$.url;
  }
  // Fallback: first image in body HTML
  const html = item.contentEncoded || item.content || '';
  const m = html.match(/<img[^>]+src="([^"]+)"/i);
  return m ? m[1] : null;
}

function yamlEscape(s) {
  return String(s == null ? '' : s).replace(/\\/g, '\\\\').replace(/"/g, '\\"');
}

function toISODate(d) {
  const dt = new Date(d);
  if (isNaN(dt.getTime())) return new Date().toISOString().slice(0, 10);
  return dt.toISOString().slice(0, 10);
}

function cleanDescription(item) {
  const raw = (item.contentSnippet || item.summary || '').trim();
  // First paragraph, capped ~200 chars, with ellipsis if truncated
  const firstPara = raw.split(/\n{2,}|\r\n\r\n/)[0].trim();
  if (firstPara.length <= 200) return firstPara;
  return firstPara.slice(0, 197).trimEnd() + '…';
}

function convertBody(item) {
  const html = item.contentEncoded || item.content || '';
  if (!html) return '';
  let md = turndown.turndown(html);
  // Collapse excessive blank lines
  md = md.replace(/\n{3,}/g, '\n\n').trim();
  return md;
}

async function ensureDir(dir) {
  await fs.mkdir(dir, { recursive: true });
}

async function existingSlugs() {
  await ensureDir(MEMOS_DIR);
  const files = await fs.readdir(MEMOS_DIR);
  return new Set(files.filter((f) => f.endsWith('.md')).map((f) => f.replace(/\.md$/, '')));
}

async function main() {
  console.log(`[sync-substack] Fetching ${FEED_URL}…`);
  const feed = await parser.parseURL(FEED_URL);
  console.log(`[sync-substack] Feed has ${feed.items.length} items.`);

  const have = await existingSlugs();
  let created = 0;

  for (const item of feed.items) {
    const slug = slugFromUrl(item.link);
    if (!slug) {
      console.log(`[sync-substack] Skipping (no slug): ${item.title}`);
      continue;
    }
    if (have.has(slug)) continue;

    const cover = extractCover(item);
    const body = convertBody(item);
    const description = cleanDescription(item);

    const frontLines = [
      '---',
      `title: "${yamlEscape(item.title)}"`,
      `description: "${yamlEscape(description)}"`,
      `pubDate: ${toISODate(item.pubDate || item.isoDate)}`,
      `substackUrl: "${item.link}"`,
    ];
    if (cover) {
      frontLines.push(`cover: "${cover}"`);
      frontLines.push(`coverAlt: "${yamlEscape(item.title)}"`);
    }
    frontLines.push('---', '', body, '');

    const filepath = path.join(MEMOS_DIR, `${slug}.md`);
    await fs.writeFile(filepath, frontLines.join('\n'), 'utf8');
    console.log(`[sync-substack]   + ${slug}.md`);
    created++;
  }

  console.log(`[sync-substack] Done. ${created} new memo(s) created.`);
}

main().catch((err) => {
  console.error('[sync-substack] FAILED:', err && err.message ? err.message : err);
  // Don't fail the build if RSS is temporarily unreachable.
  process.exit(0);
});
