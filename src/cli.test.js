import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, it } from "node:test";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

import { runCli } from "./cli.js";

const temporaryDirectories = [];
const execFileAsync = promisify(execFile);
const cliPath = fileURLToPath(new URL("./cli.js", import.meta.url));

function captureIo() {
  const output = [];
  const errors = [];
  return {
    output,
    errors,
    io: {
      out: (message) => output.push(message),
      error: (message) => errors.push(message),
    },
  };
}

async function writeCatalog(value) {
  const directory = await mkdtemp(join(tmpdir(), "sim-controls-cli-"));
  temporaryDirectories.push(directory);
  const path = join(directory, "catalog.json");
  await writeFile(path, JSON.stringify(value));
  return path;
}

afterEach(async () => {
  await Promise.all(
    temporaryDirectories.splice(0).map((directory) =>
      rm(directory, { recursive: true, force: true }),
    ),
  );
});

describe("CLI", () => {
  it("validates and summarizes a manual catalog without writing it", async () => {
    const path = await writeCatalog({
      schemaVersion: 1,
      virtualDevice: {
        provider: "simhub-control-mapper",
        identity: "SimHub output",
      },
      bindings: [{ actionId: "pit_limiter", virtualButton: 7 }],
    });
    const before = await import("node:fs/promises").then(({ readFile }) =>
      readFile(path, "utf8"),
    );
    const captured = captureIo();

    const exitCode = await runCli(["catalog", "validate", path], captured.io);

    assert.equal(exitCode, 0);
    assert.match(captured.output[0], /Catalog is valid/);
    assert.match(captured.output[0], /pit_limiter: SimHub button 7/);
    assert.deepEqual(captured.errors, []);
    const after = await import("node:fs/promises").then(({ readFile }) =>
      readFile(path, "utf8"),
    );
    assert.equal(after, before);
  });

  it("runs as a real command-line entry point", async () => {
    const path = await writeCatalog({
      schemaVersion: 1,
      virtualDevice: {
        provider: "simhub-control-mapper",
        identity: "SimHub output",
      },
      bindings: [{ actionId: "pit_limiter", virtualButton: 7 }],
    });

    const { stdout, stderr } = await execFileAsync(process.execPath, [
      cliPath,
      "catalog",
      "validate",
      path,
    ]);

    assert.match(stdout, /Catalog is valid/);
    assert.match(stdout, /pit_limiter: SimHub button 7/);
    assert.equal(stderr, "");
  });

  it("reports all catalog validation issues", async () => {
    const path = await writeCatalog({
      schemaVersion: 99,
      virtualDevice: null,
      bindings: [],
    });
    const captured = captureIo();

    const exitCode = await runCli(["catalog", "validate", path], captured.io);

    assert.equal(exitCode, 1);
    assert.match(captured.errors[0], /schemaVersion must be 1/);
    assert.match(captured.errors[0], /virtualDevice must be an object/);
  });

  it("distinguishes malformed JSON from a schema error", async () => {
    const directory = await mkdtemp(join(tmpdir(), "sim-controls-cli-"));
    temporaryDirectories.push(directory);
    const path = join(directory, "broken.json");
    await writeFile(path, "{not json");
    const captured = captureIo();

    const exitCode = await runCli(["catalog", "validate", path], captured.io);

    assert.equal(exitCode, 1);
    assert.match(captured.errors[0], /Could not read catalog/);
  });

  it("prints usage and returns 2 for an unknown command", async () => {
    const captured = captureIo();

    const exitCode = await runCli([], captured.io);

    assert.equal(exitCode, 2);
    assert.match(captured.errors[0], /catalog validate/);
    assert.match(captured.errors[0], /read-only/);
  });
});
