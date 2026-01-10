# GitHub Actions Workflows

This directory contains GitHub Actions workflows for CI/CD automation.

## Workflows

### build-and-push.yml

Builds and pushes Docker images for API and Portal components.

**Triggers:**
- Push to `main` branch
- Push of tags matching `v*`
- Pull requests to `main`

**Actions:**
- Builds multi-arch images (linux/amd64, linux/arm64)
- Pushes to GitHub Container Registry (ghcr.io)
- Tags images with:
  - Branch name (for branches)
  - PR number (for pull requests)
  - Semantic version (for tags)
  - SHA (for branches)
  - `latest` (for default branch)

### release.yml

Creates GitHub releases when tags are pushed.

**Triggers:**
- Push of tags matching `v*.*.*` (e.g., v0.1.0, v1.0.0)

**Actions:**
- Builds and pushes production images
- Creates GitHub Release with release notes
- Tags images with version and `latest`

### update-helm-chart.yml

Updates the Helm chart repository with new versions.

**Triggers:**
- Manual workflow dispatch
- Published releases

**Actions:**
- Updates Chart.yaml version
- Updates values.yaml with new image tags
- Packages and indexes the chart
- Commits and pushes to charts repository

**Requirements:**
- `GH_PAT` secret with write access to the charts repository

## Secrets

Required secrets in GitHub repository settings:

- `GITHUB_TOKEN` - Automatically provided by GitHub Actions
- `GH_PAT` - Personal Access Token with write access to charts repository (for update-helm-chart.yml)

## Usage

### Creating a Release

1. Create and push a tag (starting with v0.1.0):
   ```bash
   git tag -a v0.1.0 -m "Release version 0.1.0"
   git push origin v0.1.0
   ```

2. The `release.yml` workflow will automatically:
   - Build and push images
   - Create a GitHub Release
   - Update the Helm chart (if configured)

### Manual Chart Update

1. Go to Actions → Update Helm Chart
2. Click "Run workflow"
3. Enter the version number
4. The workflow will update the charts repository
