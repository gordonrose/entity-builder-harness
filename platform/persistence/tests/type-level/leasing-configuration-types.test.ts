import { validatePersistenceLeaseDuration, persistenceRelayConfigurationError, type PersistenceLeaseDurationReason } from "../../src/index";
const result = validatePersistenceLeaseDuration(30000);
if (result.ok) { const milliseconds: number = result.value; void milliseconds; }
else { const reason: PersistenceLeaseDurationReason = result.error.reason; persistenceRelayConfigurationError(reason); }
// @ts-expect-error Arbitrary descriptions are not diagnostic reasons.
persistenceRelayConfigurationError("private-message");
