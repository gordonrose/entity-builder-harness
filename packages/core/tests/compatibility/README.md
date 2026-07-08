# packages/core Compatibility Fixtures

This directory contains compile-only canaries for old public `packages/core`
usage patterns.

These files should keep compiling unless a public contract break is deliberate,
documented, and paired with migration guidance in the core architecture source
material and rule projection.

Keep fixtures boring: import from the public core entry point, model realistic
app or platform usage, and avoid provider SDKs, product workflows, or runtime
hosts.
