/**
 * The user-facing action vocabulary for the first proof of concept.
 *
 * Adapters translate these stable IDs to verified game-native commands. They
 * must not infer support from a similar-looking native command name.
 */
export const ACTIONS = Object.freeze({
  pit_limiter: Object.freeze({
    id: "pit_limiter",
    label: "Pit Limiter",
  }),
  tc_increase: Object.freeze({
    id: "tc_increase",
    label: "Traction Control Increase",
  }),
  tc_decrease: Object.freeze({
    id: "tc_decrease",
    label: "Traction Control Decrease",
  }),
});

export const ACTION_IDS = Object.freeze(Object.keys(ACTIONS));
export const CATALOG_SCHEMA_VERSION = 1;
export const SIMHUB_PROVIDER = "simhub-control-mapper";

const TOP_LEVEL_KEYS = new Set(["schemaVersion", "virtualDevice", "bindings"]);
const DEVICE_KEYS = new Set(["provider", "identity"]);
const BINDING_KEYS = new Set(["actionId", "virtualButton"]);

export class CatalogValidationError extends Error {
  /** @param {readonly string[]} issues */
  constructor(issues) {
    super(`Invalid action catalog:\n- ${issues.join("\n- ")}`);
    this.name = "CatalogValidationError";
    this.issues = Object.freeze([...issues]);
  }
}

/**
 * Validate and normalize an app-owned action catalog.
 *
 * `virtualButton` is the positive, one-based button number displayed by
 * SimHub. A game adapter owns any conversion to a native zero-based or
 * one-based representation.
 *
 * @param {unknown} input
 * @returns {{
 *   schemaVersion: 1,
 *   virtualDevice: {provider: string, identity: string},
 *   bindings: Array<{actionId: string, virtualButton: number}>
 * }}
 * @throws {CatalogValidationError}
 */
export function validateCatalog(input) {
  const issues = [];

  if (!isPlainObject(input)) {
    throw new CatalogValidationError(["catalog must be a JSON object"]);
  }

  rejectUnknownKeys(input, TOP_LEVEL_KEYS, "catalog", issues);

  if (input.schemaVersion !== CATALOG_SCHEMA_VERSION) {
    issues.push(
      `schemaVersion must be ${CATALOG_SCHEMA_VERSION}; received ${formatValue(input.schemaVersion)}`,
    );
  }

  const device = input.virtualDevice;
  if (!isPlainObject(device)) {
    issues.push("virtualDevice must be an object");
  } else {
    rejectUnknownKeys(device, DEVICE_KEYS, "virtualDevice", issues);

    if (device.provider !== SIMHUB_PROVIDER) {
      issues.push(`virtualDevice.provider must be ${JSON.stringify(SIMHUB_PROVIDER)}`);
    }
    if (typeof device.identity !== "string" || device.identity.trim() === "") {
      issues.push("virtualDevice.identity must be a non-empty string");
    }
  }

  if (!Array.isArray(input.bindings)) {
    issues.push("bindings must be an array");
  }

  const seenActions = new Map();
  const seenButtons = new Map();
  const normalizedBindings = [];

  if (Array.isArray(input.bindings)) {
    for (const [index, binding] of input.bindings.entries()) {
      const location = `bindings[${index}]`;
      if (!isPlainObject(binding)) {
        issues.push(`${location} must be an object`);
        continue;
      }

      rejectUnknownKeys(binding, BINDING_KEYS, location, issues);

      const { actionId, virtualButton } = binding;
      if (typeof actionId !== "string" || !ACTION_IDS.includes(actionId)) {
        issues.push(
          `${location}.actionId must be one of: ${ACTION_IDS.join(", ")}`,
        );
      } else if (seenActions.has(actionId)) {
        issues.push(
          `${location}.actionId duplicates ${seenActions.get(actionId)} (${actionId})`,
        );
      } else {
        seenActions.set(actionId, location);
      }

      if (!Number.isSafeInteger(virtualButton) || virtualButton < 1) {
        issues.push(`${location}.virtualButton must be a positive integer`);
      } else if (seenButtons.has(virtualButton)) {
        issues.push(
          `${location}.virtualButton duplicates ${seenButtons.get(virtualButton)} (button ${virtualButton})`,
        );
      } else {
        seenButtons.set(virtualButton, location);
      }

      if (
        typeof actionId === "string" &&
        ACTION_IDS.includes(actionId) &&
        Number.isSafeInteger(virtualButton) &&
        virtualButton >= 1
      ) {
        normalizedBindings.push({ actionId, virtualButton });
      }
    }
  }

  if (issues.length > 0) {
    throw new CatalogValidationError(issues);
  }

  return Object.freeze({
    schemaVersion: CATALOG_SCHEMA_VERSION,
    virtualDevice: Object.freeze({
      provider: device.provider,
      identity: device.identity.trim(),
    }),
    bindings: Object.freeze(
      normalizedBindings.map((binding) => Object.freeze(binding)),
    ),
  });
}

function isPlainObject(value) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    return false;
  }
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

function rejectUnknownKeys(value, allowedKeys, location, issues) {
  for (const key of Object.keys(value)) {
    if (!allowedKeys.has(key)) {
      issues.push(`${location}.${key} is not supported by this schema version`);
    }
  }
}

function formatValue(value) {
  const encoded = JSON.stringify(value);
  return encoded === undefined ? String(value) : encoded;
}

