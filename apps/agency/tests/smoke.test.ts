// Phase 1 smoke test: verifies agency app skeleton is structurally complete
describe("Agency App Skeleton", () => {
  test("has App component", async () => {
    const mod = await import("../src/App");
    expect(mod.default).toBeDefined();
  });

  test("has main entrypoint", async () => {
    const mod = await import("../src/main");
    expect(mod).toBeDefined();
  });

  test("vite config exists", async () => {
    const cfg = await import("../vite.config");
    expect(cfg.default.plugins).toBeDefined();
  });
});

export {};
