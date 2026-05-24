type AnyRecord = Record<string, unknown>;

function isPlainObject(value: unknown): value is AnyRecord {
  if (value === null || typeof value !== "object") return false;
  if (Array.isArray(value)) return false;
  const proto = Object.getPrototypeOf(value);
  return proto === Object.prototype || proto === null;
}

function toCamelKey(key: string) {
  return key.replace(/_([a-z0-9])/g, (_, c: string) => c.toUpperCase());
}

function toSnakeKey(key: string) {
  return key
    .replace(/([A-Z])/g, "_$1")
    .replace(/-/g, "_")
    .toLowerCase();
}

export function camelizeKeys<T>(value: T): T {
  if (Array.isArray(value)) return value.map(camelizeKeys) as T;
  if (!isPlainObject(value)) return value;

  const out: AnyRecord = {};
  for (const [k, v] of Object.entries(value)) out[toCamelKey(k)] = camelizeKeys(v);
  return out as T;
}

export function decamelizeKeys<T>(value: T): T {
  if (Array.isArray(value)) return value.map(decamelizeKeys) as T;
  if (!isPlainObject(value)) return value;

  const out: AnyRecord = {};
  for (const [k, v] of Object.entries(value)) out[toSnakeKey(k)] = decamelizeKeys(v);
  return out as T;
}

