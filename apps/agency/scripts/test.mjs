import { spawn } from "node:child_process";

const forwardedArgs = process.argv.slice(2).filter((arg) => arg !== "--run" && arg !== "run");
const child = spawn("vitest", ["run", ...forwardedArgs], {
  stdio: ["ignore", "pipe", "pipe"],
  detached: true,
});

let exiting = false;

const killProcessGroup = (signal = "SIGTERM") => {
  if (exiting || child.killed) {
    return;
  }

  exiting = true;

  try {
    if (process.platform === "win32") {
      child.kill(signal);
    } else {
      process.kill(-child.pid, signal);
    }
  } catch {
    // The process group may already be gone.
  }
};

const handlePipeError = (error) => {
  if (error?.code === "EPIPE") {
    killProcessGroup();
  }
};

process.stdout.on("error", handlePipeError);
process.stderr.on("error", handlePipeError);
process.on("SIGINT", () => killProcessGroup("SIGINT"));
process.on("SIGTERM", () => killProcessGroup("SIGTERM"));

child.stdout.pipe(process.stdout);
child.stderr.pipe(process.stderr);

child.on("error", (error) => {
  console.error(error);
  process.exitCode = 1;
});

child.on("close", (code, signal) => {
  exiting = true;

  if (signal) {
    process.exitCode = 1;
    return;
  }

  process.exitCode = code ?? 1;
});
