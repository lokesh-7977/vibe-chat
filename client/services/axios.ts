import axios, {
  type AxiosError,
  type AxiosInstance,
  type AxiosRequestHeaders,
  type InternalAxiosRequestConfig,
} from "axios";

interface ExtendedRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}
import { camelizeKeys, decamelizeKeys } from "../utils/data-transformers";
import { store } from "../store";
import { setAuth, clearAuth } from "../store/slices/auth-slice";

const DEFAULT_TIMEOUT_MS = 15_000;
const AUTH_REFRESH_PATH = "/auth/refresh";

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export function getAuthHeaders(): Record<string, string> {
  const token = store.getState().auth.accessToken;
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

const instance: AxiosInstance = axios.create({
  baseURL: apiBaseUrl,
  timeout: DEFAULT_TIMEOUT_MS,
  withCredentials: true,
});

instance.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  config.headers = (config.headers ?? {}) as AxiosRequestHeaders;
  if (config.data) config.data = decamelizeKeys(config.data);
  if (config.params) config.params = decamelizeKeys(config.params);
  const token = store.getState().auth.accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
let pendingRequests: Array<(token: string) => void> = [];

instance.interceptors.response.use(
  (response) => {
    if (response.data) response.data = camelizeKeys(response.data);
    return response;
  },
  async (error: unknown) => {
    if (!axios.isAxiosError(error)) return Promise.reject(error);
    if (error.response?.data) error.response.data = camelizeKeys(error.response.data);

    const status = error.response?.status;
    const url = error.config?.url ?? "";
    const isAuthEndpoint = url.includes("/auth/login") || url.includes("/auth/register") || url.includes(AUTH_REFRESH_PATH);

    const config = error.config as ExtendedRequestConfig | undefined;
    if (!config) return Promise.reject(error);

    if (status === 401 && !isAuthEndpoint && !config._retry) {
      if (isRefreshing) {
        return new Promise((resolve) => {
          pendingRequests.push((token: string) => {
            config.headers.Authorization = `Bearer ${token}`;
            resolve(instance(config));
          });
        });
      }

      isRefreshing = true;
      config._retry = true;

      try {
        const res = await axios.post(
          `${apiBaseUrl}${AUTH_REFRESH_PATH}`,
          {},
          { withCredentials: true },
        );
        const newToken = res.data?.data?.accessToken as string | undefined;
        if (newToken) {
          store.dispatch(setAuth({
            accessToken: newToken,
            user: store.getState().auth.user!,
          }));
          config.headers.Authorization = `Bearer ${newToken}`;
          pendingRequests.forEach((cb) => cb(newToken));
          pendingRequests = [];
          return instance(config);
        }
      } catch {
        // refresh failed
      } finally {
        isRefreshing = false;
      }

      pendingRequests.forEach((cb) => cb(""));
      pendingRequests = [];
      store.dispatch(clearAuth());
      if (typeof window !== "undefined") {
        window.location.href = "/auth";
      }
      return Promise.reject(error);
    }

    return Promise.reject(error as AxiosError);
  },
);

export default instance;
