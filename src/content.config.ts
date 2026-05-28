import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const memos = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/memos' }),
  schema: z.object({
    title: z.string(),
    description: z.string().optional(),
    pubDate: z.coerce.date(),
    cover: z.string().optional(),
    coverAlt: z.string().optional(),
    draft: z.boolean().default(false),
    // Original Substack URL — kept for migration history / "Read on Substack" fallback
    substackUrl: z.string().url().optional(),
  }),
});

export const collections = { memos };
