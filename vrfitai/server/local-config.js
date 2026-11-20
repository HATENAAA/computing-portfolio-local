import { readFileSync } from "node:fs";
import { parseEnv } from "node:util";
import { aiConfig } from "./assistant.js";

const defaultFile = new URL("../.env", import.meta.url);

export function localEnvironment(file = defaultFile, env = process.env) {
  try {
    return { ...parseEnv(readFileSync(file, "utf8")), ...env };
  } catch (error) {
    if (error.code === "ENOENT") return env;
    throw error;
  }
}

export function localAIConfig() {
  return aiConfig(localEnvironment());
}
