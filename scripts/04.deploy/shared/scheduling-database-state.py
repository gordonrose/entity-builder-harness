# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.scheduling-database-state
#   version: 2
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.scheduling
#   disciplines: [security, sre]
#   kind: script
#   purpose: Validate the finite scheduling database observation shared by independent task-proof readers.
#   portability: {class: source-only, targets: []}
#   effects: [read-only]
#   used_by:
#   - id: deploy.library.kanbien-core-platform.persistence-proof-receipts
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/proof-receipts.py
#   - id: deploy.library.entity-smoke.task-evidence
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-execution/implementation/task-evidence.py
"""A captured observation, never an activation decision or live acceptance."""
import re

RESULTS = {
    "grant-scheduling-access": "PERSISTENCE_SCHEDULING_ACCESS_GRANTED",
    "observe-scheduling-state": "PERSISTENCE_SCHEDULING_STATE_CONFIRMED",
    "prove-scheduling-access": "PERSISTENCE_SCHEDULING_PRIVILEGE_PROVEN",
}
COUNTERS = frozenset({"waiting_schedules", "pending_outbox", "active_processing"})
PREFIX_OPERATION = "observe-scheduling-prefix"
PREFIX_RESULT = "PERSISTENCE_SCHEDULING_PREFIX_CONFIRMED"


def validate(value):
    fields = {"schema", "manifest_sha256", "migration_count", "work_inventory"}
    if (type(value) is not dict or set(value) != fields
            or value["schema"] != "kanbien/scheduling-database-state/v1"
            or type(value["manifest_sha256"]) is not str
            or re.fullmatch(r"[a-f0-9]{64}", value["manifest_sha256"]) is None
            or type(value["migration_count"]) is not int
            or not 1 <= value["migration_count"] <= 9007199254740991):
        raise ValueError("scheduling-database-state-invalid")
    inventory = value["work_inventory"]
    if (type(inventory) is not dict or set(inventory) != COUNTERS
            or any(type(count) is not int or not 0 <= count <= 9007199254740991
                   for count in inventory.values())):
        raise ValueError("scheduling-database-state-invalid")
    return {**value, "work_inventory": dict(inventory)}


def validate_prefix(value, *, minimum_applied_migrations, manifest_migration_count):
    """Check captured history shape, never substitute it for complete readiness."""
    fields = {"schema", "manifest_sha256", "manifest_migration_count", "minimum_applied_migrations",
              "applied_migrations", "applied_prefix_sha256", "state"}
    if (type(value) is not dict or set(value) != fields
            or value["schema"] != "kanbien/scheduling-migration-prefix/v1"
            or any(type(value[key]) is not str or re.fullmatch(r"[a-f0-9]{64}", value[key]) is None
                   for key in ("manifest_sha256", "applied_prefix_sha256"))
            or any(type(value[key]) is not int or not 1 <= value[key] <= 9007199254740991
                   for key in ("manifest_migration_count", "minimum_applied_migrations", "applied_migrations"))
            or value["manifest_migration_count"] != manifest_migration_count
            or value["minimum_applied_migrations"] != minimum_applied_migrations
            or not minimum_applied_migrations <= value["applied_migrations"] <= manifest_migration_count):
        raise ValueError("scheduling-migration-prefix-invalid")
    complete = value["applied_migrations"] == manifest_migration_count
    if (value["state"] != ("complete" if complete else "partial")
            or (value["manifest_sha256"] == value["applied_prefix_sha256"]) != complete):
        raise ValueError("scheduling-migration-prefix-invalid")
    return dict(value)


def initial_readiness(binding, observations, *, target, scope, required_after, checked_at, timestamp, observation_expired):
    """Compare already-authenticated observations for the initial empty gate.

    Scope owners must reconcile originals with their actual provider before
    calling. This comparison does not authenticate JSON, authorize activation,
    or permit later proof-owned pending work. A controller must bind its own
    retained preparation time as required_after and recheck at the next action.
    """
    try:
        if (type(binding) is not dict or set(binding) != {"source_revision", "image_digest", "dependency_incarnation_sha256"}
                or re.fullmatch(r"[a-f0-9]{40}", binding["source_revision"]) is None
                or any(re.fullmatch(r"sha256:[a-f0-9]{64}", binding[key]) is None for key in ("image_digest", "dependency_incarnation_sha256"))
                or any(re.fullmatch(r"[a-z][a-z0-9-]{1,63}", value) is None for value in (target, scope))
                or type(observations) is not dict or set(observations) != {"state", "grant", "prove"}): raise ValueError()
        current, previous = timestamp(checked_at), timestamp(required_after)
        if current is None or previous is None or previous > current: raise ValueError()
        manifest, identities, retained = None, set(), {}
        for name in ("state", "grant", "prove"):
            observation = observations[name]
            if type(observation) is not dict or set(observation) != {"receipt_sha256", "task_arn", "started_at", "stopped_at", "database_state"}: raise ValueError()
            state = validate(observation["database_state"])
            started, stopped = timestamp(observation["started_at"]), timestamp(observation["stopped_at"])
            if (state["migration_count"] != 7 or manifest is not None and state["manifest_sha256"] != manifest
                    or started is None or stopped is None or not previous <= started <= stopped <= current
                    or observation_expired(observation["stopped_at"], checked_at, timestamp)
                    or re.fullmatch(r"sha256:[a-f0-9]{64}", observation["receipt_sha256"]) is None
                    or not isinstance(observation["task_arn"], str) or not observation["task_arn"]
                    or observation["task_arn"] in identities): raise ValueError()
            # The final privilege proof includes its own current inventory;
            # pre-grant emptiness alone cannot qualify this gate.
            if any(state["work_inventory"].values()):
                raise ValueError("scheduling-database-readiness-unrelated-work")
            manifest, previous = state["manifest_sha256"], stopped
            identities.add(observation["task_arn"])
            retained[name] = {key: observation[key] for key in ("receipt_sha256", "task_arn", "started_at", "stopped_at")}
        return {"schema": "kanbien/scheduling-database-readiness/v1", "target": target, "scope": scope,
            **binding, "manifest_sha256": manifest, "migration_count": 7, "work_inventory": dict(state["work_inventory"]),
            "required_after": required_after, "checked_at": checked_at, "proofs": retained}
    except (TypeError, KeyError, ValueError) as error:
        if str(error) == "scheduling-database-readiness-unrelated-work": raise
        raise ValueError("scheduling-database-readiness-invalid") from None
