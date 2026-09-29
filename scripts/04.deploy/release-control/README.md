<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.readme.release-control-compatibility
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: readme
purpose: Document the compatibility entry point into the existing operational realization compiler.
portability: {class: reusable, targets: [entity-builder]}
used_by:
- id: deploy.command.release-control-compiler-compatibility
  path: scripts/04.deploy/release-control/compiler.py
-->
# Release compiler compatibility

The reviewed draft at `compiler.py` now delegates to the canonical
[operational-realization gate](../operational-realization-gate/README.md).
There is one compiler implementation and no controller in this directory.

The [discovery collector](discovery/README.md) also lives here because it reads
provider-specific source syntax. It returns safe inventory to the existing
gate's `--discover`/`--coverage` modes; it has no deployment or provider effects.

Use the existing public command:

```bash
npm run deployment:realization:validate -- --release release.yml --contract realization.yml
```

For callers of the draft path, `python3 -B
scripts/04.deploy/release-control/compiler.py release.yml --contract
realization.yml` accepts the positional release filename. Canonical `--release`
arguments also work. The versioned input replaces the incomplete draft shape;
that shape never had a supported acceptance or execution contract. The wrapper
deliberately requires the realization contract and applies the same strict
checks, normalized output and exit status as the public command.

The release-control programme owns this compatibility path. Retire it during
the planned caller/adoption review only after proving no supported caller
remains; do not introduce a second deployment implementation here.
