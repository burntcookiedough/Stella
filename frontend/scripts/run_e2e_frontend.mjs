import { spawn } from "node:child_process";

const npmCommand = process.platform === "win32" ? "npm.cmd" : "npm";
const env = {
  ...process.env,
  VITE_API_BASE_URL: "http://127.0.0.1:8100",
  VITE_WS_BASE_URL: "ws://127.0.0.1:8100/v1/chat/ws",
};

function run(command, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { env, stdio: "inherit", shell: true });
    child.on("exit", (code) => {
      if (code === 0) {
        resolve();
        return;
      }
      reject(new Error(`${command} ${args.join(" ")} exited with code ${code ?? 1}`));
    });
  });
}

async function main() {
  await run(npmCommand, ["run", "build"]);

  const preview = spawn(npmCommand, ["run", "preview:e2e"], {
    env,
    stdio: "inherit",
    shell: true,
  });

  const shutdown = () => {
    preview.kill("SIGTERM");
  };

  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);

  preview.on("exit", (code) => {
    process.exit(code ?? 0);
  });
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
