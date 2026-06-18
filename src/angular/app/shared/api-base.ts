export const RUNNINGMATE_API_ORIGIN = 'https://run.myrunningmate.com';

const API_PATH_PREFIX = '/api/';
const LOCAL_NATIVE_PROTOCOLS = new Set(['capacitor:', 'ionic:', 'file:']);

function currentLocation(): Location | null {
    return typeof window === 'undefined' ? null : window.location;
}

function isApiPath(pathname: string): boolean {
    return pathname === '/api' || pathname.startsWith(API_PATH_PREFIX);
}

function isRootedApiPath(input: string): boolean {
    return input === '/api' || input.startsWith(API_PATH_PREFIX) || input.startsWith('/api?');
}

export function isNativeLocalOrigin(): boolean {
    const location = currentLocation();
    if (!location) return false;
    return LOCAL_NATIVE_PROTOCOLS.has(location.protocol);
}

export function resolveApiUrl(input: string): string {
    const raw = String(input || '');
    const location = currentLocation();
    if (!raw || !location || !isNativeLocalOrigin()) return raw;

    if (isRootedApiPath(raw)) {
        return `${RUNNINGMATE_API_ORIGIN}${raw}`;
    }

    try {
        const parsed = new URL(raw, location.href || 'capacitor://localhost/');
        if (LOCAL_NATIVE_PROTOCOLS.has(parsed.protocol) && isApiPath(parsed.pathname)) {
            return `${RUNNINGMATE_API_ORIGIN}${parsed.pathname}${parsed.search}${parsed.hash}`;
        }
        return raw;
    } catch {
        return isRootedApiPath(raw) ? `${RUNNINGMATE_API_ORIGIN}${raw}` : raw;
    }
}

export function isRunningMateApiUrl(input: string): boolean {
    const location = currentLocation();
    if (!location) return false;

    try {
        const parsed = new URL(resolveApiUrl(input), location.origin);
        if (!isApiPath(parsed.pathname)) return false;
        return parsed.origin === location.origin || parsed.origin === RUNNINGMATE_API_ORIGIN;
    } catch {
        return false;
    }
}
