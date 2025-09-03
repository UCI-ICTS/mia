# Contributing Guide

Thanks for helping improve this project! We follow a lightweight Git flow with continuous integration via GitHub Actions. Please read this guide before opening a PR.

---

## 🧪 Branches

### `dev` (default branch)
- The most up-to-date branch.
- All new features and fixes should be merged here first.
- Protected via GitHub Actions (Jest + Django tests).

### `YYYY.MM` (release branches)
- Created from `dev` at the beginning of a release cycle.
- Example: `2025.04`
- Frozen at release time and used for hotfixes during the release lifecycle.

---

## 🧩 Branch Naming

Use descriptive, kebab-case names:

- `feature/add-participant-table`
- `bugfix/login-crash`
- `hotfix/patch-consent-flow`

---

## 🚀 Feature Flow

1. **Start from `dev`**  
   Create your feature branch from the `dev` branch.

2. **Develop**  
   Make atomic commits. Run all tests locally.

3. **Push + PR**  
   Open a pull request *into* `dev`.

4. **Tests**  
   All PRs must pass GitHub Actions (Jest + Django tests).

5. **Review**  
   Include screenshots or test results where relevant.

---

## 🔖 Releases

1. Create a release branch from `dev`  
   Example:
   ```bash
   git checkout dev
   git pull
   git checkout -b 2025.04
2. Bump version number and tag (in code or via CI/CD)
3. Push the branch:
    ```bash
   git push origin 2025.04
   git tag v2025.04.0
   git push origin v2025.04.0
    ```
4. All production hotfixes should be PR’d into the release branch (not dev).

## ✅ Tests
This project uses:

- [Django tests](https://docs.djangoproject.com/en/dev/topics/testing/) for backend (server).
- [Jest tests](https://jestjs.io/docs/getting-started) for frontend (client).

CI runs both on all pull requests.


# 🙏 Thanks!
Your contributions make this project better. 

Don’t hesitate to open issues or suggest improvements:
- 🐛 [Bug Report](https://github.com/UCI-GREGoR/GREGor_dashboard/issues/new?template=bug_report.md)
- ✨ [Feature Request](https://github.com/UCI-GREGoR/GREGor_dashboard/issues/new?template=feature_request.md)
- 📝 [User Story](https://github.com/UCI-GREGoR/GREGor_dashboard/issues/new?template=user_story.md)
