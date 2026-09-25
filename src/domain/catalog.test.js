import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  ACTION_IDS,
  CatalogValidationError,
  validateCatalog,
} from "./catalog.js";

function validCatalog() {
  return {
    schemaVersion: 1,
    virtualDevice: {
      provider: "simhub-control-mapper",
      identity: "SimHub vJoy output",
    },
    bindings: [
      { actionId: "pit_limiter", virtualButton: 7 },
      { actionId: "tc_increase", virtualButton: 8 },
      { actionId: "tc_decrease", virtualButton: 9 },
    ],
  };
}

describe("action catalog", () => {
  it("exposes exactly the three first-milestone action IDs", () => {
    assert.deepEqual(ACTION_IDS, [
      "pit_limiter",
      "tc_increase",
      "tc_decrease",
    ]);
  });

  it("normalizes a valid manually configured catalog", () => {
    const catalog = validCatalog();
    catalog.virtualDevice.identity = "  SimHub vJoy output  ";

    const result = validateCatalog(catalog);

    assert.equal(result.virtualDevice.identity, "SimHub vJoy output");
    assert.deepEqual(result.bindings, catalog.bindings);
    assert.ok(Object.isFrozen(result));
    assert.ok(Object.isFrozen(result.bindings));
    assert.ok(Object.isFrozen(result.bindings[0]));
  });

  it("allows an empty catalog while a user is still assigning actions", () => {
    const catalog = validCatalog();
    catalog.bindings = [];

    assert.deepEqual(validateCatalog(catalog).bindings, []);
  });

  it("rejects duplicate action assignments", () => {
    const catalog = validCatalog();
    catalog.bindings[1].actionId = "pit_limiter";

    assert.throws(
      () => validateCatalog(catalog),
      (error) =>
        error instanceof CatalogValidationError &&
        error.issues.some((issue) => issue.includes("duplicates bindings[0]")),
    );
  });

  it("rejects duplicate virtual-button assignments", () => {
    const catalog = validCatalog();
    catalog.bindings[1].virtualButton = 7;

    assert.throws(
      () => validateCatalog(catalog),
      (error) =>
        error instanceof CatalogValidationError &&
        error.issues.some((issue) => issue.includes("button 7")),
    );
  });

  it("rejects unknown actions and non-positive button numbers", () => {
    const catalog = validCatalog();
    catalog.bindings = [
      { actionId: "headlights", virtualButton: 0 },
      { actionId: "tc_increase", virtualButton: 1.5 },
    ];

    assert.throws(
      () => validateCatalog(catalog),
      (error) =>
        error instanceof CatalogValidationError && error.issues.length === 3,
    );
  });

  it("rejects unknown schema versions and fields instead of discarding them", () => {
    const catalog = validCatalog();
    catalog.schemaVersion = 2;
    catalog.unrecognized = true;
    catalog.bindings[0].nativeAction = "guessed-value";

    assert.throws(
      () => validateCatalog(catalog),
      (error) =>
        error instanceof CatalogValidationError &&
        error.issues.some((issue) => issue.includes("schemaVersion")) &&
        error.issues.some((issue) => issue.includes("catalog.unrecognized")) &&
        error.issues.some((issue) => issue.includes("nativeAction")),
    );
  });

  it("reports independent structural problems together", () => {
    assert.throws(
      () =>
        validateCatalog({
          schemaVersion: 1,
          virtualDevice: null,
          bindings: "not-an-array",
        }),
      (error) =>
        error instanceof CatalogValidationError &&
        error.issues.includes("virtualDevice must be an object") &&
        error.issues.includes("bindings must be an array"),
    );
  });
});

