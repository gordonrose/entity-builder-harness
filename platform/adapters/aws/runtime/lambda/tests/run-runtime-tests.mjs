import { spawnSync } from "node:child_process";
import { loadWorkspaceGraph, selectWorkspaceProject } from "../../../../../../scripts/repo/workspace-build/declarations.mjs";
import { prepareWorkspaceRuntime } from "../../../../../../scripts/repo/workspace-build/runtime-packages.mjs";

const repository = process.cwd();
const compiledRoot = ".cache/platform-adapter-aws-runtime-lambda-runtime";
const selection = { roots: [selectWorkspaceProject(loadWorkspaceGraph(repository), "platform/adapters/aws/runtime/lambda/tsconfig.runtime-test.json")], includeRootDevDependencies: true };
prepareWorkspaceRuntime({ repository, compiledRoot, selection });
const result = spawnSync(process.execPath, ["--test", `${compiledRoot}/platform/adapters/aws/runtime/lambda/tests/contract/lambda-dispatch-runtime.test.js`], { stdio: "inherit" });
process.exitCode = result.status ?? 1;
