import { getStore } from "@netlify/blobs";

const store = getStore("corescope-downloads");
const headers = {
  "Content-Type": "application/json; charset=utf-8",
  "Cache-Control": "no-store"
};

const json = (body, status = 200) => new Response(JSON.stringify(body), { status, headers });

async function readCount() {
  const entry = await store.getWithMetadata("total");
  const count = Number.parseInt(entry?.data, 10);

  return {
    count: Number.isFinite(count) ? count : 5,
    etag: entry?.etag
  };
}

export default async (request) => {
  if (request.method === "GET") {
    const { count } = await readCount();
    return json({ count });
  }

  if (request.method !== "POST") {
    return new Response("Method Not Allowed", {
      status: 405,
      headers: { ...headers, Allow: "GET, POST" }
    });
  }

  for (let attempt = 0; attempt < 4; attempt += 1) {
    const { count, etag } = await readCount();
    const nextCount = count + 1;

    try {
      if (etag) {
        await store.set("total", String(nextCount), { onlyIfMatch: etag });
      } else {
        await store.set("total", String(nextCount), { onlyIfNew: true });
      }
      return json({ count: nextCount });
    } catch {
      // Another download may have been recorded in the meantime; retry with its value.
    }
  }

  return json({ error: "Unable to record this download." }, 409);
};
