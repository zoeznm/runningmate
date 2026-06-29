import { authHeaderForUrl, getRefreshToken, handleAuthFailure, isAuthProtectedUrl, refreshAuthTokens } from 'src/app/shared/auth';
import { resolveApiUrl } from 'src/app/shared/api-base';

export type ApiErrorKind = 'network' | 'parse' | 'server' | 'timeout' | 'client' | 'unknown';

export interface ApiError {
    kind: ApiErrorKind;
    message: string;
    status?: number;
    details?: unknown;
}

export interface ApiResult<T = unknown> {
    success: boolean;
    data?: T;
    error?: ApiError;
    message?: string;
    raw?: unknown;
}

export interface ApiFetchOptions extends RequestInit {
    authFailureRedirect?: boolean;
    retries?: number;
    retryDelayMs?: number;
    timeoutMs?: number;
}

const ERROR_MESSAGES: Record<ApiErrorKind, string> = {
    network: '인터넷 연결을 확인해줘',
    parse: '응답을 읽지 못했어. 다시 시도해줘',
    server: '잠깐 문제가 생겼어. 다시 시도해줘',
    timeout: '응답이 너무 늦어. 다시 시도해줘',
    client: '요청을 처리하지 못했어.',
    unknown: '잠깐 문제가 생겼어. 다시 시도해줘'
};

const TECHNICAL_MESSAGE_PATTERNS: RegExp[] = [
    /\b(TypeError|ReferenceError|SyntaxError|RangeError|DOMException|AbortError|NSURLError|URLError|NSError|Exception|Traceback|Stack trace|SQL|Postgres|Prisma|Sequelize)\b/i,
    /\b(ECONNRESET|ECONNREFUSED|ENOTFOUND|ETIMEDOUT|EAI_AGAIN|NetworkError|FetchError|AbortError)\b/i,
    /\b(Unable to|Could not|Cannot|Failed to|invalid state|current state|status code|HTTP\s?\d{3}|Unexpected token|JSON|undefined|null|NaN)\b/i,
    /(<\/?[a-z][\s\S]*>|[{}])/i,
    /(\/api\/|https?:\/\/|file:\/\/|\.swift\b|\.tsx?\b|\.jsx?\b|line\s+\d+|column\s+\d+)/i
];

const STATUS_ERROR_MESSAGES: Record<number, string> = {
    400: '입력한 내용을 다시 확인해줘.',
    401: '로그인이 만료됐어. 다시 로그인해줘.',
    403: '이 작업을 할 권한이 없어.',
    404: '대상을 찾지 못했어.',
    409: '이미 처리된 요청이야.',
    413: '파일 용량이 너무 커.',
    429: '요청이 많아 잠시 후 다시 시도해줘.'
};

const delay = (ms: number): Promise<void> => new Promise((resolve) => window.setTimeout(resolve, ms));

export function standardApiError(kind: ApiErrorKind, overrides: Partial<ApiError> = {}): ApiError {
    const fallback = apiErrorFallback(kind, overrides.status);
    return {
        kind,
        message: safeUserMessage(overrides.message, fallback),
        status: overrides.status,
        details: overrides.details
    };
}

export function apiErrorMessage(error?: ApiError | null, fallback?: string): string {
    return safeUserMessage(error?.message, fallback || apiErrorFallback(error?.kind, error?.status));
}

export function payloadUserMessage(payload: unknown, fallback: string = ERROR_MESSAGES.unknown): string {
    return safeUserMessage(normalizeMessage(payload), fallback);
}

export function safeUserMessage(value: unknown, fallback: string = ERROR_MESSAGES.unknown): string {
    const fallbackText = String(fallback || '').trim();
    const raw = extractMessage(value).trim();
    if (!raw) return fallbackText;

    const message = raw.replace(/\s+/g, ' ').trim();
    if (!message) return fallbackText;
    if (message.length > 160) return fallbackText;
    if (isTechnicalMessage(message)) return fallbackText;
    return message;
}

export function isApiResult(value: unknown): value is ApiResult {
    return Boolean(value && typeof value === 'object' && 'success' in (value as Record<string, unknown>));
}

function apiErrorFallback(kind: ApiErrorKind | undefined, status?: number): string {
    if (status && STATUS_ERROR_MESSAGES[status]) return STATUS_ERROR_MESSAGES[status];
    if (status && status >= 500) return ERROR_MESSAGES.server;
    return kind ? ERROR_MESSAGES[kind] : ERROR_MESSAGES.unknown;
}

function extractMessage(value: unknown): string {
    if (typeof value === 'string') return value;
    if (value instanceof Error) return value.message || '';
    if (value && typeof value === 'object') {
        const source = value as Record<string, unknown>;
        if (typeof source['message'] === 'string') return source['message'];
        if (typeof source['localizedDescription'] === 'string') return source['localizedDescription'];
        if (source['error']) return extractMessage(source['error']);
    }
    return '';
}

function isTechnicalMessage(message: string): boolean {
    return TECHNICAL_MESSAGE_PATTERNS.some((pattern) => pattern.test(message));
}

function normalizeData<T>(payload: unknown): T {
    if (payload && typeof payload === 'object' && 'data' in (payload as Record<string, unknown>)) {
        return (payload as Record<string, unknown>)['data'] as T;
    }
    return payload as T;
}

function normalizeMessage(payload: unknown): string {
    if (!payload || typeof payload !== 'object') return '';
    const source = payload as Record<string, unknown>;
    const message = source['message'] ?? source['error'];
    if (typeof message === 'string') return message;
    if ('data' in source) return normalizeMessage(source['data']);
    return '';
}

function normalizeStatus(payload: unknown): number | undefined {
    if (!payload || typeof payload !== 'object') return undefined;
    const code = (payload as Record<string, unknown>)['code'];
    if (code === undefined || code === null || code === '') return undefined;
    const status = typeof code === 'number' ? code : Number(code);
    return Number.isFinite(status) ? status : undefined;
}

function isFailureStatus(status?: number): boolean {
    return typeof status === 'number' && (status < 200 || status >= 300);
}

function failureKind(status?: number): ApiErrorKind {
    return typeof status === 'number' && status >= 500 ? 'server' : 'client';
}

function textResponseMessage(text: string): string {
    return String(text || '')
        .replace(/<script[\s\S]*?<\/script>/gi, ' ')
        .replace(/<style[\s\S]*?<\/style>/gi, ' ')
        .replace(/<[^>]+>/g, ' ')
        .replace(/\s+/g, ' ')
        .trim()
        .slice(0, 240);
}

function looksLikeHtmlResponse(response: Response, text: string): boolean {
    const contentType = response.headers.get('content-type') || '';
    const sample = String(text || '').trim().slice(0, 120).toLowerCase();
    return contentType.includes('text/html')
        || sample.startsWith('<!doctype html')
        || sample.startsWith('<html')
        || sample.includes('<body');
}

function nonJsonPayload(response: Response, text: string, error: unknown): ApiResult {
    const isHtml = looksLikeHtmlResponse(response, text);
    const fallback = textResponseMessage(text);
    return {
        success: false,
        message: isHtml ? ERROR_MESSAGES.server : ERROR_MESSAGES.parse,
        data: {
            response_status: response.status,
            content_type: response.headers.get('content-type') || '',
            body_preview: fallback,
            parse_error: error instanceof Error ? error.message : String(error || '')
        },
        raw: text
    };
}

function failureResult<T>(payload: unknown, status?: number): ApiResult<T> {
    const kind = failureKind(status);
    const error = standardApiError(kind, {
        status,
        message: normalizeMessage(payload),
        details: payload
    });
    return {
        success: false,
        error,
        message: error.message,
        raw: payload
    };
}

async function readPayload(response: Response): Promise<unknown> {
    const text = await response.text();
    if (!text) return null;

    try {
        return JSON.parse(text);
    } catch (error) {
        if (!response.ok) {
            return {
                success: false,
                message: textResponseMessage(text),
                raw: text
            };
        }
        return nonJsonPayload(response, text, error);
    }
}

async function fetchOnce<T>(url: string, options: ApiFetchOptions, authRetried: boolean = false): Promise<ApiResult<T>> {
    const requestUrl = resolveApiUrl(url);
    const timeoutMs = options.timeoutMs ?? 20000;
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
    const {
        authFailureRedirect,
        retries,
        retryDelayMs,
        timeoutMs: _timeoutMs,
        signal,
        ...requestOptions
    } = options;
    const isProtected = isAuthProtectedUrl(requestUrl);
    const shouldRedirectAuthFailure = authFailureRedirect !== false;

    try {
        const response = await fetch(requestUrl, {
            cache: 'no-store',
            ...requestOptions,
            headers: {
                ...authHeaderForUrl(requestUrl),
                ...(requestOptions.headers || {})
            },
            signal: signal || controller.signal
        });
        if (response.status === 401 && isProtected && !authRetried && getRefreshToken() && await refreshAuthTokens()) {
            window.clearTimeout(timeout);
            return fetchOnce<T>(url, options, true);
        }
        if (response.status === 401 && isProtected) {
            handleAuthFailure(shouldRedirectAuthFailure, !getRefreshToken());
        }
        const payload = await readPayload(response).catch((error) => {
            if (isApiError(error)) throw error;
            throw standardApiError('parse', { details: error });
        });

        if (response.status >= 500) {
            const error = standardApiError('server', {
                status: response.status,
                message: normalizeMessage(payload),
                details: payload
            });
            return {
                success: false,
                error,
                message: error.message,
                raw: payload
            };
        }

        if (!response.ok) {
            const error = standardApiError('client', {
                status: response.status,
                message: normalizeMessage(payload),
                details: payload
            });
            return {
                success: false,
                error,
                message: error.message,
                raw: payload
            };
        }

        const payloadStatus = normalizeStatus(payload);
        if (isFailureStatus(payloadStatus)) {
            return failureResult<T>(payload, payloadStatus);
        }

        if (isApiResult(payload) && payload.success === false) {
            return failureResult<T>(payload, payloadStatus);
        }

        const data = normalizeData(payload);
        if (isApiResult(data) && data.success === false) {
            return failureResult<T>(payload, payloadStatus);
        }

        return {
            success: true,
            data: data as T,
            message: safeUserMessage(normalizeMessage(payload), ''),
            raw: payload
        };
    } catch (error) {
        if (isApiError(error)) {
            return { success: false, error };
        }

        const aborted = error instanceof DOMException && error.name === 'AbortError';
        return {
            success: false,
            error: aborted
                ? standardApiError('timeout', { details: error })
                : standardApiError('network', { details: error })
        };
    } finally {
        window.clearTimeout(timeout);
    }
}

export async function apiFetch<T = unknown>(url: string, options: ApiFetchOptions = {}): Promise<ApiResult<T>> {
    const retries = Math.max(0, options.retries ?? 1);
    const retryDelayMs = Math.max(0, options.retryDelayMs ?? 350);

    for (let attempt = 0; attempt <= retries; attempt++) {
        const result = await fetchOnce<T>(url, options);
        if (result.success || result.error?.kind !== 'network' || attempt === retries) {
            return result;
        }
        await delay(retryDelayMs * (attempt + 1));
    }

    return {
        success: false,
        error: standardApiError('unknown')
    };
}

export function jsonRequest<T = unknown>(url: string, method: string, body?: unknown, options: ApiFetchOptions = {}): Promise<ApiResult<T>> {
    return apiFetch<T>(url, {
        ...options,
        method,
        headers: {
            'Content-Type': 'application/json',
            ...(options.headers || {})
        },
        body: body === undefined ? options.body : JSON.stringify(body)
    });
}

export function isApiError(value: unknown): value is ApiError {
    return Boolean(value && typeof value === 'object' && 'kind' in (value as Record<string, unknown>));
}
