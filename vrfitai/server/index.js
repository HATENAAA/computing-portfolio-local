import { mkdirSync } from "node:fs";
import {dirname,resolve} from "node:path";
import { createApp } from "./app.js";
import { localAIConfig, localEnvironment } from "./local-config.js";
const runtime = localEnvironment();
const database=runtime.VRFITAI_DB || "data/vrfitai.sqlite";
mkdirSync(dirname(resolve(database)), { recursive: true });
const { app, close } = createApp({
  database,
  readConfig: localAIConfig,
  logger: (record) => console.log(JSON.stringify(record)),
});
const port = Number(runtime.PORT || 8780),
  host = runtime.HOST || "127.0.0.1";
const server = app.listen(port, host, () =>
  console.log(`VRFitAI: http://${host}:${port}`),
);
for (const signal of ["SIGINT", "SIGTERM"])
  process.on(signal, () =>
    server.close(() => {
      close();
      process.exit(0);
    }),
  );
