# Deployment

## Hosting model

The production artifact is the contents of site/, served at https://frbread7.github.io/books/. Internal routes, JSON requests, canonical URLs, and local assets preserve the /books/ prefix by deriving the current flat-page base.

## GitHub Pages setup

After the repository exists, configure Settings → Pages → Build and deployment → Source: GitHub Actions. The workflow is .github/workflows/pages.yml. It validates and runs browser journeys on pull requests, then deploys after pushes to main and manual runs on main. Only site/ is uploaded.

The workflow uses actions/configure-pages@v5, actions/upload-pages-artifact@v4, and actions/deploy-pages@v4 with contents: read, pages: write, and id-token: write. Deployment uses the github-pages environment.

Official references:

- [GitHub Pages overview](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)
- [Publishing source options](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [Automatic deployment](https://docs.github.com/en/get-started/start-your-journey/deploying-your-website-automatically)
- [Pages REST API](https://docs.github.com/en/rest/pages/pages)

No custom domain or CNAME is configured. GitHub Actions must be the Pages source rather than a branch-folder build.

## Local validation prerequisites

Install Python 3.12+, Node.js 20+, and npm. Install the Python `jsonschema` dependency with `python3 -m pip install -r requirements.txt`, install JavaScript dependencies with `npm ci`, and install Playwright Chromium with `npx playwright install chromium`. On Linux hosts missing browser libraries, use `npx playwright install --with-deps chromium`. See [Testing](TESTING.md) for commands and coverage details.

## Release checks

1. Run npm ci && npm test.
2. Review catalog/index changes and check for incorrect upstream identity or invalid links.
3. Push/merge the reviewed commit to main.
4. Wait for the validation and deployment workflow to pass.
5. Confirm the GitHub Pages deployment environment reports the site URL.
6. Open the homepage, search, PMICBook English/Korean routes, subjects, paths, and experiments; inspect a mobile viewport.
7. Confirm internal assets and JSON requests use /books/ and the deployed worktree is clean.

## Feedback

The Feedback view opens the repository's public GitHub issue form. No administrative token is configured; feedback uses GitHub's public issue service. Issue titles, descriptions, attachments, and GitHub usernames are public; the issue template tells users not to submit confidential material.
