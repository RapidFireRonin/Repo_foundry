# Product Gallery Contract v1

This contract defines how completed playable or usable deliverables become visible and launchable in Mission Control.

## Purpose

Mission Control must not only show agent activity. It must also provide a polished gallery of products Garrett can open, test, and use.

## Product registry

Agents must register completed products in `registry/products.yaml`.

Each registered product should include:

- `id`: stable machine-readable product id.
- `title`: human-readable product name.
- `status`: one of `usable`, `playable`, `complete`, `working`, `needs-proof`, or `blocked`.
- `kind`: product category, such as `game`, `web-app`, `tool`, `repo`, or `control-plane`.
- `description`: what was built.
- `launch_url`: URL or route Garrett can open to use the product.
- `repo_url`: source repository when available.
- `visual_proof`: screenshot or visual artifact path when available.
- `test_evidence`: checks, smoke tests, builds, or playtests that passed.
- `quality`: plain-English quality verdict.
- `next_action`: what should happen next.
- `last_verified`: date or timestamp of the latest verification.

## Agent requirements

When an autonomous agent finishes a user-facing product, game, tool, or usable repo, it must:

- Add or update a product entry in `registry/products.yaml`.
- Include a launch URL whenever the product can be opened.
- Attach visual proof for UI, game, or app deliverables.
- Attach test evidence before marking the product `usable`, `playable`, or `complete`.
- Mention the product entry in the hourly cycle summary.
- Link related PRs, commits, workflow runs, artifacts, and logs.

## Dashboard requirements

Mission Control must show a visible Playable / Usable Products gallery with:

- Completed products first.
- Product status and kind.
- Open Product action for launchable deliverables.
- Visual proof action when proof exists.
- Repo/source action when available.
- Test evidence and quality verdict.
- Next action and latest verification marker.

## Definition of done

A product deliverable is not fully done until Garrett can find it in Mission Control, open or inspect it from the product gallery, and see proof that it was tested or verified.

## Product quality gate

Mission Control must evaluate every registered product with a machine-readable quality gate. Agents must not claim `usable`, `playable`, or `complete` unless the product passes the gate.

The gate requires:

- Launch or inspection access for anything marked done.
- Screenshot or visual proof for games, web apps, tools, operator tools, and control-plane UI.
- At least two concrete test, build, smoke-test, or playtest evidence items.
- A specific plain-English quality verdict, not a placeholder or vague "looks shippable" claim.
- `last_verified` from a real smoke test, playtest, or build verification.
- A next recommended action.
- For games, evidence of a real playable interaction loop.

Mission Control must show the gate status, score, verdict, and blockers on each product card so weak deliverables remain visible as weak instead of being hidden behind a finished-looking label.
