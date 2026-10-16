# Website handover and operations

Production: https://aymanesam.com · Source: https://github.com/aymanesam90-dot/aymanesam-website · Deployment branch: `main` (verify Cloudflare Pages settings).

## Updating content
1. Branch from `main` and edit corresponding English (`en/`) and Arabic (`ar/`) pages together.
2. Verify career titles, dates, certifications and metrics with the site owner; do not invent claims.
3. For new pages, update `sitemap.xml`, canonical and reciprocal `hreflang` links.
4. Open a PR. Require successful internal-link and responsive Playwright checks; for homepage changes also review Lighthouse and homepage performance checks.
5. Merge to `main` only after passing CI; verify the actual Cloudflare production deployment separately.

## Final release checklist
- [ ] Confirm Cloudflare Pages production deployment SHA matches latest `main`.
- [ ] Check DNS, HTTPS, redirects and custom domain settings in Cloudflare.
- [ ] Check live `/en/`, `/ar/`, both contact pages, `/robots.txt` and `/sitemap.xml`.
- [ ] Test email (`mailto:`), phone (`tel:`) and LinkedIn links on a device; these depend on client apps.
- [ ] Verify domain ownership in Google Search Console, submit `https://aymanesam.com/sitemap.xml`, and inspect indexing, canonical selection and bilingual pages.
- [ ] Obtain owner approval for all professional biographical claims and contact details.
- [ ] Review responsive screenshots on mobile and desktop.

## Checks
- `python3 scripts/check_internal_links.py` validates local internal links.
- `node scripts/responsive_visual_audit.mjs` runs Playwright keyboard, overflow and visual tests with a local HTTP server at port 8765 and Chromium installed.
- GitHub Actions includes mobile Lighthouse and homepage CSS/performance safeguards.
- Passing repository CI does **not** prove live DNS availability, successful deployment, Google indexing, or external mail-client behavior.

## Rollback
Revert the relevant PR merge, let Cloudflare Pages redeploy, and verify the public URLs. Keep all production changes version-controlled.
