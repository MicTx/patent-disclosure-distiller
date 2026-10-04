> [!NOTE]
> This mirror is republished from a private development source as a filtered snapshot: each publish rebuilds it as a single commit, so pull requests cannot be merged here. Open an issue describing the problem instead; fixes are ported by the maintainer and appear with the next publish.

## Summary

<!-- One or two sentences: what changes and why. Reference the issue, e.g. "Fixes #123". -->

## How did you test it?

<!-- The exact commands you ran and their output. The regression suite is:
     python3 -m unittest discover -s .agents/skills/patent-disclosure-distiller/tests -v -->

## AI-assistance disclosure

- [ ] This change was written without AI assistance, or the AI contribution is described below (tool/model, what it wrote, how I verified it)

## Checklist

- [ ] Regression suite passes: `python3 -m unittest discover -s .agents/skills/patent-disclosure-distiller/tests -v`
- [ ] `validate → generate → validate` still passes for `examples/map-preload/package.json`
- [ ] No claim of unverified effects, legal conclusions, or experiment results was added — content keeps `[Q]`/`[I]` where evidence is missing
- [ ] Schema or pipeline behavior changes are reflected in `references/pipeline.md`
