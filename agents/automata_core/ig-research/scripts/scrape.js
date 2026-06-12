#!/usr/bin/env node
"use strict";

/**
 * CDP-based Instagram scraper for agency-research's CDPInstagramScraper.
 *
 * Connects to an already-running, logged-in Chrome instance via the
 * DevTools protocol (started with --remote-debugging-port, e.g. via
 * agents/automata_core/scripts/open-instagram-session.ps1 -Mode cdp),
 * scrapes competitor profiles and hashtag pages, and writes the results
 * to raw-posts.json in the given project directory.
 *
 * Usage: node scripts/scrape.js <project-dir>
 *   <project-dir>/config.json   — input (written by CDPInstagramScraper)
 *   <project-dir>/raw-posts.json — output
 */

const fs = require("fs");
const path = require("path");
const puppeteer = require("puppeteer-core");

const NAV_TIMEOUT = 30000;
const POST_LINK_SELECTOR = 'a[href*="/p/"], a[href*="/reel/"]';

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function jitter(min, max) {
  return sleep(min + Math.random() * (max - min));
}

function shortcodeFromUrl(url) {
  const match = url.match(/\/(p|reel)\/([^/?]+)/);
  return match ? match[2] : "";
}

/** Parse Instagram's <meta name="description"> content for likes/comments/caption. */
function parseMetaDescription(desc) {
  if (!desc) return { likes: "", comments: "", caption: "" };

  const full = desc.match(
    /^([\d.,]+[KMB]?)\s+[Ll]ikes?,\s+([\d.,]+[KMB]?)\s+[Cc]omments?\s+-\s+.+?:\s+"([\s\S]*)"\s*$/
  );
  if (full) {
    return { likes: full[1], comments: full[2], caption: full[3] };
  }

  const likes = desc.match(/([\d.,]+[KMB]?)\s+[Ll]ikes?/);
  const comments = desc.match(/([\d.,]+[KMB]?)\s+[Cc]omments?/);
  const caption = desc.match(/:\s+"([\s\S]*)"\s*$/);
  return {
    likes: likes ? likes[1] : "",
    comments: comments ? comments[1] : "",
    caption: caption ? caption[1] : "",
  };
}

async function collectPostLinks(page, count) {
  await page.waitForSelector(POST_LINK_SELECTOR, { timeout: NAV_TIMEOUT }).catch(() => {});

  const links = new Set();
  let attempts = 0;
  while (links.size < count && attempts < 6) {
    const hrefs = await page.$$eval(POST_LINK_SELECTOR, (els) => els.map((e) => e.href));
    for (const href of hrefs) {
      links.add(href);
      if (links.size >= count) break;
    }
    if (links.size >= count) break;
    await page.evaluate(() => window.scrollBy(0, window.innerHeight * 2));
    await jitter(1000, 2000);
    attempts += 1;
  }
  return Array.from(links).slice(0, count);
}

async function scrapePost(browser, url) {
  const page = await browser.newPage();
  try {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: NAV_TIMEOUT });
    await jitter(800, 1800);

    const description = await page
      .$eval('meta[name="description"]', (el) => el.content)
      .catch(() => "");
    const isVideo = await page.$("video").then(Boolean).catch(() => false);
    const { likes, comments, caption } = parseMetaDescription(description);

    return {
      postId: shortcodeFromUrl(url),
      url,
      fullCaption: caption,
      likes,
      comments,
      shares: 0,
      date: "",
      type: url.includes("/reel/") ? "Reel" : isVideo ? "Video" : "Image",
    };
  } finally {
    await page.close();
  }
}

async function scrapeLinks(browser, listUrl, count) {
  const page = await browser.newPage();
  let links = [];
  try {
    await page.goto(listUrl, { waitUntil: "domcontentloaded", timeout: NAV_TIMEOUT });
    await jitter(1500, 2500);
    links = await collectPostLinks(page, count);
  } finally {
    await page.close();
  }

  const posts = [];
  for (const link of links) {
    try {
      posts.push(await scrapePost(browser, link));
    } catch (err) {
      console.error(`  ! failed to scrape ${link}: ${err.message}`);
    }
    await jitter(1500, 3000);
  }
  return posts;
}

async function main() {
  const projectDir = process.argv[2];
  if (!projectDir) {
    console.error("Usage: node scrape.js <project-dir>");
    process.exit(1);
  }

  const configPath = path.join(projectDir, "config.json");
  const config = JSON.parse(fs.readFileSync(configPath, "utf-8"));
  const port = config.browserPort || 9222;
  const maxCompetitorPosts = config.maxCompetitorPosts || 12;
  const maxPostsPerSearch = config.maxPostsPerSearch || 20;

  console.error(`[ig-research] connecting to Chrome on port ${port}...`);
  const browser = await puppeteer.connect({ browserURL: `http://127.0.0.1:${port}` });

  const posts = [];

  for (const url of config.competitors || []) {
    const handle = url.replace(/^https?:\/\/(www\.)?instagram\.com\//, "").replace(/\/+$/, "");
    console.error(`[ig-research] scraping competitor @${handle}...`);
    try {
      const items = await scrapeLinks(browser, url, maxCompetitorPosts);
      for (const item of items) {
        posts.push({ ...item, source: `competitor:${handle}` });
      }
    } catch (err) {
      console.error(`  ! failed competitor @${handle}: ${err.message}`);
    }
  }

  for (const term of config.searchTerms || []) {
    const tag = term.replace(/^#/, "");
    console.error(`[ig-research] scraping hashtag #${tag}...`);
    try {
      const items = await scrapeLinks(
        browser,
        `https://www.instagram.com/explore/tags/${tag}/`,
        maxPostsPerSearch
      );
      for (const item of items) {
        posts.push({ ...item, source: `hashtag:${tag}` });
      }
    } catch (err) {
      console.error(`  ! failed hashtag #${tag}: ${err.message}`);
    }
  }

  await browser.disconnect();

  fs.writeFileSync(path.join(projectDir, "raw-posts.json"), JSON.stringify({ posts }, null, 2));
  console.error(`[ig-research] wrote ${posts.length} posts to raw-posts.json`);
}

main().catch((err) => {
  console.error(`[ig-research] fatal: ${err.message}`);
  process.exit(1);
});
