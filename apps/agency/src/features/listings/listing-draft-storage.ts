import { getTenantSession } from "@/lib/session/auth-session";
import type { StagedListingPhoto, StagedListingPhotoStatus } from "./listing-media";
import type { DraftViewingSlot } from "./viewing-slot-draft";

const DRAFT_VERSION = "v1";
const DB_NAME = "akarai-agency-listing-drafts";
const STORE_NAME = "listing-photos";

type DraftPayload = {
  formData: Record<string, string>;
  stagedViewingSlots: DraftViewingSlot[];
  updatedAt: string;
};

type StoredPhotoRecord = {
  draftKey: string;
  id: string;
  file: Blob;
  name: string;
  type: string;
  lastModified: number;
  status: StagedListingPhotoStatus;
  message: string;
  moderationLabel: string | null;
  moderationScore: number | null;
};

function buildDraftKey(): string {
  const session = getTenantSession();
  const tenantId = session?.tenantId || "tenant";
  const userId = session?.userId || "user";
  return `akarai:agency:listing-draft:${DRAFT_VERSION}:new:${tenantId}:${userId}`;
}

function getStorageKey(draftKey: string): string {
  return `${draftKey}:form`;
}

function hasWindowStorage(): boolean {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function openDraftDb(): Promise<IDBDatabase | null> {
  if (typeof indexedDB === "undefined") {
    return Promise.resolve(null);
  }

  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, { keyPath: ["draftKey", "id"] });
        store.createIndex("draftKey", "draftKey", { unique: false });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function replacePhotoRecords(draftKey: string, stagedPhotos: StagedListingPhoto[]): Promise<void> {
  const db = await openDraftDb();
  if (!db) {
    return;
  }

  await new Promise<void>((resolve, reject) => {
    const transaction = db.transaction(STORE_NAME, "readwrite");
    const store = transaction.objectStore(STORE_NAME);
    const index = store.index("draftKey");
    const existingRequest = index.getAllKeys(draftKey);

    existingRequest.onsuccess = () => {
      for (const key of existingRequest.result) {
        store.delete(key);
      }

      for (const photo of stagedPhotos) {
        const record: StoredPhotoRecord = {
          draftKey,
          id: photo.id,
          file: photo.file,
          name: photo.file.name,
          type: photo.file.type,
          lastModified: photo.file.lastModified,
          status: photo.status,
          message: photo.message,
          moderationLabel: photo.moderationLabel,
          moderationScore: photo.moderationScore,
        };
        store.put(record);
      }
    };
    existingRequest.onerror = () => reject(existingRequest.error);
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error);
  });
  db.close();
}

async function readPhotoRecords(draftKey: string): Promise<StagedListingPhoto[]> {
  const db = await openDraftDb();
  if (!db) {
    return [];
  }

  const records = await new Promise<StoredPhotoRecord[]>((resolve, reject) => {
    const transaction = db.transaction(STORE_NAME, "readonly");
    const store = transaction.objectStore(STORE_NAME);
    const index = store.index("draftKey");
    const request = index.getAll(draftKey);
    request.onsuccess = () => resolve((request.result as StoredPhotoRecord[]) || []);
    request.onerror = () => reject(request.error);
  });
  db.close();

  return records.map((record) => ({
    id: record.id,
    file: new File([record.file], record.name, {
      type: record.type,
      lastModified: record.lastModified,
    }),
    status: record.status,
    message: record.message,
    moderationLabel: record.moderationLabel,
    moderationScore: record.moderationScore,
  }));
}

async function clearPhotoRecords(draftKey: string): Promise<void> {
  const db = await openDraftDb();
  if (!db) {
    return;
  }

  await new Promise<void>((resolve, reject) => {
    const transaction = db.transaction(STORE_NAME, "readwrite");
    const store = transaction.objectStore(STORE_NAME);
    const index = store.index("draftKey");
    const request = index.getAllKeys(draftKey);
    request.onsuccess = () => {
      for (const key of request.result) {
        store.delete(key);
      }
    };
    request.onerror = () => reject(request.error);
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error);
  });
  db.close();
}

export async function loadListingDraft(): Promise<{
  formData: Record<string, string>;
  stagedPhotos: StagedListingPhoto[];
  stagedViewingSlots: DraftViewingSlot[];
}> {
  const draftKey = buildDraftKey();
  let formData: Record<string, string> = {};
  let stagedViewingSlots: DraftViewingSlot[] = [];

  if (hasWindowStorage()) {
    try {
      const raw = window.localStorage.getItem(getStorageKey(draftKey));
      if (raw) {
        const parsed = JSON.parse(raw) as DraftPayload;
        formData = parsed.formData || {};
        stagedViewingSlots = parsed.stagedViewingSlots || [];
      }
    } catch {
      formData = {};
      stagedViewingSlots = [];
    }
  }

  const stagedPhotos = await readPhotoRecords(draftKey);
  return { formData, stagedPhotos, stagedViewingSlots };
}

export async function saveListingDraft(
  formData: Record<string, string>,
  stagedPhotos: StagedListingPhoto[],
  stagedViewingSlots: DraftViewingSlot[],
): Promise<void> {
  const draftKey = buildDraftKey();

  if (hasWindowStorage()) {
    window.localStorage.setItem(
      getStorageKey(draftKey),
      JSON.stringify({
        formData,
        stagedViewingSlots,
        updatedAt: new Date().toISOString(),
      } satisfies DraftPayload),
    );
  }

  await replacePhotoRecords(draftKey, stagedPhotos);
}

export async function clearListingDraft(): Promise<void> {
  const draftKey = buildDraftKey();
  if (hasWindowStorage()) {
    window.localStorage.removeItem(getStorageKey(draftKey));
  }
  await clearPhotoRecords(draftKey);
}
