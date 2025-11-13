# Next.js Demo Dashboard - Deployment Instructions

This document provides instructions for completing the GitHub Pages deployment for the vTOC demo dashboard.

## Current Status

✅ **Completed:**
- Next.js + TypeScript app scaffolded at repo root
- Static export configured with basePath `/vTOC/demo`
- Four station pages (TOC-S1, TOC-S2, TOC-S3, TOC-S4) with mock data
- Timeline component with IMEI blacklist alerts (red-tinted borders)
- Global styles ported from existing frontend
- GitHub Actions workflow created (.github/workflows/pages-demo.yml)
- README updated with Live Demo link
- Local build verified and passes TypeScript checks
- .nojekyll file automatically added to output

⏳ **Pending:**
- GitHub Pages must be enabled in repository settings
- Workflow run requires approval (appears to have environment protection)

## Manual Steps Required

### 1. Enable GitHub Pages

Go to repository Settings → Pages and configure:
- **Source**: Deploy from a branch
- **Branch**: `gh-pages` / `/ (root)`
- **Save**

### 2. Run the Workflow

The workflow is set to run automatically on pushes to `copilot/gh-pages-demo` branch. 
It can also be triggered manually:

1. Go to Actions → "Deploy Demo (Next.js → GitHub Pages)"
2. Click "Run workflow"
3. Select branch: `copilot/gh-pages-demo`
4. Click "Run workflow"

### 3. Approve Environment Protection (if required)

If the workflow shows "action_required" status:
1. Check if there are pending approvals in the Actions tab
2. Approve the deployment to continue

## Verification Steps

Once deployed, verify at https://pr-cybr.github.io/vTOC/demo/:

- [ ] Root redirects to /demo/
- [ ] Landing page redirects to /stations/toc-s1/
- [ ] All 4 station pages load without console errors
- [ ] KPI cards show metrics (Events, Active Sources)
- [ ] Timeline displays entries grouped by date
- [ ] IMEI blacklist alerts have red-tinted borders and ⚠️ icon
- [ ] Mission Console placeholder visible at bottom-right
- [ ] Navigation pills switch between stations
- [ ] Role badges display next to station names

## Local Development

```bash
# Install dependencies
pnpm install

# Start dev server
pnpm run dev
# Visit http://localhost:3000/vTOC/demo/

# Type check
pnpm run typecheck

# Build for production
pnpm run build
# Output in out/ directory
```

## Architecture

- **Pages Router**: Using Next.js Pages Router (not App Router)
- **Static Generation**: All pages pre-rendered at build time via `getStaticProps`
- **Data**: Mock JSON files in `public/data/`
- **Styles**: Global CSS with vTOC visual identity
- **Export**: Static HTML in `out/` with basePath `/vTOC/demo/`

## Files Structure

```
.
├─ pages/
│  ├─ _app.tsx                    # App wrapper with global styles
│  ├─ index.tsx                   # Redirects to toc-s1
│  ├─ 404.tsx                     # Custom 404 page
│  └─ stations/[slug].tsx         # Dynamic station pages
├─ components/
│  ├─ Layout.tsx                  # Header, nav, console
│  └─ Timeline.tsx                # Timeline entries with date groups
├─ lib/
│  ├─ data.ts                     # Server-side data loading (fs)
│  ├─ utils.ts                    # Client-side utilities
│  ├─ time.ts                     # Date formatting
│  └─ types.ts                    # TypeScript types
├─ styles/globals.css             # vTOC visual identity
├─ public/data/                   # Mock JSON data
├─ next.config.js                 # Next.js config for GH Pages
└─ .github/workflows/pages-demo.yml
```

## Troubleshooting

### Build Fails with Module Not Found

Ensure lib/ directory is not being ignored:
```gitignore
lib/
!lib/
!lib/**
```

### Assets 404 on GitHub Pages

- Verify `.nojekyll` exists in gh-pages branch
- Check basePath in next.config.js matches: `/vTOC/demo`
- Ensure assetPrefix is set: `/vTOC/demo/`

### Workflow Shows "action_required"

This indicates an environment protection rule. Go to Settings → Environments → Review required deployments.
