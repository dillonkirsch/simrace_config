import { createHash, randomUUID } from "node:crypto";
import {
  constants as fsConstants,
  copyFile,
  mkdir,
  open,
  readFile,
  rename,
  stat,
  unlink,
  writeFile,
} from "node:fs/promises";
import { basename, dirname, join, resolve } from "node:path";

export const RECEIPT_VERSION = 1;

export class FileChangeError extends Error {
  constructor(code, message, options) {
    super(message, options);
    this.name = "FileChangeError";
    this.code = code;
  }
}

/**
 * Read a source file and prepare an immutable, byte-exact change plan.
 * Planning never writes to disk.
 *
 * @param {{sourcePath: string, nextBytes: Uint8Array}} input
 */
export async function planFileChange({ sourcePath, nextBytes }) {
  if (typeof sourcePath !== "string" || sourcePath.trim() === "") {
    throw new TypeError("sourcePath must be a non-empty string");
  }
  if (!(nextBytes instanceof Uint8Array)) {
    throw new TypeError("nextBytes must be a Uint8Array or Buffer");
  }

  const absoluteSourcePath = resolve(sourcePath);
  const sourceBytes = await readFile(absoluteSourcePath);
  const proposedBytes = Buffer.from(nextBytes);
  const sourceHash = sha256(sourceBytes);
  const nextHash = sha256(proposedBytes);

  return Object.freeze({
    sourcePath: absoluteSourcePath,
    sourceHash,
    nextHash,
    nextBytes: proposedBytes,
    changed: sourceHash !== nextHash,
  });
}

/**
 * Apply one planned file change with a verified backup and restore receipt.
 *
 * `validate` must parse/validate the proposed native format. `isTargetInUse`
 * lets the caller enforce the game's process-running guard.
 *
 * @param {Awaited<ReturnType<typeof planFileChange>>} plan
 * @param {{
 *   backupDirectory: string,
 *   validate?: (bytes: Buffer) => boolean | void | Promise<boolean | void>,
 *   isTargetInUse?: () => boolean | Promise<boolean>,
 *   now?: () => Date
 * }} options
 */
export async function applyFileChange(plan, options) {
  assertPlan(plan);
  if (!options || typeof options.backupDirectory !== "string") {
    throw new TypeError("backupDirectory is required");
  }

  const validate = options.validate ?? (() => true);
  const isTargetInUse = options.isTargetInUse ?? (() => false);
  const now = options.now ?? (() => new Date());

  if (await isTargetInUse()) {
    throw new FileChangeError(
      "TARGET_IN_USE",
      "Refusing to write while the target game or process is running",
    );
  }

  const currentBytes = await readFile(plan.sourcePath);
  const currentHash = sha256(currentBytes);
  if (currentHash !== plan.sourceHash) {
    throw new FileChangeError(
      "SOURCE_CHANGED",
      "The source file changed after preview; create a new preview before applying",
    );
  }

  if (sha256(plan.nextBytes) !== plan.nextHash) {
    throw new FileChangeError(
      "PLAN_CHANGED",
      "The proposed bytes no longer match the previewed change",
    );
  }

  if (!plan.changed) {
    return Object.freeze({ status: "unchanged", receiptPath: null, receipt: null });
  }

  await runValidation(validate, plan.nextBytes, "Proposed content failed validation");

  const backupDirectory = resolve(options.backupDirectory);
  await mkdir(backupDirectory, { recursive: true });

  const timestamp = formatTimestamp(now());
  const suffix = randomUUID();
  const originalName = basename(plan.sourcePath);
  const backupPath = join(backupDirectory, `${timestamp}-${suffix}-${originalName}.bak`);
  const receiptPath = join(backupDirectory, `${timestamp}-${suffix}-receipt.json`);

  await copyFile(plan.sourcePath, backupPath, fsConstants.COPYFILE_EXCL);
  const backupHash = sha256(await readFile(backupPath));
  if (backupHash !== plan.sourceHash) {
    await unlinkIfPresent(backupPath);
    throw new FileChangeError("BACKUP_INVALID", "Backup hash does not match the previewed source");
  }

  const sourceStat = await stat(plan.sourcePath);
  const tempPath = temporarySiblingPath(plan.sourcePath);
  let replacementCompleted = false;

  try {
    await writeExclusiveFile(tempPath, plan.nextBytes, sourceStat.mode);
    const tempBytes = await readFile(tempPath);
    if (sha256(tempBytes) !== plan.nextHash) {
      throw new FileChangeError("TEMP_INVALID", "Temporary file hash does not match the preview");
    }
    await runValidation(validate, tempBytes, "Temporary content failed validation");

    await replaceFile(tempPath, plan.sourcePath);
    replacementCompleted = true;

    const appliedBytes = await readFile(plan.sourcePath);
    if (sha256(appliedBytes) !== plan.nextHash) {
      throw new FileChangeError("POST_WRITE_INVALID", "Written file hash does not match the preview");
    }
    await runValidation(validate, appliedBytes, "Written content failed post-write validation");

    const receipt = Object.freeze({
      receiptVersion: RECEIPT_VERSION,
      createdAt: now().toISOString(),
      originalPath: plan.sourcePath,
      backupPath,
      originalHash: plan.sourceHash,
      appliedHash: plan.nextHash,
    });

    await writeJsonExclusive(receiptPath, receipt);
    return Object.freeze({ status: "applied", receiptPath, receipt });
  } catch (error) {
    if (replacementCompleted) {
      try {
        await restoreBytesFromBackup(backupPath, plan.sourcePath, plan.sourceHash);
      } catch (rollbackError) {
        throw new FileChangeError(
          "ROLLBACK_FAILED",
          `Apply failed and the automatic rollback also failed: ${rollbackError.message}`,
          { cause: error },
        );
      }
    }
    throw error;
  } finally {
    await unlinkIfPresent(tempPath);
  }
}

/**
 * Inspect whether a receipt can be safely restored without changing anything.
 *
 * @param {string} receiptPath
 */
export async function previewRestore(receiptPath) {
  const receipt = await readReceipt(receiptPath);
  const backupBytes = await readFile(receipt.backupPath);
  if (sha256(backupBytes) !== receipt.originalHash) {
    throw new FileChangeError("BACKUP_INVALID", "Backup no longer matches its receipt");
  }

  let currentHash = null;
  try {
    currentHash = sha256(await readFile(receipt.originalPath));
  } catch (error) {
    if (error.code !== "ENOENT") {
      throw error;
    }
  }

  let status;
  if (currentHash === receipt.originalHash) {
    status = "already-restored";
  } else if (currentHash === receipt.appliedHash) {
    status = "ready";
  } else if (currentHash === null) {
    status = "target-missing";
  } else {
    status = "changed-since-apply";
  }

  return Object.freeze({ receipt, currentHash, status });
}

/**
 * Restore a verified backup. Intervening target changes are refused unless the
 * caller explicitly opts in with `allowChangedTarget` after showing a preview.
 *
 * @param {string} receiptPath
 * @param {{
 *   allowChangedTarget?: boolean,
 *   isTargetInUse?: () => boolean | Promise<boolean>,
 *   validate?: (bytes: Buffer) => boolean | void | Promise<boolean | void>
 * }} [options]
 */
export async function restoreFile(receiptPath, options = {}) {
  const isTargetInUse = options.isTargetInUse ?? (() => false);
  if (await isTargetInUse()) {
    throw new FileChangeError(
      "TARGET_IN_USE",
      "Refusing to restore while the target game or process is running",
    );
  }

  const preview = await previewRestore(receiptPath);
  if (preview.status === "already-restored") {
    return Object.freeze({ status: "unchanged", receipt: preview.receipt });
  }
  if (preview.status !== "ready" && !options.allowChangedTarget) {
    throw new FileChangeError(
      "TARGET_CHANGED",
      `Restore target is ${preview.status}; preview and explicitly confirm before overwriting it`,
    );
  }

  const backupBytes = await readFile(preview.receipt.backupPath);
  if (options.validate) {
    await runValidation(options.validate, backupBytes, "Backup failed restore validation");
  }
  await restoreBytesFromBackup(
    preview.receipt.backupPath,
    preview.receipt.originalPath,
    preview.receipt.originalHash,
  );

  return Object.freeze({ status: "restored", receipt: preview.receipt });
}

export function sha256(bytes) {
  return createHash("sha256").update(bytes).digest("hex");
}

function assertPlan(plan) {
  if (
    !plan ||
    typeof plan.sourcePath !== "string" ||
    typeof plan.sourceHash !== "string" ||
    typeof plan.nextHash !== "string" ||
    !(plan.nextBytes instanceof Uint8Array) ||
    typeof plan.changed !== "boolean"
  ) {
    throw new TypeError("Invalid file change plan");
  }
}

async function runValidation(validate, bytes, message) {
  try {
    const result = await validate(Buffer.from(bytes));
    if (result === false) {
      throw new Error("validator returned false");
    }
  } catch (error) {
    if (error instanceof FileChangeError) {
      throw error;
    }
    throw new FileChangeError("VALIDATION_FAILED", `${message}: ${error.message}`, {
      cause: error,
    });
  }
}

async function writeExclusiveFile(path, bytes, mode) {
  const handle = await open(path, "wx", mode);
  try {
    await handle.writeFile(bytes);
    await handle.sync();
  } finally {
    await handle.close();
  }
}

async function writeJsonExclusive(path, value) {
  const handle = await open(path, "wx");
  try {
    await handle.writeFile(`${JSON.stringify(value, null, 2)}\n`, "utf8");
    await handle.sync();
  } finally {
    await handle.close();
  }
}

async function replaceFile(tempPath, targetPath) {
  try {
    await rename(tempPath, targetPath);
    return;
  } catch (error) {
    if (error.code !== "EEXIST" && error.code !== "EPERM") {
      throw error;
    }
  }

  const displacedPath = temporarySiblingPath(targetPath, "rollback");
  await rename(targetPath, displacedPath);
  try {
    await rename(tempPath, targetPath);
  } catch (error) {
    await rename(displacedPath, targetPath);
    throw error;
  }
  await unlinkIfPresent(displacedPath);
}

async function restoreBytesFromBackup(backupPath, targetPath, expectedHash) {
  const tempPath = temporarySiblingPath(targetPath, "restore");
  try {
    const targetMode = await stat(targetPath).then((value) => value.mode, () => undefined);
    await writeExclusiveFile(tempPath, await readFile(backupPath), targetMode);
    await replaceFile(tempPath, targetPath);
    if (sha256(await readFile(targetPath)) !== expectedHash) {
      throw new FileChangeError("RESTORE_INVALID", "Restored file hash does not match its receipt");
    }
  } finally {
    await unlinkIfPresent(tempPath);
  }
}

async function readReceipt(path) {
  let receipt;
  try {
    receipt = JSON.parse(await readFile(resolve(path), "utf8"));
  } catch (error) {
    throw new FileChangeError("RECEIPT_INVALID", `Could not read restore receipt: ${error.message}`, {
      cause: error,
    });
  }

  const requiredStrings = [
    "createdAt",
    "originalPath",
    "backupPath",
    "originalHash",
    "appliedHash",
  ];
  if (
    !receipt ||
    receipt.receiptVersion !== RECEIPT_VERSION ||
    requiredStrings.some((key) => typeof receipt[key] !== "string" || receipt[key] === "")
  ) {
    throw new FileChangeError("RECEIPT_INVALID", "Restore receipt has an unsupported shape or version");
  }

  return Object.freeze({ ...receipt });
}

function temporarySiblingPath(targetPath, purpose = "write") {
  return join(dirname(targetPath), `.${basename(targetPath)}.sim-controls-${purpose}-${randomUUID()}.tmp`);
}

function formatTimestamp(value) {
  if (!(value instanceof Date) || Number.isNaN(value.valueOf())) {
    throw new TypeError("now() must return a valid Date");
  }
  return value.toISOString().replaceAll(":", "-");
}

async function unlinkIfPresent(path) {
  try {
    await unlink(path);
  } catch (error) {
    if (error.code !== "ENOENT") {
      throw error;
    }
  }
}

