#!/usr/bin/env bash
# Publish each project under projects/ as its own GitHub repository, keeping its git history.
#
# 1. Create EMPTY repos on GitHub first (no README/license), e.g. at https://github.com/new:
#      guildforge-bot  patchmeta  overlaykit  sensforge  assetforge
#    or with the GitHub CLI:  for r in guildforge-bot patchmeta overlaykit sensforge assetforge; do gh repo create "$r" --private; done
# 2. Run from the repository root:  ./scripts/split-repos.sh [github-user] [branch]
set -euo pipefail

USER_NAME="${1:-ericx00}"
BRANCH="${2:-$(git rev-parse --abbrev-ref HEAD)}"
PROJECTS=(guildforge-bot patchmeta overlaykit sensforge assetforge)

cd "$(git rev-parse --show-toplevel)"
for p in "${PROJECTS[@]}"; do
  echo "==> $p"
  # Extract the folder's history into its own branch, then push it as that repo's main branch.
  git subtree split --prefix="projects/$p" -b "split/$p" "$BRANCH"
  git push "git@github.com:${USER_NAME}/${p}.git" "split/$p:main"
  git branch -D "split/$p"
done
echo "Done. Each project is now at https://github.com/${USER_NAME}/<project>"
