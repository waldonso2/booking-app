# quality-kit

Shared CI workflows (`secrets.yml`, `workflows.yml`, `dependency-review.yml`, called with `workflow_call`) and the
setup checklist (`SETUP.md`) for every project; the per-language templates are separate template repositories
(see README). Docs are German, code and comments English.

- Actions are pinned to commit SHAs with the version as a comment; zizmor (min. medium) must pass on this repo.
- A change that makes a workflow stricter is a new major tag (`v<n>`); projects pin the tag's commit.
- Performance checks never block a build (owner's rule) - they report to the run's summary only.
- Questions to the owner go as a clickable list (the question tool), never as free text.
