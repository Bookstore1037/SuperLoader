# Connector issue drafts — archived, not to be filed

> **Status: archived on 2026-11-06.** Connector upstream states that 1.21.1 no longer receives compatibility fixes:
> *"As our LTS support target, 1.21.1 will no longer receive new compatibility fixes. Please upgrade to the latest version for mod
> compatibility support."* Filing these would only produce "won't fix for 1.21.1".
>
> Keep them as (a) a precise record of the L2 failures we hit on 1.21.1 and (b) reference samples if the stack ever moves to 26.x.
> Do **not** spend time uploading logs or submitting unless the target version changes.

One issue per mod, all English, in the exact field order of
[`.github/ISSUE_TEMPLATE/mod_incompatibility.yml`](https://github.com/Sinytra/Connector/blob/26.2.x/.github/ISSUE_TEMPLATE/mod_incompatibility.yml)
(`🚧 Incompatible Mod / Crash`, type `Compat`).

Each draft is self-contained: a maintainer who cannot see this machine has everything they need in the body (crash line, both annotation
variants, bytecode evidence, minimal set). No local paths, no references to internal notes.

**The only thing left to fill in is `### Logs`**, where `<link>` must become a paste-site URL — the template does not accept file
uploads. Files ready to drag are in [uploads/](uploads/) (renamed per case so they do not overwrite each other in the browser).

## Files

| # | draft | mod | failure stage | layer | related existing issue |
|---|-------|-----|---------------|-------|------------------------|
| 1 | [01-replaymod.md](01-replaymod.md) | ReplayMod 2.6.28 | world join / GUI render | L2 (mixin annotation rewrite) | none open for this crash; #556 is the general ReplayMod thread |
| 2 | [02-minihud.md](02-minihud.md) | MiniHUD 0.32.60 (+ MaLiLib) | Bootstrap (class load) | L2 (NeoForge method-body rewrite) | #2258 open (different crash — cross-reference it) |
| 3 | [03-bumblezone.md](03-bumblezone.md) | The Bumblezone 7.17.3 | jar transform (before mod load) | L2 (Connector adapter NPE) | none |
| 4 | [04-farmers-delight-refabricated.md](04-farmers-delight-refabricated.md) | Farmer's Delight Refabricated 3.3.6 | mod load | L2 (NeoForge parameter-type change) | #2304 open but 26.1.2 + different symptom |
| 5 | [05-friends-and-foes.md](05-friends-and-foes.md) | Friends & Foes 5.0.4 (Fabric) | mixin attach | L2 (enum extension vs enum mixin) | none |
| 6 | [06-language-reload.md](06-language-reload.md) | Language Reload 1.7.6 | runtime (`charTyped`) | L2 (Language patch ordering) | none |

## Before submitting (template rules)

The template explicitly rejects reports that do not meet these conditions:

1. **Latest Connector + dependencies.** We are on `2.0.0-beta.17+1.21.1`, the newest 1.21.1 build.
2. **Minimal mod set.** All six have been replayed with only Connector + Forgified Fabric API + the mod (and its Fabric dependencies);
   the crash reported in each draft is the one that came out of that run.
3. **Does not occur on Fabric.** These are Fabric-native mods. Where a NeoForge build exists (Friends & Foes, Farmer's Delight) the
   NeoForge build works and the Fabric one is the failing one.
4. **Logs via paste site.** Upload `debug.log` and the crash report, put the links into `### Logs`.

## Files to upload

| case | upload |
|------|--------|
| 01-replaymod | `uploads/01-replaymod-debug.log`, `uploads/01-replaymod-crash-report.txt` |
| 02-minihud | `uploads/02-minihud-debug.log`, `uploads/02-minihud-crash-report.txt` |
| 03-bumblezone | `uploads/03-bumblezone-debug.log`, `uploads/03-bumblezone-crash-report.txt` (the report is the FML summary page; the real cause is only in `debug.log`) |
| 04-farmers-delight-refabricated | `uploads/04-farmers-delight-refabricated-debug.log`, `…-crash-report.txt` |
| 05-friends-and-foes | `uploads/05-friends-and-foes-debug.log`, `…-crash-report.txt` |
| 06-language-reload | `uploads/06-language-reload-debug.log`, `…-crash-report.txt` |

Fill the links in with:

```
python tools/set_issue_logs.py 01-replaymod https://mclo.gs/xxxx https://mclo.gs/yyyy
```

## Evidence appendix

`compat/connector-issues.md` keeps the Chinese working notes behind these drafts (raw annotations, mapped-jar annotations, NeoForge
bytecode offsets, jar hashes). It is local-only on purpose: the drafts do not depend on it.
