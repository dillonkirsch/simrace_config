#!/usr/bin/env node

import { readFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";

import { CatalogValidationError, validateCatalog } from "./domain/catalog.js";

/**
 * Run the dependency-free command-line interface.
 *
 * @param {string[]} args
 * @param {{out: (message: string) => void, error: (message: string) => void}} io
 * @returns {Promise<number>} process exit code
 */
export async function runCli(
  args,
  io = {
    out: (message) => console.log(message),
    error: (message) => console.error(message),
  },
) {
  if (args[0] === "catalog" && args[1] === "validate" && args.length === 3) {
    return validateCatalogCommand(args[2], io);
  }

  io.error(usage());
  return 2;
}

async function validateCatalogCommand(path, io) {
  let input;
  try {
    input = JSON.parse(await readFile(path, "utf8"));
  } catch (error) {
    io.error(`Could not read catalog: ${error.message}`);
    return 1;
  }

  try {
    const catalog = validateCatalog(input);
    io.out(
      [
        "Catalog is valid.",
        `Device: ${catalog.virtualDevice.identity}`,
        `Bindings: ${catalog.bindings.length}`,
        ...catalog.bindings.map(
          ({ actionId, virtualButton }) => `- ${actionId}: SimHub button ${virtualButton}`,
        ),
      ].join("\n"),
    );
    return 0;
  } catch (error) {
    if (error instanceof CatalogValidationError) {
      io.error(error.message);
      return 1;
    }
    throw error;
  }
}

function usage() {
  return [
    "Usage:",
    "  node src/cli.js catalog validate <catalog.json>",
    "",
    "This command is read-only. No simulator files are modified.",
  ].join("\n");
}

const isEntryPoint =
  process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;

if (isEntryPoint) {
  process.exitCode = await runCli(process.argv.slice(2));
}
