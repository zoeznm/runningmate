import { isRunningMateApiUrl, resolveApiUrl } from 'src/app/shared/api-base';

export interface AuthTokenPayload {
    access_token?: string;
    refresh_token?: string;
    token_type?: string;
    expires_in?: number;
    user?: unknown;
    data?: AuthTokenPayload;
    raw?: AuthTokenPayload;
}

const ACCESS_TOKEN_KEY = 'runningmate.auth.accessToken';
const REFRESH_TOKEN_KEY = 'runningmate.auth.refreshToken';
const AUTO_LOGIN_KEY = 'runningmate.auth.autoLogin';
const INSTALLED_KEY = '__runningmateAuthFetchInstalled';
const AUTH_REQUEST_TIMEOUT_MS = 10000;

let nativeFetch: typeof window.fetch | null = null;
let refreshPromise: Promise<boolean> | null = null;
let memoryAccessToken = '';
let memoryRefreshToken = '';
let memoryAutoLogin = false;

function storage(kind: 'local' | 'session'): Storage | null {
    try {
        return kind === 'local' ? window.localStorage : window.sessionStorage;
    } catch {
        return null;
    }
}

function safeGet(target: Storage | null, key: string): string {
    try {
        return target?.getItem(key) || '';
    } catch {
        return '';
    }
}

function safeSet(target: Storage | null, key: string, value: string): boolean {
    if (!target) return false;
    try {
        target.setItem(key, value);
        return true;
    } catch {
        return false;
    }
}

function safeRemove(target: Storage | null, key: string): void {
    try {
        target?.removeItem(key);
    } catch {
        // Ignore storage restrictions; auth state is also mirrored in memory.
    }
}

function authStorage(): Storage | null {
    const local = storage('local');
    const session = storage('session');
    if (safeGet(local, AUTO_LOGIN_KEY) === '1' && (safeGet(local, ACCESS_TOKEN_KEY) || safeGet(local, REFRESH_TOKEN_KEY))) return local;
    if (safeGet(session, ACCESS_TOKEN_KEY) || safeGet(session, REFRESH_TOKEN_KEY)) return session;
    return session || local;
}

function shouldAttachAuth(url: string): boolean {
    try {
        const parsed = new URL(resolveApiUrl(url), window.location.origin);
        if (!isRunningMateApiUrl(url)) return false;
        if (!parsed.pathname.startsWith('/api/')) return false;
        return ![
            '/api/auth/login',
            '/api/auth/register',
            '/api/auth/refresh',
            '/api/auth/logout',
            '/api/auth/check-username',
            '/api/auth/check-email',
            '/api/auth/forgot-password',
            '/api/auth/reset-password'
        ].includes(parsed.pathname);
    } catch {
        return false;
    }
}

export function isAuthProtectedUrl(url: string): boolean {
    return shouldAttachAuth(url);
}

function requestUrl(input: RequestInfo | URL): string {
    if (input instanceof Request) return input.url;
    return String(input);
}

function requestInput(input: RequestInfo | URL): RequestInfo | URL {
    if (input instanceof Request) return input;
    return resolveApiUrl(String(input));
}

async function fetchWithTimeout(
    fetcher: typeof window.fetch,
    input: RequestInfo | URL,
    init: RequestInit = {},
    timeoutMs: number = AUTH_REQUEST_TIMEOUT_MS
): Promise<Response> {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), timeoutMs);

    try {
        return await fetcher(requestInput(input), {
            credentials: 'same-origin',
            ...init,
            signal: init.signal || controller.signal
        });
    } finally {
        window.clearTimeout(timeout);
    }
}

export function getAccessToken(): string {
    return safeGet(authStorage(), ACCESS_TOKEN_KEY) || memoryAccessToken || '';
}

export function getRefreshToken(): string {
    return safeGet(authStorage(), REFRESH_TOKEN_KEY) || memoryRefreshToken || '';
}

export function hasAuthTokens(): boolean {
    return Boolean(getAccessToken() || getRefreshToken());
}

function tokenValue(payload: AuthTokenPayload | null | undefined, key: 'access_token' | 'refresh_token'): string {
    if (!payload) return '';
    const source = payload as Record<string, any>;
    return String(
        source[key]
        || source.data?.[key]
        || source.raw?.[key]
        || source.raw?.data?.[key]
        || ''
    );
}

export function saveAuthTokens(payload: AuthTokenPayload | null | undefined, autoLogin: boolean): boolean {
    const accessToken = tokenValue(payload, 'access_token');
    const refreshToken = tokenValue(payload, 'refresh_token');
    if (!accessToken || !refreshToken) return false;

    clearAuthTokens();
    memoryAccessToken = accessToken;
    memoryRefreshToken = refreshToken;
    memoryAutoLogin = autoLogin;

    const write = (target: Storage | null, persist: boolean): boolean => {
        if (!target) return false;
        const wroteAccess = safeSet(target, ACCESS_TOKEN_KEY, accessToken);
        const wroteRefresh = safeSet(target, REFRESH_TOKEN_KEY, refreshToken);
        const wroteAutoLogin = safeSet(target, AUTO_LOGIN_KEY, persist ? '1' : '0');
        if (!wroteAccess || !wroteRefresh || !wroteAutoLogin) return false;
        return safeGet(target, ACCESS_TOKEN_KEY) === accessToken && safeGet(target, REFRESH_TOKEN_KEY) === refreshToken;
    };

    if (autoLogin) {
        return write(storage('local'), true) || write(storage('session'), true) || true;
    }

    write(storage('session'), false);
    return true;
}

export function clearAuthTokens(): void {
    for (const target of [storage('local'), storage('session')]) {
        safeRemove(target, ACCESS_TOKEN_KEY);
        safeRemove(target, REFRESH_TOKEN_KEY);
        safeRemove(target, AUTO_LOGIN_KEY);
    }
    memoryAccessToken = '';
    memoryRefreshToken = '';
    memoryAutoLogin = false;
}

function isAccessPath(): boolean {
    if (typeof window === 'undefined') return true;
    const path = window.location.pathname.replace(/\/+$/, '') || '/';
    return path === '/access';
}

export function redirectToAccess(): void {
    if (typeof window === 'undefined' || isAccessPath()) return;
    window.location.replace('/access');
}

export function handleAuthFailure(redirect: boolean = true): void {
    clearAuthTokens();
    if (redirect) redirectToAccess();
}

export function authHeaderForUrl(url: string): Record<string, string> {
    if (!shouldAttachAuth(url)) return {};
    const token = getAccessToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function refreshAuthTokens(): Promise<boolean> {
    if (refreshPromise) return refreshPromise;

    refreshPromise = (async () => {
        const token = getRefreshToken();
        if (!token) {
            clearAuthTokens();
            return false;
        }

        try {
            const fetcher = nativeFetch || window.fetch.bind(window);
            const response = await fetchWithTimeout(fetcher, '/api/auth/refresh', {
                method: 'POST',
                cache: 'no-store',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: token })
            });
            const payload = await response.json().catch(() => null);
            const success = !!(payload?.success || payload?.data?.success);
            if (!response.ok || !success) {
                clearAuthTokens();
                return false;
            }

            const currentAutoLogin = safeGet(storage('local'), AUTO_LOGIN_KEY) === '1' || memoryAutoLogin;
            saveAuthTokens(payload?.data?.data || payload?.data || payload, currentAutoLogin);
            return true;
        } catch {
            return false;
        }
    })();

    try {
        return await refreshPromise;
    } finally {
        refreshPromise = null;
    }
}

async function fetchWithAuth(input: RequestInfo | URL, init: RequestInit = {}, retry: boolean = true): Promise<Response> {
    const fetcher = nativeFetch || window.fetch.bind(window);
    const resolvedInput = requestInput(input);
    const url = requestUrl(resolvedInput);
    const headers = new Headers(init.headers || (input instanceof Request ? input.headers : undefined));
    const token = shouldAttachAuth(url) ? getAccessToken() : '';
    if (token && !headers.has('Authorization')) {
        headers.set('Authorization', `Bearer ${token}`);
    }

    const response = await fetcher(resolvedInput, {
        ...init,
        credentials: init.credentials || 'same-origin',
        headers
    });

    if (response.status !== 401 || !retry || !shouldAttachAuth(url)) {
        if (response.status === 401 && shouldAttachAuth(url)) {
            handleAuthFailure();
        }
        return response;
    }

    const refreshed = await refreshAuthTokens();
    if (!refreshed) {
        handleAuthFailure();
        return response;
    }

    return fetchWithAuth(resolvedInput, init, false);
}

export function installAuthFetchInterceptor(): void {
    if (typeof window === 'undefined' || (window as any)[INSTALLED_KEY]) return;
    nativeFetch = window.fetch.bind(window);
    (window as any)[INSTALLED_KEY] = true;
    window.fetch = ((input: RequestInfo | URL, init?: RequestInit) => fetchWithAuth(input, init || {})) as typeof window.fetch;
}

export async function authenticatedUser(retry: boolean = true): Promise<unknown | null> {
    const fetcher = nativeFetch || window.fetch.bind(window);
    const response = await fetchWithTimeout(fetcher, '/api/auth/me', {
        cache: 'no-store',
        headers: authHeaderForUrl('/api/auth/me')
    })
        .catch(() => null);
    if (!response) return null;
    const payload = await response.json().catch(() => null);
    if (!response.ok) {
        if (response.status === 401) {
            if (retry && getRefreshToken() && await refreshAuthTokens()) {
                return authenticatedUser(false);
            }
            handleAuthFailure();
        }
        return null;
    }
    if (payload?.success) return payload.data || null;
    if (payload?.data?.success) return payload.data.data || null;
    if (payload?.code === 200 && payload?.data && !('success' in payload.data)) return payload.data;
    return null;
}

export async function ensureAuthenticated(): Promise<boolean> {
    const user = await authenticatedUser().catch(() => null);
    if (user) return true;
    if (!getAccessToken() && !getRefreshToken()) return false;
    if (getRefreshToken()) return await refreshAuthTokens();
    return false;
}
