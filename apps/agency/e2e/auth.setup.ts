import { expect, request as playwrightRequest, test } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import { ADMIN_STORAGE_STATE, AUTH_STATE_DIR, SUPPORT_STORAGE_STATE } from "./auth-state";

const PASSWORD = "Test1234!";

async function writeStorageStateForUser(email: string, path: string) {
  const api = await playwrightRequest.newContext({
    baseURL: "http://127.0.0.1:8000",
  });

  const response = await api.post("/auth/login", {
    data: {
      email,
      password: PASSWORD,
    },
  });

  expect(response.ok(), `login failed for ${email}`).toBeTruthy();
  await api.storageState({ path });
  await api.dispose();
}

test("create authenticated storage states", async () => {
  await mkdir(AUTH_STATE_DIR, { recursive: true });
  await writeStorageStateForUser("agency.admin@akarai.test", ADMIN_STORAGE_STATE);
  await writeStorageStateForUser("support@akarai.test", SUPPORT_STORAGE_STATE);
});
