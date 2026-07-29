## Automation wrapper — mandatory Git rules

The external automation wrapper has already verified that the repository is clean, executed `git fetch origin` and `git pull --ff-only origin main`, and confirmed that local `main` is synchronized with `origin/main`.

Do not execute `git fetch`, `git pull`, `git commit`, `git push`, or any command that writes inside `.git`.
Do not repeat Git synchronization or startup gate checks from inside Codex.
Work only on the site files required for the publication, run the requested quality checks, and write the exact modified-file list to the manifest path provided by `DAILY_AI_PUBLISHER_MANIFEST`.

# Daily AI Publisher Prompt

You are running inside the `underside-ai` repository to prepare the daily publication for `https://ai.underside.be/`.

Follow `AGENTS.md` exactly. Your responsibility is content discovery, content decision, site file updates, quality checks, and manifest generation. Do not commit. Do not push. Do not use `danger-full-access`.

## Non-Negotiable Startup Checks

1. Run `git fetch`.
2. Verify the current branch is `main`.
3. Verify local `main` is synchronized with `origin/main`.
4. Stop immediately if `git status --porcelain` is not empty before your work begins.
5. If any startup check fails, make no changes and report the failure.

## News Research Scope

Research AI news from the last 24 to 48 hours only.

Prioritize official sources:

- official company announcements, blogs, documentation, or press releases;
- official government, regulator, EU, standards, or public agency publications;
- official conference pages;
- official GitHub repositories or release notes;
- official financial, legal, or public filings.

Secondary sources may only be used to discover leads. They must not be the sole basis for publication.

Reject:

- rumors;
- unverifiable social posts;
- syndicated summaries without a primary source;
- speculative claims;
- topics with no clear operational relevance for Underside's audience.

## Relevance Filter

Select only topics that are genuinely relevant to Underside's positioning:

- sovereign AI and digital sovereignty;
- enterprise AI adoption, governance, compliance, security, privacy, and traceability;
- AI infrastructure, cloud, GPU capacity, data centers, private or hybrid deployments;
- European, Belgian, or French AI regulation and implementation;
- Odoo Enterprise, ERP, automation, data workflows, or AI in business operations.

Do not publish generic product noise, consumer-only features, vague funding news, or minor model updates unless there is a strong enterprise or sovereignty angle.

## Duplicate Detection

Before deciding to publish:

1. Search existing `site/article-*.html`, `site/en/article-*.html`, `site/blog.html`, `site/en/blog.html`, `site/actualites.html`, `site/en/actualites.html`, `site/llms.txt`, and `site/sitemap.xml`.
2. Compare topic, company, source URL, dates, and slug.
3. If the topic is already covered and no meaningful official update exists, publish nothing.
4. If an existing article needs a factual update from a new official source, update that article pair instead of creating a duplicate.

## Publication Decision

Choose exactly one outcome:

- create a new article;
- create a short news item;
- update an existing article pair;
- publish nothing.

The best outcome may be "publish nothing". Use it when the available official information is weak, repetitive, not relevant enough, or already covered.

## Required Language Output

For any public content update, produce French and English together.

- FR page: root `site/`.
- EN page: `site/en/`.
- Keep facts, dates, sources, figures, and conclusions aligned between languages.
- Use idiomatic English, not literal translation.
- Preserve FR as `x-default` unless an existing file clearly uses another convention.

## HTML And Site Structure

Respect the existing static HTML structure exactly:

- standalone HTML files;
- inline CSS conventions already used by adjacent pages;
- dark Underside visual identity;
- Manrope/system font stack;
- existing header, article, card, share, CTA, and metadata patterns;
- existing relative paths for assets from FR and EN pages;
- `page-transition.css` and `page-transition.js` includes where matching article templates use them.

Do not refactor shared styles. Do not rewrite existing editorial copy. Do not create a new design system.

## Files That May Be Updated

Update only files required by the selected outcome:

- `site/index.html`
- `site/en/index.html`
- `site/blog.html`
- `site/en/blog.html`
- `site/actualites.html`
- `site/en/actualites.html`
- `site/sitemap.xml`
- `site/llms.txt`
- `site/.well-known/mcp.json`
- new or updated FR article page under `site/`
- new or updated EN article page under `site/en/`
- justified new image assets under `site/media/articles/`

Do not touch unrelated files.

## Required Updates When Publishing

When creating a new article or news item:

1. Add/update the relevant FR and EN public page entries.
2. Update homepage FR and homepage EN when their visible latest-content sections require it.
3. Update blog FR and blog EN for articles.
4. Update actualites FR and actualites EN for news items.
5. Update `site/sitemap.xml` with FR and EN URLs, `lastmod`, `hreflang`, `changefreq`, and `priority`.
6. Update `site/llms.txt`.
7. Update `site/.well-known/mcp.json`, including latest URLs, dates, and stats if changed.

When updating an existing article:

1. Update both FR and EN versions.
2. Update `dateModified` in JSON-LD.
3. Update relevant hub pages only if title, summary, date, or ranking changes.
4. Update discovery files only if their metadata or dates are affected.

When publishing nothing:

1. Make no site changes.
2. Produce an empty manifest file.
3. Report why no publication was made.

## Quality Controls

Before finishing, run appropriate checks:

- parse or validate every touched HTML file;
- verify JSON-LD blocks parse as JSON;
- verify canonical and hreflang URLs are symmetrical for FR/EN pairs;
- verify newly added source links are official and open in a new tab with `rel="noopener"` when `target="_blank"` is used;
- verify `site/sitemap.xml` is well-formed XML if touched;
- verify `site/.well-known/mcp.json` is valid JSON if touched;
- run `git diff --check`;
- inspect `git diff` manually and confirm only intentional files changed.

## Manifest

At the end, generate a manifest listing only files modified by this run.

Use the manifest path provided by the automation environment variable `DAILY_AI_PUBLISHER_MANIFEST` when it exists. If it does not exist, write to `/tmp/underside-ai-daily-publisher-manifest.txt`.

Manifest format:

- UTF-8 plain text.
- One repository-relative path per line.
- No bullets.
- No commentary.
- Empty file when nothing was published.
- Include only files that should be staged by the automation script.
- Do not include logs, temporary files, or the manifest itself.

Final response must summarize:

- publication decision;
- official sources used;
- files modified;
- checks run and result;
- manifest path.
