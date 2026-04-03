# Authoring rule sets

This guide explains how the rules prompts are built and how to update or create rule sets.

## How the rules prompts are built

The rules prompts are **generated from Jinja2 templates**. The source lives under `prompts/`: shared fragments in `prompts/common/` (phase1-base, phase2, optional `gm-fidelity-combat.j2`, formatting, system-actions-core) and per-rule fragments in `prompts/rules/<rule-id>/` (opening, mechanics, and optional extra-actions). A Python script assembles them into `rules-prompts.md`.

**Assembly order** for each rule: **opening** → **phase1-base** → **mechanics** → **phase2** → **`gm-fidelity-combat.j2`** (only for rule IDs listed in `GM_FIDELITY_RULE_IDS` in `scripts/build.py`) → **formatting** → **system-actions-core** → **extra-actions** (if present).

- **To regenerate** after editing templates: install dependencies with `pip install -r requirements.txt`, then run `python scripts/build.py`. This overwrites `rules-prompts.md`.
- **To check formatting and structure**: run `pytest scripts/test_build.py`.

## What is included automatically

Phase 1 (character/setting creation, language, game start, respond to actions), Phase 2 (world creation, coherence), formatting (message #X, location/time, tokens, emojis), and core system actions (@save, @inventory, @quests, @map, @help, etc.) are included from `prompts/common/` for every rule. You only write the **opening**, **mechanics**, and optionally **extra-actions** for your rule set.

## Updating an existing rule set

1. Edit the files in `prompts/rules/<rule-id>/` (e.g. `opening.j2`, `mechanics.j2`, or `extra-actions.j2`). Keep the same structure: opening text first, then mechanics, then extra system actions if any.
2. Run `python scripts/build.py` and `pytest scripts/test_build.py`.
3. Commit both your template changes and the updated `rules-prompts.md`.

## Creating a new rule set

1. Add an entry to `prompts/rules/_index.yaml` with `id`, `title`, and `intro`, in the order you want it to appear.
2. Create a directory `prompts/rules/<new-id>/` with at least `opening.j2` and `mechanics.j2`. Add `extra-actions.j2` if the game has rule-specific commands (e.g. @internal, @vats).
3. Copy content from a similar rule (e.g. D&D or Dice pool) as a starting point; adjust the opening line and mechanics to match the new game.
4. Run `python3 scripts/build.py` and `pytest scripts/test_build.py`; commit the new fragments, the updated `_index.yaml`, and the updated `rules-prompts.md`.

## Fragment templates

Each rule set is built from up to three per-rule files. Use the snippets below as a starting point; see the linked examples for real rule sets.

### opening.j2

One or two short paragraphs: the game-master line and (optionally) scope (e.g. open-world vs. single mystery).

**Examples:** [prompts/rules/dnd/opening.j2](prompts/rules/dnd/opening.j2), [prompts/rules/deduction-detective/opening.j2](prompts/rules/deduction-detective/opening.j2).

<details>
<summary>Template for opening.j2</summary>

```
From now on, you will act as the game master for an interactive role-playing session using [your game system or style].

[Optional: It is an open-world adventure. There is no main plot; instead, the player can move freely and discover individual quests or tasks of greater or lesser importance.]
```

</details>

### mechanics.j2

Game-specific rules: difficulty (or equivalent), how the player rolls, resolution, and guidance. For dice-based games this is often: Difficulty/DC → Player rolls → Resolution → Guide the player.

**Examples:** [prompts/rules/dnd/mechanics.j2](prompts/rules/dnd/mechanics.j2), [prompts/rules/dice-pool/mechanics.j2](prompts/rules/dice-pool/mechanics.j2).

<details>
<summary>Template for mechanics.j2 (dice-based)</summary>

```
Difficulty System and Dice Rolls:

Difficulty: Before the player performs an action with an uncertain outcome, you must assign a [Difficulty Class / Difficulty Level / etc.]. [Define how difficulty is set and what scale you use.]

The Player Rolls the Dice: [Describe how many dice, what counts as a success, and how modifiers work.]

Resolution: If [success condition]: The action is successful. Describe in detail what the player discovers or achieves. If [failure condition]: The action fails. Describe what the player fails to do. It is important not to reveal why they failed.

Guide the Player: If the player gets stuck, you can offer subtle clues or have a non-player character provide information.
```

</details>

For narrative, social, or puzzle-focused games, replace the dice block with the appropriate mechanics (e.g. clues and deductions, relationship checks, or conversation branches). See other rule dirs under `prompts/rules/` for examples.

### extra-actions.j2 (optional)

A bullet list of rule-specific `@` commands. Only add this file if the game has commands beyond the core set (e.g. @pokemon, @dex, @internal, @vats).

**Example:** [prompts/rules/pokemon/extra-actions.j2](prompts/rules/pokemon/extra-actions.j2).

<details>
<summary>Template for extra-actions.j2</summary>

```
- Every time the player says "@command", you must [describe what to generate or do].

- Every time the player says "@other", you must [describe what to generate or do].
```

</details>
