#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.source-transition
#   version: 2
#   status: draft
#   created_on: "2026-11-11"
#   updated_on: "2026-11-26"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Validate retained administrator-recovery history and compatibility while rejecting its retired image-transition executor.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
import hashlib
import json
import re
from types import SimpleNamespace

LABEL = "entity-smoke-8f76ed3480e85d60fb60f547"
RETIRED_PROOF_LABEL = LABEL
OLD_SOURCE = "8f76ed3480e85d60fb60f547f996628c8554504d"
OLD_IMAGE = "sha256:282b3b2a4dab14df45cc7433c9d52ad30a8a4ea61ba1353d861c487b5251c0ac"
FAILED_PREFLIGHT = "es-cfa256731b854baeb1e1427fd94cb01f"
PINS = {
    "54e1f8035f6c1cf1404ce685193d0e5e141bee0856ee726afe239581f93c8cb3": ("9c66ffe83e80692c301e98c7bd89b158c4b675e58c1e011eee7ebb3f48778c30", "ae545968c53e005e223320e805967c95209b7a96d764257e3b537cb4adce9903"),
    "c048875837a67e77371278a31ee77600e53f7b8633c1dffcfd51445576f916f4": ("2e77bb18ed5b82574a04d69e4b4b5df522c5749edf4670c35bf104e78a2982f1", "ae545968c53e005e223320e805967c95209b7a96d764257e3b537cb4adce9903"),
    "d5ed43c61fa2179b4c46cc8326e83c6bcdf9f38a7a8e5b643ef16a1125f999db": ("626dd88cd876e4d8e969c713fa783eda4340c35042f89a2959e6a8e6ba27ba79", "20373db2f9f42a0a63f5948c14d587343161b4666f225f32818a937300a742c8"),
    "b7f6b2db5eaef57d82088aee602102a4283698bc60dc817a4df44ffe06c69da5": ("0390d89072d1a0a0493d662d9cf06d9931c0ddbeb1dc3a4928ed2bbed07e4311", "20373db2f9f42a0a63f5948c14d587343161b4666f225f32818a937300a742c8"),
}
TASK_DEFINITIONS = {name + "TaskDefinition" for name in ("Server", "Migration", "Administration", "Verifier", "DatabaseProof")}
# Exact successful grant/permissions custody before controller-only repairs.
# These already use the current qualified image, not OLD_IMAGE.
CONTROLLER_REPAIR_PINS = {
    "62a5836895aefd79c277c6e26afa80fce5dd78a2dd980016aacba02b39d95216": ("157b62e23169a40e691bfde41ce50b557142ed2dfc8c3702a5db801555495589", "3d3a9818b84ee8174f4d7bc4caa59e898629c124277eca03768d683c55fd29a1"),
    "625fa6adfb7c585a6df84f6b645e7fe430f2317c246e75eb5e21c3931b83d489": ("e5428c0a242c063e34ecafa59477bf325fdf7c506f45095e62d82b011552ae41", "2f07f14b598ee22cfd9b1ab8980ef990f06ed43d1301bda848bf75934daa9f4c"),
    "b82bc6487a8a3d24024aeeb4ef8fd21d931d25dc9a94d2dfb6c0100ad6dba689": ("c8b7d8d9043dac48de128c8d6bc6483fadc06dd7d53222e2beabdc9d725e86fc", "2f07f14b598ee22cfd9b1ab8980ef990f06ed43d1301bda848bf75934daa9f4c"),
    "f86edfe5bb0a57bc58a28a659b86f1377800c8472fe0f9a2327f7c8ed9440607": ("ed3f465366f0ed09287e4f3e5d0a7d4770164c3ae3da58949abf3a75b33a121d", "1a4f5abbf42a6771fa410981768887cd5f9ebdb02031d046dcad8c8119ad6457"),
    "a12aaa5258ec59d35496c9fe26f1334d105cd90fb666d674865052b7818f43e1": ("dbe4ad4be0dae5ce91174dd302e0ed2bf074c31a69477f359ebe262e5160b59d", "1a4f5abbf42a6771fa410981768887cd5f9ebdb02031d046dcad8c8119ad6457"),
    "612094606ecf7473081c093246a7ae61c7d2df9ffbd72693f7d7deb9c5ff67d9": ("c8731dc47b6aa65aec390a130e7aa8c0a6e088271d895a3197bbbe49c81af09b", "e022fa391f24fa326a4ba5b9b6193fff7c587045525fb758e3935b7394cbad9b"),
    "05af75adfe08f3678dd6226494a436779806c3642ce2d6408b850fa3feaa4284": ("10e7a3a35ed89ee94bc1632704f942ba21bcb567553b0f88a10c2676993bdf9f", "e022fa391f24fa326a4ba5b9b6193fff7c587045525fb758e3935b7394cbad9b"),
    "c0af84a06e80fc03010c60c8bf8abe49980d1790e1a034996a22778378dc36d1": ("23f50cc110485a0af00bca7024a73658b05c0630ca4d3bebbe0088a767c5c06b", "e022fa391f24fa326a4ba5b9b6193fff7c587045525fb758e3935b7394cbad9b"),
    "b4fe8cc8c7851aeda1ff4c14256efd0dcb7923458aba7aa703bd8965213454df": ("cba93ec274658450f98a4b8158e846b88345ffa8acaa08e581edd8a4abc0b7b5", "e022fa391f24fa326a4ba5b9b6193fff7c587045525fb758e3935b7394cbad9b"),
    "fb8995433ced8601ffa5492afe013c391be778d5ca2aff5dcc98858572a54c95": ("d2a40f89c6692d255caec08aeed64ea580d25980efd0136a1b87c1ded222c192", "73972bbe0d009d57bf81353056b407b424b7f67c78f1355915c89422cfe20d76"),
    "33be6d1b5c712f12a43c28dc40b2373c15aea4d140a07fb25c6c3959dbd736ad": ("e6a7800a15d0b815b857739c94014829e848aa5ec28dc4d1e504903c58042625", "73972bbe0d009d57bf81353056b407b424b7f67c78f1355915c89422cfe20d76"),
    "4c9fa83aca658fa9e38c4239872f8213bbf805042710609e509159c42692007d": ("252b3eebf5ef44f91051a8d92a0216ee106224a2acc72be95ac22eed9fc8d264", "73972bbe0d009d57bf81353056b407b424b7f67c78f1355915c89422cfe20d76"),
    "ec9eea404148f7374c77ec9784ba43e0f45b58800c954ad6ee89c17292763bbf": ("cab5a67784c3c51ac65f050216eb434b037bb0efcb9e2b022685b102b59ae011", "73972bbe0d009d57bf81353056b407b424b7f67c78f1355915c89422cfe20d76"),
    "41428e9d5fa8b8d3e25e87eb187c54c85fbd5eb88aa430d7839af7a391851b9d": ("9f0a8fd796cda4520f346a919e092528aa61c45b49da5e9eceb79123cdfc1dd0", "73972bbe0d009d57bf81353056b407b424b7f67c78f1355915c89422cfe20d76"),
    "e10473d6c5ebc0bb33e042eb46ccef404e380f323da9a877e72f10cb72abb710": ("19b55df23869b6c15c3d1aa7e8c085f69ec6c90fae3ab09df859dbf46fd3ea5a", "73972bbe0d009d57bf81353056b407b424b7f67c78f1355915c89422cfe20d76"),
    "e004fc0e288df46b0e4fc258190f90e9ea305718c55d6c6a10bb027ff8673d9f": ("b057d31f2961ba81a970895141caf67d371f643ca7d43475194c508fd2f86f92", "73972bbe0d009d57bf81353056b407b424b7f67c78f1355915c89422cfe20d76"),
    "07d957062f64c99a5865f83b4e335f7fe79e48b7c774bfb1976f144a7b225a99": ("f95170628ce680b472f6686f31c21d7acd5316afc4e25201490bae81d8a775f5", "73972bbe0d009d57bf81353056b407b424b7f67c78f1355915c89422cfe20d76"),
    "a23a9a795be66bd18b81df262fdaec8cf8422537d78a331277ca3cfe7909fb46": ("d4e600bedd72727da84d4a25df06c68cafe58ff10ca591034701307bdd6d38f0", "73972bbe0d009d57bf81353056b407b424b7f67c78f1355915c89422cfe20d76"),
    "65e5caedc468e695ff76a9bfb2e22aa03f6a86f455d3af314cae937cbff80600": ("af38a97d81cc6290022018a6638c2c255fec6d8a5df390ddc8094922debce26f", "73972bbe0d009d57bf81353056b407b424b7f67c78f1355915c89422cfe20d76"),
    "cc54216f376d48a61d7819e4bc8f01020ab9cefc853f0a73d7bb1cc85b2caa0e": ("8c1b2c14bf88bb17c71a5417c3639ab761c9484d787421cf3b87013823ecbeb5", "4efd5bafb39ecea7173f3a6622b6a7d37d1dadc5d4d9bb12e19dd190ed490091"),
    "9743ae4553d93a135b9433f0676f9abd45cd0e499fe2a8f8912ea571de71dbae": ("b35f2942fc879ec357de2f074c77621e51d32d783238418670bee8230998ccd1", "4efd5bafb39ecea7173f3a6622b6a7d37d1dadc5d4d9bb12e19dd190ed490091"),
    "64b4810e796333e67039af4130be627046063b342ee0ea9f3f7602e26ecb5501": ("c2c00a42e398a9bcf02b1c1558a4d3064ff90e1680372a770337fd4dea4b41a6", "4efd5bafb39ecea7173f3a6622b6a7d37d1dadc5d4d9bb12e19dd190ed490091"),
    "fecb3d313f7d157f59fb90012339fea8bd4ea1a7dc785ee489acce87797bbac3": ("f46b3076bdbe0abf011f37c1df8a84c602c1510cf603ac3bdd38a9ee4542d5a0", "7730ae5eb2e8e72c75cb4bbc7bfa100250582345c1fa9ead29713a20de0e8f15"),
    "4dc28dca67cd3a33a8bf53077c818fcf97a873d9648ff07c821eca8ac81895c5": ("b17cf62b770e0de7767103f3e003bf8c5488df74f2b22e475eaa5dd5b314c8f0", "7730ae5eb2e8e72c75cb4bbc7bfa100250582345c1fa9ead29713a20de0e8f15"),
    "ec4a2353fd182ffa6ea8379e09af5de537da99b12023fec6dc2caca477faf873": ("0b1d384938cb232bb25e2bc1ac2eeee783f0eac08f690a994c016dfa85ad8ad7", "8db4387e1bd8c592883644ea91a155272c70e42d2e17eb740756b40772862c8d"),
    "87662ce19ee938ed333b87f93bdbe9ae3e8945c5c5f9cbc3f731dffb4d1512b2": ("33b827867da2c170a4b0e1099ee7186ba790f625202fba2cf0190ef9267ed0f6", "8db4387e1bd8c592883644ea91a155272c70e42d2e17eb740756b40772862c8d"),
    "24e4623c020bedf999b968d289a12232a1693b721e71f68089a68da48243fccf": ("8785f7165f2b205509b1fd7fcd11d9245fde37c7bc6d3a1907221769fae95230", "8db4387e1bd8c592883644ea91a155272c70e42d2e17eb740756b40772862c8d"),
    "3803b6162189d6b3e168833c9c6579700eb8ce4a899a5fc4218c811a2a125cb3": ("cc124a43eea82f9c3b9ab2529dab923639cbd4eb619b76d3291f98747470a91e", "8db4387e1bd8c592883644ea91a155272c70e42d2e17eb740756b40772862c8d"),
    "18edb5427b0e6883152f4583e3b22dcc4449a5af274e721004cb20ffd7311d8e": ("606887188a43b4581696ee9924d789aa878a2e2acf9ba46e942fa24dd2a3cbd1", "8db4387e1bd8c592883644ea91a155272c70e42d2e17eb740756b40772862c8d"),
    "fccbb75f4b2a73da6ed8582efcdc049bdb3729f9d964383390b62ef7460e77ff": ("ce2a6122c75b8cbe0b5178a57f14ad081dd37b42232df7c863ee66b84e0e78be", "3e8b6d53bd794833c308e6ebb318def7442d56017932900f78304ce4539ca9a9"),
    "d0bd1010709a93f6ea9140ef04a3ab072f958e54173a4f380d6414abb621bbe7": ("cf569f98859027efefc6903d526509d4f620336dd93dc77b36d29976a21a7674", "3e8b6d53bd794833c308e6ebb318def7442d56017932900f78304ce4539ca9a9"),
    "a16c5478379bd82a66f081d48a3a690850ab1fe5ce1124142ebbbf640b285c46": ("a54d8e4f58e0d6179bc8128a511b551e3c50652e1aacd1a5af2b98c80a4bfd91", "3e8b6d53bd794833c308e6ebb318def7442d56017932900f78304ce4539ca9a9"),
    "2bbbbb32aec9a3f67af515523271e40431429b67b2a864f44cad9c9551a2dc96": ("5cdf789860c3a4895a8f42838cacb667d1938685235232caa74c0ac4f7b47163", "3e8b6d53bd794833c308e6ebb318def7442d56017932900f78304ce4539ca9a9"),
    "725c8d91dbdeb03ba2af0d7d6986cd99bc5a03c67160830e853edf4a6fddc794": ("6bdafce7582bb9dc7de6c6c40cfc163a3419e17cb7572b2501dfeb345a8eb45b", "3e8b6d53bd794833c308e6ebb318def7442d56017932900f78304ce4539ca9a9"),
    "e66842a43431dd9a738752263f5520a81640bfb078e9bdeafa4b88d0142993f3": ("78cfaa909d7ee998c4aee92c7d2e9431ad4a427548c3616d2d4e40f0bd6c798a", "d78b850e6f2208fa8d17ce69c160024c479fec33c59b05ae6ced47f13bc269a8"),
    "f1db111a594a4f16a42029dd6ab0542801b9d9e37c55d5d621d8b9875b23ec21": ("c7d3eca3949d61b38907de25aecd57a0e1a30d9f91b53d4f9d49ffc3fd106a27", "d78b850e6f2208fa8d17ce69c160024c479fec33c59b05ae6ced47f13bc269a8"),
    "6bdd329d5e4f0d17927634945e5a4dfe62af8b1f1c63543f6562ed39e8f1c1ff": ("435c4e9c532bfa420ff43259be725cd3b9b73bd78d3425e03bc9427168aa1caa", "cdf63a0df5c0d09263e8be7a083a7c908a4b3bdea7713150292c453e6a1c9bfd"),
    "02a2ecd3110ff3fdf71d2b482be3f60d586674240c4727d53dd5edd4796619ec": ("8ae4f77b9f669e1220f498e4b98e5c7f659e06f7d5f619d259c290a817f7ba4e", "cdf63a0df5c0d09263e8be7a083a7c908a4b3bdea7713150292c453e6a1c9bfd"),
}
UNSUBMITTED_PREFLIGHT = "es-8c2a5ae0be9e4090b2aa38c324592f46"
UNSUBMITTED_REPORT = ".cache/test-runs/entity-smoke-stable.7wpnDKuN/finish-task-execute-7a7e118e3ef9493f98eb24f93fd064f6.json"
UNSUBMITTED_REPORT_HASH = "sha256:e17a09ab60e17680486e5c6b45dd22602c70a848512c96032e3b188c5b31cd52"
UNSUBMITTED_RESERVATION_HASH = "sha256:b952cb026b1600eb1ea46cd8e9f37a5e58c9130c604ff8776c90e9149be6ee15"
COLLISION_PROBE = "es-d8eb01dcede146719f91b8dd16278882"
COLLISION_PACKET = "sha256:725c8d91dbdeb03ba2af0d7d6986cd99bc5a03c67160830e853edf4a6fddc794"
COLLISION_COMPLETION = "sha256:6bdafce7582bb9dc7de6c6c40cfc163a3419e17cb7572b2501dfeb345a8eb45b"
COLLISION_FAILURE = ".cache/test-runs/entity-smoke-stable.7wpnDKuN/finish-task-execute-fbb4b5379f72404498c8b52029deed90.json"
COLLISION_FAILURE_HASH = "sha256:fab39feb1d9a14f8cc3512a6b40fca4173a5d5372071e07c52574c9601ac60f4"
REPLACEMENT_PROBE = "es-9f8bba57dbba435881194887c95894aa"
REPLACEMENT_PACKET = "sha256:18edb5427b0e6883152f4583e3b22dcc4449a5af274e721004cb20ffd7311d8e"
REPLACEMENT_COMPLETION = "sha256:606887188a43b4581696ee9924d789aa878a2e2acf9ba46e942fa24dd2a3cbd1"
REPLACEMENT_FAILURE = ".cache/test-runs/entity-smoke-stable.7wpnDKuN/finish-task-execute-48877f792d464fedbca502de7a93a70a.json"
REPLACEMENT_FAILURE_HASH = "sha256:093022ee1b8b513b9f9517ad4e30d2d30a0bdb5770f59be97bc28abc29d33348"
HISTORY_PROBE = "es-bea613cae49e429697a780cd3d5de244"
HISTORY_PACKET = "sha256:64b4810e796333e67039af4130be627046063b342ee0ea9f3f7602e26ecb5501"
HISTORY_COMPLETION = "sha256:c2c00a42e398a9bcf02b1c1558a4d3064ff90e1680372a770337fd4dea4b41a6"
HISTORY_FAILURE = ".cache/test-runs/entity-smoke-stable.7wpnDKuN/finish-task-execute-ba3f7a648fce4dafbab63285797f2402.json"
HISTORY_FAILURE_HASH = "sha256:d51de3649c43f77651463e667bb907195d407e2743cf1c6d5e8a1c5b2875b5f7"
CREDENTIAL_PROBE = "es-b72f7c07746d4fdb8a086df46f5cf7f2"
CREDENTIAL_PACKET = "sha256:a23a9a795be66bd18b81df262fdaec8cf8422537d78a331277ca3cfe7909fb46"
CREDENTIAL_COMPLETION = "sha256:d4e600bedd72727da84d4a25df06c68cafe58ff10ca591034701307bdd6d38f0"
CREDENTIAL_FAILURE = ".cache/test-runs/entity-smoke-stable.7wpnDKuN/finish-task-plan-7200236746314bd1a6128b0fc985cc15.json"
CREDENTIAL_FAILURE_HASH = "sha256:aa23ea2ce53e67eed66b5fa0990490a0d4dffd12c3292cb49da91b06140e4d1f"
RESTORE_PROBE = "es-7718c551963245a899c9f1421dc84d5c"
RESTORE_LABEL = LABEL
RESTORE_FAILURE = "diagnostics/restore-reader-preflight-" + RESTORE_PROBE + ".json"
RESTORE_FAILURE_HASH = "sha256:6e9ffd437275f3e23f308587ef2483ad069686afea8843f21d98fc70bb050ae0"
CLEANUP_LABEL = LABEL
CLEANUP_PLAN_HASH = "sha256:3950b70bb6eb1de7c130f4a9e2ebd1e3fc978a954d2777f12195ec612305eaff"
CLEANUP_FAILURE = ".cache/test-runs/entity-smoke-stable.7wpnDKuN/finish-restore-e00dd39c9de542d1900bcbc4b7007789.json"
CLEANUP_FAILURE_HASH = "sha256:240ca1fe8a0572f0f79c9bda55ae5bd9118ecdc44c91f27d1a7012c066a5e553"
CLEANUP_RECONCILE_PLAN = "sha256:836a81adcd0eb1e8ee39b8164f6fba1d45c30b46efe732e6c22d3bb4c1979979"
CLEANUP_RECONCILE = {
    "plan": ("restore-cleanup-plans/836a81adcd0eb1e8ee39b8164f6fba1d45c30b46efe732e6c22d3bb4c1979979.json", "sha256:1ac6f5a45d807749ba49b33e0aa52aa30dccf2581ee69de03af1fe43fdd1e62f"),
    "reservation": ("attempts/" + LABEL + "-delete-restore.json", "sha256:48ae916ea53cca1cd08ad1a53181544ee4d7b2f6c6e41822895cb2b9fc775392"),
    "gate": ("restore-cleanup-realization/execution-preflight-ba2adae99830468f839834c5831e0c8f.json", "sha256:ffdeac82397aac254dca8923e051c2409a1b4d46300aff124bbbd22b702f2498"),
}
CLEANUP_RECONCILE_FAILURE = ".cache/test-runs/entity-smoke-stable.7wpnDKuN/finish-restore-4fda0a72ead942ef8a495cbb57349a39.json"
CLEANUP_RECONCILE_FAILURE_HASH = "sha256:02e58b3158189a30bf9acd40aad57902d152b15db22c36f1c01d7e9219775022"
ACCEPTANCE_REFRESH_LABEL = LABEL
ACCEPTANCE_RENEWAL_LABEL = LABEL
ACCEPTANCE_PROBE = "es-02963945b7784b11a3366f46d8c6d3f9"
ACCEPTANCE_PACKET = "sha256:62a5836895aefd79c277c6e26afa80fce5dd78a2dd980016aacba02b39d95216"
ACCEPTANCE_COMPLETION = "sha256:157b62e23169a40e691bfde41ce50b557142ed2dfc8c3702a5db801555495589"
ACCEPTANCE_FAILURE = ".cache/test-runs/entity-smoke-stable.7wpnDKuN/finish-task-execute-13d3dae7310542d4886217c36a4ed8f2.json"
ACCEPTANCE_FAILURE_HASH = "sha256:953a82faddf6df2b24b83b64fb46db89c82abc04f3feef9ca07619a3aec42725"
ACCEPTANCE_REFRESH_CONTROLLER = "sha256:2f07f14b598ee22cfd9b1ab8980ef990f06ed43d1301bda848bf75934daa9f4c"
ACCEPTANCE_REFRESH_FAILURE = ".cache/test-runs/entity-smoke-stable.7wpnDKuN/finish-collect-acceptance-3d5f9bd455ba4b30865c7717172f550c.json"
ACCEPTANCE_REFRESH_FAILURE_HASH = "sha256:ade8a64f7e28862eb00d2430fd4b5cf8dd98ce54780a6cc463acc654f131cc81"
ACCEPTANCE_REFRESH_INPUTS = {
    "preflight": ("task-steps/verifier-read-acceptance-preflight.json", "sha256:625fa6adfb7c585a6df84f6b645e7fe430f2317c246e75eb5e21c3931b83d489", "sha256:e5428c0a242c063e34ecafa59477bf325fdf7c506f45095e62d82b011552ae41"),
    "operation": ("task-steps/verifier-read-acceptance-operation.json", "sha256:b82bc6487a8a3d24024aeeb4ef8fd21d931d25dc9a94d2dfb6c0100ad6dba689", "sha256:c8b7d8d9043dac48de128c8d6bc6483fadc06dd7d53222e2beabdc9d725e86fc"),
}
RECOVERY = {
    "administrator-recovery/validated/result.json": "9adfdc13e471d1c12839af34d6f5d0ac4d136d367c45ea3f68e34c910b07a727",
    "administrator-recovery/validated/temporary-access-removed.json": "78793d7a4addfc11a4b3045ad3feed4eb2bb009d2600533e1da7ebf591db83d6",
}


def document(value):
    return hashlib.sha256((json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()).hexdigest()


def require_existing_attempt(C, proof_label, reservation):
    """Incident selectors may read original attempts, never launch new ones."""
    C.require(proof_label != RETIRED_PROOF_LABEL or reservation is not None,
              "incident-proof-new-attempt-retired")


def cleanup_reconciliation(C, cache, binding, request, store, declaration):
    """An observer-only successor links the actual old submission and six gates."""
    failure_path = C.ROOT / CLEANUP_RECONCILE_FAILURE
    C.RESOURCE.CONTROL.no_symlinks(failure_path)
    if binding["proof_label"] != CLEANUP_LABEL or not failure_path.exists(): return None
    C.require(C.digest_file(failure_path) == CLEANUP_RECONCILE_FAILURE_HASH, "restore-cleanup-reconciliation-failure-changed")
    failure = C.read_json(failure_path)
    C.require(failure.get("schema") == "deploy/entity-smoke-restore-report/v1" and failure.get("verdict") == "blocked"
              and failure.get("effect") == "original-restore-operation-reconcile-only" and failure.get("condition") == "restore-cleanup-observation-unavailable"
              and failure.get("context") == {"mode": "execute", "phase": "cleanup", "proof_label_sha256": hashlib.sha256(CLEANUP_LABEL.encode()).hexdigest()},
              "restore-cleanup-reconciliation-observation-required")
    retained = {}
    for name, (relative, digest) in CLEANUP_RECONCILE.items():
        path = cache / relative
        C.require(C.digest_file(path) == digest, "restore-cleanup-reconciliation-custody-changed")
        retained[name] = C.read_json(path)
    original, reservation = retained["plan"], retained["reservation"]
    declaration = C.GRAPH.retained(C, declaration, graph_sha256=original["plan"].get("graph_sha256"))
    C.require(original.get("request") == request and original.get("plan_sha256") == CLEANUP_RECONCILE_PLAN
              and C.DEPLOY.fingerprint(original["plan"]) == CLEANUP_RECONCILE_PLAN and original["plan"].get("binding") == binding
              and original["plan"].get("graph_sha256") == C.DEPLOY.fingerprint(declaration)
              and store.read("delete-restore", request) == reservation, "restore-cleanup-reconciliation-original-mismatch")
    completion = C.module("entity_smoke_cleanup_original_admission", C.DIRECTORY / "task-execution/implementation/task-completion.py")
    completion.validate_gate(SimpleNamespace(C=C, STEPS=SimpleNamespace(require=C.require)), declaration, retained["gate"], CLEANUP_RECONCILE_PLAN,
                             {declaration["artifacts"][0]["id"]: original["plan"]["controller_sha256"]}, through="execution-preflight")
    summary = retained["gate"].get("change_summary")
    C.require(isinstance(summary, dict) and summary.get("operation_counts") == {"create": 0, "update": 0, "delete": 8, "replace": 0, "broaden-permission": 0}
              and summary.get("input_sha256") == C.GATE.evidence_bindings(declaration, retained["gate"]["facts"])["gates"]["change-set"],
              "restore-cleanup-reconciliation-change-summary-invalid")
    C.require(C.RESOURCE.timestamp(retained["gate"]["facts"]["gate_evidence"][-1]["timestamp"]) <= C.RESOURCE.timestamp(reservation["reserved_at"]),
              "restore-cleanup-reconciliation-admission-order-invalid")
    return CLEANUP_RECONCILE_PLAN


def cleanup_plan_path(C, cache, packet, store, declaration=None):
    """Keep the rejected unsubmitted plan; select only its controller repair."""
    original = cache / "restore-cleanup-plan.json"
    C.RESOURCE.CONTROL.no_symlinks(original)
    if not original.exists() or C.read_json(original) == packet: return original
    if packet["plan"]["binding"]["proof_label"] != CLEANUP_LABEL: return original
    C.require(C.digest_file(original) == CLEANUP_PLAN_HASH, "restore-cleanup-repair-original-plan-changed")
    before = C.read_json(original)
    retained = cache / "restore-cleanup-plans" / (before["plan_sha256"].removeprefix("sha256:") + ".json")
    C.require(C.digest_file(retained) == CLEANUP_PLAN_HASH, "restore-cleanup-repair-original-plan-changed")
    failure_path = C.ROOT / CLEANUP_FAILURE
    C.require(C.digest_file(failure_path) == CLEANUP_FAILURE_HASH, "restore-cleanup-repair-failure-changed")
    failure = C.read_json(failure_path)
    C.require(failure.get("schema") == "deploy/entity-smoke-restore-report/v1" and failure.get("verdict") == "blocked"
              and failure.get("effect") == "not-started" and failure.get("condition") == "restore-reader-task-definition-not-confirmed"
              and failure.get("context") == {"mode": "execute", "phase": "cleanup", "proof_label_sha256": hashlib.sha256(CLEANUP_LABEL.encode()).hexdigest()},
              "restore-cleanup-repair-not-unsubmitted")
    adjusted = {**before, "plan": {**before["plan"], "controller_sha256": packet["plan"]["controller_sha256"]}, "plan_sha256": packet["plan_sha256"]}
    reconciliation = packet["plan"].get("reconciles_plan_sha256")
    if reconciliation is not None:
        C.require(reconciliation == cleanup_reconciliation(C, cache, packet["plan"]["binding"], packet["request"], store, declaration),
                  "restore-cleanup-reconciliation-reference-invalid")
        adjusted["plan"]["reconciles_plan_sha256"] = reconciliation
    C.require(adjusted == packet and packet["plan_sha256"] == C.DEPLOY.fingerprint(packet["plan"]), "restore-cleanup-repair-intent-changed")
    corrected = cache / "restore-cleanup-plans" / (packet["plan_sha256"].removeprefix("sha256:") + ".json")
    C.RESOURCE.CONTROL.no_symlinks(corrected)
    if not corrected.exists() and reconciliation is None:
        C.require(store.read("delete-restore", packet["request"]) is None, "restore-cleanup-repair-already-reserved")
    return corrected


def controller(packet, completion, current):
    pinned = (PINS | CONTROLLER_REPAIR_PINS).get(document(packet))
    return "sha256:" + pinned[1] if pinned and document(completion) == pinned[0] else current


def historical(packet, completion):
    return controller(packet, completion, None) is not None


def compatible(C, before, after):
    C.RESOURCE.validate_binding(before, record_required=False)
    C.RESOURCE.validate_binding(after, record_required=False)
    C.require(before["source_revision"] == OLD_SOURCE and before["image_digest"] == OLD_IMAGE
              and before["proof_label"] == after["proof_label"] == LABEL
              and before["source_revision"] != after["source_revision"] and before["image_digest"] != after["image_digest"]
              and all(before[key] == after[key] for key in before if key not in {"source_revision", "image_digest"}), "source-transition-binding-incompatible")


def validate(C, value, binding):
    C.require(isinstance(value, dict) and set(value) == {"schema", "plan", "plan_sha256", "resources", "terminal_token", "completed_at", "graph", "gate"}
              and value["schema"] == "deploy/entity-smoke-source-transition/v1", "source-transition-receipt-invalid")
    plan = value["plan"]
    C.require(isinstance(plan, dict) and value["plan_sha256"] == C.DEPLOY.fingerprint(plan)
              and plan.get("binding") == binding and plan.get("desired_count") == 0
              and plan.get("automatic_retry") is False, "source-transition-plan-mismatch")
    compatible(C, plan["previous_binding"], binding)
    before, after = plan["resources"], value["resources"]
    C.require(set(before) == set(after) == set(C.DEPLOY.RESOURCE_TYPES), "source-transition-resource-set-invalid")
    for name, row in before.items():
        C.require(row["type"] == after[name]["type"] == C.DEPLOY.RESOURCE_TYPES[name]
                  and (row == after[name] if name not in TASK_DEFINITIONS else row["physical_id"] != after[name]["physical_id"]), "source-transition-resource-identity-invalid")
    C.require(value["terminal_token"] == "es-source-execute-" + value["plan_sha256"][7:39], "source-transition-terminal-token-invalid")
    C.RESOURCE.timestamp(value["completed_at"])
    declaration = C.GRAPH.retained(C, graph(C), graph_sha256=C.DEPLOY.fingerprint(value["graph"]))
    C.require(value["graph"] == declaration, "source-transition-graph-mismatch")
    completion = C.module("entity_smoke_transition_gate_reader", C.DIRECTORY / "task-execution/implementation/task-completion.py")
    completion.validate_gate(SimpleNamespace(C=C, STEPS=SimpleNamespace(require=C.require)), value["graph"], value["gate"], value["plan_sha256"], {"infrastructure-controller-source": plan["controller_sha256"]})
    summary = value["gate"].get("change_summary")
    C.require(isinstance(summary, dict) and summary.get("operation_counts") == {"create": 0, "update": 1, "delete": 0, "replace": 5, "broaden-permission": 0}
              and summary.get("input_sha256") == C.GATE.evidence_bindings(value["graph"], value["gate"]["facts"])["gates"]["change-set"], "source-transition-change-counts-mismatch")
    return value


def read(C, cache, binding):
    path = cache / "source-transition/receipt.json"
    C.RESOURCE.CONTROL.no_symlinks(path)
    if not path.exists(): return None
    value = validate(C, C.read_json(path), binding)
    plan = value["plan"]
    C.require(C.digest_file(cache / "receipts/create.json") == plan["creation_sha256"], "source-transition-creation-changed")
    for name, digest in RECOVERY.items():
        C.require(C.digest_file(cache / name) == "sha256:" + digest, "source-transition-recovery-changed")
    return value


def original_receipt(C, context, packet, completion):
    if not historical(packet, completion): return False
    before = packet["binding"]
    if before != context["binding"]:
        transition = read(C, context["cache"], context["binding"])
        C.require(transition is not None and before == transition["plan"]["previous_binding"], "source-transition-historical-binding-invalid")
    return True


def legacy_context(route, context, args, packet, completion):
    if not original_receipt(route.C, context, packet, completion): return None
    C = route.C
    request = packet["reservation"]["request"]
    checked = {**context["checked"], **{key: request[key] for key in ("definition", "security_group", "subnets")}}
    report = {"plan": {"preflight_label": request["proof_label"]}}
    return {**context, "binding": packet["binding"], "checked": checked, "report": report}


def collision_recovery(args):
    return (args.proof_label, args.workload, args.operation, getattr(args, "proof_stage", "baseline")) == (LABEL, "database-proof", "collision", "baseline")


def readback_recovery(args):
    if acceptance_renewal(args):
        return {"probe": ACCEPTANCE_PROBE, "packet": ACCEPTANCE_PACKET, "completion": ACCEPTANCE_COMPLETION,
                "failure": ACCEPTANCE_FAILURE, "failure_hash": ACCEPTANCE_FAILURE_HASH,
                "path": "task-steps/verifier-read-acceptance-collector-recovery-1-preflight.json", "condition": "preflight-observation-not-fresh", "prefix": "task-acceptance-read-recovery"}
    if (args.proof_label, args.workload, args.operation, getattr(args, "proof_stage", "baseline")) == (LABEL, "verifier", "read", "credential-recovery"):
        return {"probe": CREDENTIAL_PROBE, "packet": CREDENTIAL_PACKET, "completion": CREDENTIAL_COMPLETION,
                "failure": CREDENTIAL_FAILURE, "failure_hash": CREDENTIAL_FAILURE_HASH,
                "path": "task-steps/verifier-read-credential-recovery-preflight.json", "condition": "aws-command-failed", "prefix": "task-credential-read-recovery"}
    if (args.proof_label, args.workload, args.operation, getattr(args, "proof_stage", "baseline")) == (LABEL, "administration", "observe-migration-state", "initial-recovery"):
        return {"probe": HISTORY_PROBE, "packet": HISTORY_PACKET, "completion": HISTORY_COMPLETION,
                "failure": HISTORY_FAILURE, "failure_hash": HISTORY_FAILURE_HASH,
                "path": "task-steps/administration-observe-migration-state-initial-recovery-preflight.json", "condition": "preflight-observation-not-fresh", "prefix": "task-history-read-recovery"}
    if collision_recovery(args):
        return {"probe": COLLISION_PROBE, "packet": COLLISION_PACKET, "completion": COLLISION_COMPLETION,
                "failure": COLLISION_FAILURE, "failure_hash": COLLISION_FAILURE_HASH,
                "path": "task-steps/database-proof-collision-preflight.json", "condition": "task-log-observation-incomplete", "prefix": "task-collision-recovery"}
    if (args.proof_label, args.workload, args.operation, getattr(args, "proof_stage", "baseline")) == (LABEL, "verifier", "read", "server-replacement"):
        return {"probe": REPLACEMENT_PROBE, "packet": REPLACEMENT_PACKET, "completion": REPLACEMENT_COMPLETION,
                "failure": REPLACEMENT_FAILURE, "failure_hash": REPLACEMENT_FAILURE_HASH,
                "path": "task-steps/verifier-read-server-replacement-preflight.json", "condition": "resource-observation-not-confirmed", "prefix": "task-replacement-read-recovery"}
    return None


def preflight_step_suffix(args):
    if acceptance_refresh(args): return "-collector-recovery-1" + ("-readback-recovery-1" if acceptance_renewal(args) and args.phase == "preflight" else "")
    if restore_reader_recovery(args) and args.phase == "preflight": return "-connection-recovery-1"
    return "-readback-recovery-1" if readback_recovery(args) is not None and args.phase == "preflight" else ""


def replacement_label(context, args, original):
    if acceptance_refresh(args):
        original = collector_label(original)
        return "entity-smoke-" + hashlib.sha256((original + ":" + ACCEPTANCE_PROBE + ":readback-recovery-1").encode()).hexdigest()[:24] if acceptance_renewal(args) else original
    if restore_reader_recovery(args):
        return "entity-smoke-" + hashlib.sha256((original + ":" + RESTORE_PROBE + ":connection-recovery-1").encode()).hexdigest()[:24]
    recovery = readback_recovery(args)
    if recovery is not None:
        return "entity-smoke-" + hashlib.sha256((original + ":" + recovery["probe"] + ":readback-recovery-1").encode()).hexdigest()[:24]
    if (args.proof_label, args.workload, args.operation, getattr(args, "proof_stage", "baseline")) == (LABEL, "database-proof", "permissions", "baseline"):
        return "entity-smoke-" + hashlib.sha256((original + ":" + UNSUBMITTED_PREFLIGHT + ":known-not-submitted-recovery-1").encode()).hexdigest()[:24]
    if (args.proof_label, args.workload, args.operation, getattr(args, "proof_stage", "baseline")) != (LABEL, "administration", "grant-runtime", "baseline"):
        return original
    return "entity-smoke-" + hashlib.sha256((original + ":" + FAILED_PREFLIGHT + ":administrator-authentication-recovery-1").encode()).hexdigest()[:24]


def restore_reader_recovery(args):
    return (args.proof_label, args.workload, args.operation, getattr(args, "proof_stage", "baseline")) == (RESTORE_LABEL, "restore-reader", "restore-read", "isolated-restore")


def acceptance_refresh(args):
    return (args.proof_label, args.workload, args.operation, getattr(args, "proof_stage", "baseline")) == (ACCEPTANCE_REFRESH_LABEL, "verifier", "read", "acceptance")


def collector_label(original):
    return "entity-smoke-" + hashlib.sha256((original + ":collector-recovery-1").encode()).hexdigest()[:24]


def acceptance_renewal(args):
    return acceptance_refresh(args) and args.proof_label == ACCEPTANCE_RENEWAL_LABEL


def acceptance_refresh_preflight(C, context, args, original, *, current_time):
    """One fresh ready/read pair after the pinned collector failure; no replay."""
    C.require(acceptance_refresh(args), "acceptance-refresh-selection-invalid")
    failure_path = C.ROOT / ACCEPTANCE_REFRESH_FAILURE
    C.require(C.digest_file(failure_path) == ACCEPTANCE_REFRESH_FAILURE_HASH, "acceptance-refresh-failure-changed")
    failure = C.read_json(failure_path)
    C.require(failure.get("schema") == "deploy/entity-smoke-acceptance-report/v1" and failure.get("verdict") == "blocked"
              and failure.get("condition") == "source-transition-binding-incompatible"
              and failure.get("effect") == "no-provider-mutation-no-scope-promotion"
              and failure.get("context") == {"proof_label_sha256": hashlib.sha256(args.proof_label.encode()).hexdigest(), "stage": "acceptance-collection"},
              "acceptance-refresh-failure-invalid")
    runner = C.module("entity_smoke_acceptance_refresh_runner", C.DIRECTORY / "task-execution/implementation/task-runner.py")
    graph = C.module("entity_smoke_acceptance_refresh_graph", C.DIRECTORY / "task-execution/implementation/task-graph.py")
    completion_owner = C.module("entity_smoke_acceptance_refresh_completion", C.DIRECTORY / "task-execution/implementation/task-completion.py")
    declaration = graph.contract("verifier", C.GATE)
    artifacts = {row["id"]: ACCEPTANCE_REFRESH_CONTROLLER if row["id"] == graph.CONTROLLER_SOURCE else context["binding"]["image_digest"] for row in declaration["artifacts"]}
    store = runner.CONTROL.AttemptStore(context["cache"] / "task-attempts")
    packets = {}
    for phase, (relative, packet_hash, completion_hash) in ACCEPTANCE_REFRESH_INPUTS.items():
        path = context["cache"] / relative
        companion = completion_owner.path(path)
        C.require(C.digest_file(path) == packet_hash and C.digest_file(companion) == completion_hash, "acceptance-refresh-original-custody-changed")
        packet, closed = C.read_json(path), C.read_json(companion)
        request, reservation = packet["reservation"]["request"], packet["reservation"]
        key = "task-" + hashlib.sha256((args.proof_label + ":verifier:read:" + phase + ":acceptance").encode()).hexdigest()[:48]
        label = original if phase == "preflight" else args.proof_label
        environment = {"ENTITY_SMOKE_VERIFICATION_OPERATION": "ready" if phase == "preflight" else "read", "ENTITY_SMOKE_PROOF_LABEL": label,
                       "ENTITY_SMOKE_EXPECTED_SOURCE": context["binding"]["source_revision"]}
        if phase == "operation": environment["ENTITY_SMOKE_EXPECTED_DIGEST"] = args.expected_digest
        C.require(packet["binding"] == context["binding"] and store.read(key, request) == reservation
                  and request["proof_label"] == label and request["workload"] == "verifier"
                  and request["environment"] == environment,
                  "acceptance-refresh-original-binding-invalid")
        C.require(runner.EVIDENCE.validate_retained(packet["receipt"], reservation) == packet["receipt"], "acceptance-refresh-original-result-invalid")
        reference = closed["realization_evidence"]
        prefix = str((context["cache"] / "task-realization").relative_to(C.ROOT)) + "/controlled-execution-"
        C.require(isinstance(reference, str) and reference.startswith(prefix) and re.fullmatch(r"[a-f0-9]{32}\.json", reference[len(prefix):])
                  and closed["step_sha256"] == packet_hash and closed["plan_sha256"] == packet["plan_sha256"], "acceptance-refresh-original-completion-invalid")
        gate_path = C.ROOT / reference
        C.require(C.digest_file(gate_path) == closed["realization_evidence_sha256"], "acceptance-refresh-original-gate-changed")
        retained_gate = C.read_json(gate_path)
        retained_graph = graph.retained(C, declaration, gate=retained_gate)
        completion_owner.validate_gate(SimpleNamespace(C=C, STEPS=SimpleNamespace(require=C.require)), retained_graph, retained_gate, packet["plan_sha256"], artifacts)
        packets[phase] = packet
    before, result = packets["preflight"], packets["operation"]
    runner.PREFLIGHT.read_admission(context["cache"] / "task-receipts", result["reservation"])
    admission = C.read_json(runner.PREFLIGHT.admission_path(context["cache"] / "task-receipts", result["reservation"]))
    C.require(admission["preflight"]["reservation"] == before["reservation"] and admission["preflight"]["receipt"] == before["receipt"]
              and result["receipt"]["result"].get("code") == "ENTITY_SMOKE_RECORD_RETRIEVED"
              and result["receipt"]["result"].get("record_digest") == args.expected_digest, "acceptance-refresh-original-read-required")
    C.require((C.RESOURCE.timestamp(current_time) - C.RESOURCE.timestamp(result["receipt"]["collected_at"])).total_seconds() > 900,
              "acceptance-refresh-original-read-not-expired")
    return replacement_label(context, args, original)


def restore_reader_preflight(C, context, deployed, original):
    """One new read-only observation, never a retry of the failed reservation."""
    args = SimpleNamespace(proof_label=context["binding"]["proof_label"], workload="restore-reader", operation="restore-read", proof_stage="isolated-restore")
    if not restore_reader_recovery(args): return original
    path = context["cache"] / RESTORE_FAILURE
    C.require(C.digest_file(path) == RESTORE_FAILURE_HASH, "restore-reader-recovery-evidence-changed")
    failure = C.read_json(path)
    C.require(isinstance(failure, dict) and failure.get("schema") == "deploy/entity-smoke-restore-reader-failure/v1"
              and failure.get("scope_acceptance") is False and failure.get("current_readiness") is False
              and failure.get("condition") == "task-unsuccessful-completion"
              and failure.get("deployment_sha256") == C.digest_file(context["cache"] / "restore-deploy-receipt.json"), "restore-reader-recovery-evidence-invalid")
    reservation_path = context["cache"] / "task-attempts" / (original + "-restore-reader-preflight.json")
    C.require(failure.get("reservation_path") == str(reservation_path.relative_to(C.ROOT))
              and C.digest_file(reservation_path) == failure.get("reservation_sha256"), "restore-reader-recovery-reservation-changed")
    reservation = C.read_json(reservation_path)
    expected = {**context["binding"], **context["checked"], "workload": "restore-reader", "proof_label": original,
                "environment": {"ENTITY_SMOKE_DATABASE_PROOF_OPERATION": "preflight", "ENTITY_SMOKE_PROOF_LABEL": original}, "deadline_seconds": 90}
    # checked can contain inspection-only facts; the request has just these bindings.
    expected = {key: value for key, value in expected.items() if key in {"source_revision", "image_digest", "configuration_contract_sha256", "permission_contract_sha256", "dependency_incarnation_sha256", "definition", "security_group", "subnets", "workload", "proof_label", "environment", "deadline_seconds"}}
    store = C.RESOURCE.CONTROL.AttemptStore(context["cache"] / "task-attempts")
    C.require(reservation.get("operation_id") == RESTORE_PROBE and reservation.get("request") == expected
              and store.read("original-restore-preflight", expected) == reservation, "restore-reader-recovery-original-request-mismatch")
    task = failure.get("task", {})
    timestamp = C.RESOURCE.timestamp
    C.require(task.get("operation_id") == RESTORE_PROBE and task.get("exit_code") == 1
              and task.get("image_digest") == expected["image_digest"]
              and timestamp(deployed["observed_at"]) <= timestamp(task.get("created_at")) <= timestamp(task.get("started_at")) <= timestamp(task.get("stopped_at")) <= timestamp(failure.get("observed_at"))
              and (timestamp(task["stopped_at"]) - timestamp(task["created_at"])).total_seconds() <= 90, "restore-reader-recovery-terminal-required")
    original_failure = C.ROOT / failure["failure_path"]
    C.require(C.digest_file(original_failure) == failure.get("failure_sha256"), "restore-reader-recovery-report-changed")
    report = C.read_json(original_failure)
    C.require(report.get("condition") == "task-unsuccessful-completion" and report.get("effect") == "unknown-reconcile-only"
              and all(report.get("context", {}).get(key) == value for key, value in {"mode": "execute", "phase": "preflight", "workload": "restore-reader"}.items()), "restore-reader-recovery-report-invalid")
    bundle = C.RESOURCE.EVIDENCE.failure_bundle({"verdict": "failed", "code": "ENTITY_SMOKE_OPERATION_NOT_CONFIRMED", "diagnostic": failure["diagnostic"], "related_diagnostics": failure["related_diagnostics"]})
    C.require(all(report.get(key) == value for key, value in bundle.items())
              and bundle["diagnostic"]["code"] == "persistence.unclassified-failure"
              and bundle["diagnostic"]["detail"] == {"phase": "pool_connect", "classification": "unknown", "codeStatus": "absent", "operation": "readiness", "effect": "not-assessed"}, "restore-reader-recovery-diagnostic-invalid")
    selected = replacement_label(context, args, original)
    renewed = {**expected, "proof_label": selected, "environment": {**expected["environment"], "ENTITY_SMOKE_PROOF_LABEL": selected}}
    if store.read("replacement-restore-preflight", renewed) is None:
        key = "task-" + hashlib.sha256((args.proof_label + ":restore-reader:restore-read:operation:isolated-restore").encode()).hexdigest()[:48]
        operation_path = context["cache"] / "task-attempts" / (key + ".json")
        C.RESOURCE.CONTROL.no_symlinks(operation_path)
        C.require(not operation_path.exists(), "restore-reader-recovery-operation-already-reserved")
    return selected


def recovery_preflight(C, context, args, original):
    selected = replacement_label(context, args, original)
    if acceptance_refresh(args):
        acceptance_refresh_preflight(C, context, args, original, current_time=C.now())
        if not acceptance_renewal(args): return selected
        original = collector_label(original)
    if selected == original: return original
    recovery = readback_recovery(args)
    if recovery is not None:
        target = context["cache"] / recovery["path"]
        sidecar = target.with_name(target.stem + ".completion.json")
        C.require(C.digest_file(target) == recovery["packet"] and C.digest_file(sidecar) == recovery["completion"]
                  and C.digest_file(C.ROOT / recovery["failure"]) == recovery["failure_hash"], recovery["prefix"] + "-evidence-changed")
        packet, completion, failure = C.read_json(target), C.read_json(sidecar), C.read_json(C.ROOT / recovery["failure"])
        reservation, receipt = packet["reservation"], packet["receipt"]
        request = reservation["request"]
        environment = {"ENTITY_SMOKE_DATABASE_PROOF_OPERATION": "preflight", "ENTITY_SMOKE_PROOF_LABEL": original} if args.workload == "database-proof" else {
            "ENTITY_SMOKE_VERIFICATION_OPERATION": "ready", "ENTITY_SMOKE_PROOF_LABEL": original, "ENTITY_SMOKE_EXPECTED_SOURCE": context["binding"]["source_revision"]}
        if args.workload == "administration": environment = {"ENTITY_SMOKE_ADMINISTRATION_OPERATION": "preflight"}
        C.RESOURCE.EVIDENCE.validate_retained(receipt, reservation)
        C.require(historical(packet, completion) and packet["binding"] == context["binding"]
                  and completion["step_sha256"] == recovery["packet"] and completion["plan_sha256"] == packet["plan_sha256"]
                  and C.digest_file(C.ROOT / completion["realization_evidence"]) == completion["realization_evidence_sha256"]
                  and reservation["operation_id"] == recovery["probe"] and request["proof_label"] == original and request["environment"] == environment
                  and request["deadline_seconds"] == 90
                  and failure.get("effect") == "not-started" and failure.get("condition") == recovery["condition"]
                  and all(failure.get("context", {}).get(key) == value for key, value in {"workload": args.workload, "operation": args.operation, "phase": "operation", "proof_stage": getattr(args, "proof_stage", "baseline")}.items())
                  and (C.RESOURCE.timestamp(C.now()) - C.RESOURCE.timestamp(receipt["task"]["stopped_at"])).total_seconds() > 900,
                  recovery["prefix"] + "-evidence-invalid")
        store = C.RESOURCE.CONTROL.AttemptStore(context["cache"] / "task-attempts")
        C.require(store.read("original-readback-preflight", request) == reservation, recovery["prefix"] + "-reservation-required")
        renewed_environment = dict(request["environment"])
        if "ENTITY_SMOKE_PROOF_LABEL" in renewed_environment: renewed_environment["ENTITY_SMOKE_PROOF_LABEL"] = selected
        renewed = {**request, "proof_label": selected, "environment": renewed_environment}
        if args.phase == "preflight" and store.read("renewed-readback-preflight", renewed) is None:
            suffix = "" if getattr(args, "proof_stage", "baseline") == "baseline" else ":" + args.proof_stage
            if acceptance_renewal(args): suffix += ":collector-recovery-1"
            key = "task-" + hashlib.sha256((LABEL + ":" + args.workload + ":" + args.operation + ":operation" + suffix).encode()).hexdigest()[:48]
            operation_path = context["cache"] / "task-attempts" / (key + ".json")
            C.RESOURCE.CONTROL.no_symlinks(operation_path)
            C.require(not operation_path.exists(), recovery["prefix"] + "-operation-already-reserved")
        return selected
    if args.workload == "database-proof":
        target = context["cache"] / "task-attempts" / (original + "-database-proof-preflight.json")
        C.require(C.digest_file(target) == UNSUBMITTED_RESERVATION_HASH
                  and C.digest_file(C.ROOT / UNSUBMITTED_REPORT) == UNSUBMITTED_REPORT_HASH, "task-unsubmitted-recovery-evidence-changed")
        reservation, failure = C.read_json(target), C.read_json(C.ROOT / UNSUBMITTED_REPORT)
        request = reservation["request"]
        C.require(reservation["operation_id"] == UNSUBMITTED_PREFLIGHT and request["proof_label"] == original
                  and all(request.get(key) == value for key, value in context["binding"].items() if key != "proof_label")
                  and request["environment"] == {"ENTITY_SMOKE_DATABASE_PROOF_OPERATION": "preflight", "ENTITY_SMOKE_PROOF_LABEL": original}
                  and failure.get("effect") == "not-started" and failure.get("condition") == "aws-command-failed"
                  and C.RESOURCE.CONTROL.AttemptStore(context["cache"] / "task-attempts").read("original-unsubmitted-preflight", request) == reservation,
                  "task-unsubmitted-recovery-evidence-invalid")
        return selected
    C.require(read(C, context["cache"], context["binding"]) is not None, "source-transition-replacement-preflight-recovery-required")
    target = context["cache"] / "task-attempts" / (original + "-administration-preflight.json")
    previous = C.read_json(target)
    request = previous.get("request", {})
    C.require(previous.get("operation_id") == FAILED_PREFLIGHT and request.get("source_revision") == OLD_SOURCE
              and request.get("image_digest") == OLD_IMAGE and request.get("proof_label") == original
              and request.get("environment") == {"ENTITY_SMOKE_ADMINISTRATION_OPERATION": "preflight"}
              and C.RESOURCE.CONTROL.AttemptStore(context["cache"] / "task-attempts").read("original-preflight", request) == previous,
              "source-transition-original-preflight-mismatch")
    return selected


def graph(C):
    value = C.yaml.safe_load(C.CONTRACT.read_text())
    value["id"] += "-source-transition"
    value["artifacts"][0]["entrypoint"] = "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/recovery-and-replacement/source-transition/source-transition.py"
    value["change_shape"].update(allowed_operation_classes=["update", "replace"], forbidden_operation_classes=["create", "delete", "broaden-permission"])
    value["change_shape"]["immutable_definition_refresh"] = {key: True for key in (
        "owned_task_definitions_only", "stopped_workload_required", "unchanged_permissions_and_storage", "qualified_image_required", "original_preparation_retained")}
    C.GATE.validate_contract(value)
    return value


def main():
    # Historical custody validation does not authorize another transition.
    # No provider/module loading or CLI-supplied file access is needed.
    print(json.dumps({"verdict": "blocked",
                      "condition": "source-transition-executor-retired",
                      "effect": "not-started"}, sort_keys=True))
    return 1


if __name__ == "__main__": raise SystemExit(main())
