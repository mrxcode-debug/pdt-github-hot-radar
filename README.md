# PDT GitHub Hot Radar — Daily Open-Source Discovery

**GitHub Actions scans once daily around 08:23 Vietnam time, with zero additional ChatGPT scheduled-task slots.**

- [Latest digest](reports/latest.md) · [Latest structured data](reports/latest.json)
- [Alert issues](../../issues) · [Run history](../../actions)

The scanner uses only public metadata from the official GitHub REST Search API. It samples recently created AI-agent, automation, web/QA, media and developer repos; selects up to 3 with evidence, stars, declared license, an application to PDT, and suggested sandbox review. It never clones, installs or runs third-party code.

**This is NOT the official GitHub Trending algorithm:** GitHub Search sorts recently created repos by total stars, not by daily stars gained. After a baseline is recorded, star differences are estimates across sampled runs. The four queries are not an exhaustive inventory.

New high-signal candidates generate one issue assigned to the GitHub repository owner. Notifications depend on the owner's GitHub email/notification settings. If there is no worthwhile new repo, there is no issue.

The existing ChatGPT SCOUT V5 task may also read the public report daily and decide whether to alert the owner. No sixth ChatGPT automation is required.

## Run manually

GitHub → Actions → PDT GitHub Hot Radar (daily) → Run workflow.

Python 3.12+ local smoke test: python scripts/radar.py

## Boundaries

- Never fetch private PDT repositories or disclose customer data.
- Never auto-install, deploy, execute an external repo, or buy products.
- A declared license is only metadata; review commercial use and security before adoption.
- Exclude obvious malicious descriptions; human review remains mandatory.
- GitHub scheduled workflows can be delayed, and on inactive public repos may stop after 60 days. Daily snapshot commits maintain repository activity while they succeed.

Original PDT LABS orchestration script. Ownership of third-party repositories remains with their respective authors.
