import { describe, test, expect, vi, beforeAll } from "vitest";
import * as fs from "fs";
import * as path from "path";

beforeAll(() => {
  if (!document.getElementById("root")) {
    const root = document.createElement("div");
    root.id = "root";
    document.body.appendChild(root);
  }
});

describe("User App Skeleton", () => {
  test("has App component", async () => {
    const mod = await import("../src/App");
    expect(mod.default).toBeDefined();
  });

  test("has main entrypoint file", () => {
    const mainPath = path.resolve(__dirname, "../src/main.tsx");
    expect(fs.existsSync(mainPath)).toBe(true);
    const content = fs.readFileSync(mainPath, "utf-8");
    expect(content).toContain("createRoot");
    expect(content).toContain("App");
  });

  test("vite config file exists", () => {
    const configPath = path.resolve(__dirname, "../vite.config.ts");
    expect(fs.existsSync(configPath)).toBe(true);
    const content = fs.readFileSync(configPath, "utf-8");
    expect(content).toContain("defineConfig");
  });
});

export {};
