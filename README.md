# tutuadetunmbi.com

The site behind [tutuadetunmbi.com](https://tutuadetunmbi.com). Built with [Astro](https://astro.build).

## Writing a new memo

Memos live in `src/content/memos/` as markdown files.

To publish a new one:

1. Create a new file: `src/content/memos/your-memo-slug.md`
2. Add the frontmatter:

   ```md
   ---
   title: "Your memo title"
   description: "One-line preview (shows in lists)."
   pubDate: 2026-05-30
   cover: "https://path-to-cover-image.jpg"  # optional
   coverAlt: "Alt text for the cover"        # optional
   draft: false                              # set to true to hide
   ---
   ```

3. Write the memo body in markdown below the frontmatter.
4. Commit and push to GitHub. Netlify rebuilds automatically.

The slug (file name minus `.md`) becomes the URL: `/memos/your-memo-slug/`.

## Editing in GitHub web UI (no terminal)

Go to `https://github.com/YOUR-USERNAME/tutuadetunmbi-com/tree/main/src/content/memos`, click **Add file → Create new file**, name it `your-memo-slug.md`, paste in the frontmatter and body, scroll down, hit **Commit changes**. Netlify auto-deploys in ~30 seconds.

## Running locally

```bash
npm install
npm run dev
```

Open http://localhost:4321.

## Deploy

Netlify auto-builds from the `main` branch. Build command: `npm run build`. Publish directory: `dist`.

## Email collection

Subscribe forms post to Buttondown (`tutuadetunmbi` account). To change the recipient, edit `BUTTONDOWN_USERNAME` in `src/components/Subscribe.astro`.

## Structure

```
src/
  layouts/Layout.astro      # base HTML shell (head, nav, footer)
  components/
    Nav.astro
    Footer.astro
    Subscribe.astro
  content/
    memos/                   # markdown memos go here
  pages/
    index.astro              # homepage
    memos/
      index.astro            # /memos
      [...slug].astro        # /memos/[slug]
  styles/global.css
public/                      # static assets (images, _redirects)
```
