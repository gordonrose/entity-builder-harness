import { spawnSync } from "node:child_process";
import { join } from "node:path";
import { loadWorkspaceGraph, selectWorkspaceProject } from "../../../../../../scripts/repo/workspace-build/declarations.mjs";
import { prepareWorkspaceRuntime } from "../../../../../../scripts/repo/workspace-build/runtime-packages.mjs";

const runtimeRoot = ".cache/platform-adapter-aws-persistence-postgresql-integration";
const repository = process.cwd();
const selection = { roots: [selectWorkspaceProject(loadWorkspaceGraph(repository), "platform/adapters/aws/persistence/postgresql/tsconfig.integration-test.json")], includeRootDevDependencies: true };
prepareWorkspaceRuntime({ repository, compiledRoot: runtimeRoot, selection });

const result = spawnSync(
  process.execPath,
  [join(runtimeRoot, "platform/adapters/aws/persistence/postgresql/tests/integration/postgresql-persistence-adapter-integration.test.js")],
  { stdio: "inherit", env: process.env },
);

process.exitCode = result.status ?? 1;
