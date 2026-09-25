import assert from "node:assert/strict";
import { mkdtemp, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, it } from "node:test";

import {
  FileChangeError,
  applyFileChange,
  planFileChange,
  previewRestore,
  restoreFile,
  sha256,
} from "./file-change.js";

const temporaryDirectories = [];

async function fixture() {
  const directory = await mkdtemp(join(tmpdir(), "sim-controls-manager-"));
  temporaryDirectories.push(directory);
  const sourcePath = join(directory, "controls.fixture");
  const backupDirectory = join(directory, "backups");
  await writeFile(sourcePath, Buffer.from([0x00, 0x41, 0xff, 0x0a]));
  return { directory, sourcePath, backupDirectory };
}

afterEach(async () => {
  await Promise.all(
    temporaryDirectories.splice(0).map((directory) =>
      rm(directory, { recursive: true, force: true }),
    ),
  );
});

describe("guarded file changes", () => {
  it("recognizes an idempotent plan and creates no backup", async () => {
    const { sourcePath, backupDirectory } = await fixture();
    const original = await readFile(sourcePath);
    const plan = await planFileChange({ sourcePath, nextBytes: original });

    const result = await applyFileChange(plan, { backupDirectory });

    assert.equal(plan.changed, false);
    assert.equal(result.status, "unchanged");
    await assert.rejects(readdir(backupDirectory), { code: "ENOENT" });
  });

  it("applies exact bytes and creates a verified backup and receipt", async () => {
    const { sourcePath, backupDirectory } = await fixture();
    const original = await readFile(sourcePath);
    const nextBytes = Buffer.from([0x00, 0x42, 0xfe, 0x0a]);
    const plan = await planFileChange({ sourcePath, nextBytes });

    const result = await applyFileChange(plan, {
      backupDirectory,
      validate: (bytes) => bytes.length === 4,
      now: () => new Date("2026-09-25T01:02:03.000Z"),
    });

    assert.equal(result.status, "applied");
    assert.deepEqual(await readFile(sourcePath), nextBytes);
    assert.deepEqual(await readFile(result.receipt.backupPath), original);
    assert.equal(result.receipt.originalHash, sha256(original));
    assert.equal(result.receipt.appliedHash, sha256(nextBytes));
    assert.deepEqual(
      JSON.parse(await readFile(result.receiptPath, "utf8")),
      result.receipt,
    );
  });

  it("refuses to apply when the source changed after preview", async () => {
    const { sourcePath, backupDirectory } = await fixture();
    const plan = await planFileChange({
      sourcePath,
      nextBytes: Buffer.from("planned"),
    });
    await writeFile(sourcePath, "changed elsewhere");

    await assert.rejects(
      applyFileChange(plan, { backupDirectory }),
      (error) => error instanceof FileChangeError && error.code === "SOURCE_CHANGED",
    );
    await assert.rejects(readdir(backupDirectory), { code: "ENOENT" });
  });

  it("refuses to apply while the target process is running", async () => {
    const { sourcePath, backupDirectory } = await fixture();
    const plan = await planFileChange({ sourcePath, nextBytes: Buffer.from("next") });

    await assert.rejects(
      applyFileChange(plan, { backupDirectory, isTargetInUse: () => true }),
      (error) => error instanceof FileChangeError && error.code === "TARGET_IN_USE",
    );
    await assert.rejects(readdir(backupDirectory), { code: "ENOENT" });
  });

  it("validates before backup and writing", async () => {
    const { sourcePath, backupDirectory } = await fixture();
    const original = await readFile(sourcePath);
    const plan = await planFileChange({ sourcePath, nextBytes: Buffer.from("invalid") });

    await assert.rejects(
      applyFileChange(plan, { backupDirectory, validate: () => false }),
      (error) => error instanceof FileChangeError && error.code === "VALIDATION_FAILED",
    );
    assert.deepEqual(await readFile(sourcePath), original);
    await assert.rejects(readdir(backupDirectory), { code: "ENOENT" });
  });

  it("rolls back if post-write validation fails", async () => {
    const { sourcePath, backupDirectory } = await fixture();
    const original = await readFile(sourcePath);
    const plan = await planFileChange({ sourcePath, nextBytes: Buffer.from("next") });
    let validationCalls = 0;

    await assert.rejects(
      applyFileChange(plan, {
        backupDirectory,
        validate: () => {
          validationCalls += 1;
          return validationCalls < 3;
        },
      }),
      (error) => error instanceof FileChangeError && error.code === "VALIDATION_FAILED",
    );

    assert.equal(validationCalls, 3);
    assert.deepEqual(await readFile(sourcePath), original);
  });
});

describe("restore", () => {
  async function appliedFixture() {
    const values = await fixture();
    const original = await readFile(values.sourcePath);
    const nextBytes = Buffer.from("applied bytes");
    const plan = await planFileChange({ sourcePath: values.sourcePath, nextBytes });
    const applied = await applyFileChange(plan, {
      backupDirectory: values.backupDirectory,
    });
    return { ...values, original, nextBytes, applied };
  }

  it("previews, restores, and then reports an idempotent restore", async () => {
    const { sourcePath, original, applied } = await appliedFixture();

    assert.equal((await previewRestore(applied.receiptPath)).status, "ready");
    assert.equal((await restoreFile(applied.receiptPath)).status, "restored");
    assert.deepEqual(await readFile(sourcePath), original);
    assert.equal((await previewRestore(applied.receiptPath)).status, "already-restored");
    assert.equal((await restoreFile(applied.receiptPath)).status, "unchanged");
  });

  it("refuses to overwrite intervening changes unless explicitly confirmed", async () => {
    const { sourcePath, original, applied } = await appliedFixture();
    await writeFile(sourcePath, "user changed this after apply");

    assert.equal(
      (await previewRestore(applied.receiptPath)).status,
      "changed-since-apply",
    );
    await assert.rejects(
      restoreFile(applied.receiptPath),
      (error) => error instanceof FileChangeError && error.code === "TARGET_CHANGED",
    );
    assert.equal(await readFile(sourcePath, "utf8"), "user changed this after apply");

    assert.equal(
      (await restoreFile(applied.receiptPath, { allowChangedTarget: true })).status,
      "restored",
    );
    assert.deepEqual(await readFile(sourcePath), original);
  });
});

