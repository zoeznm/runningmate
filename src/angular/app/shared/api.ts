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

const delay = (ms: number): Promise<void> => new Promise((resolve) => window.setTimeout(resolve, ms));

export function standardApiError(kind: ApiErrorKind, overrides: Partial<ApiError> = {}): ApiError {
    return {
        kind,
        message: overrides.message || ERROR_MESSAGES[kind],
        status: overrides.status,
        details: overrides.details
    };
}

export function apiErrorMessage(error?: ApiError | null): string {
    return error?.message || ERROR_MESSAGES.unknown;
}

export function isApiResult(value: unknown): value is ApiResult {
    return Boolean(value && typeof value === 'object' && 'success' in (value as Record<string, unknown>));
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
        message: isHtml
            ? '서버가 API 응답 대신 화면 HTML을 반환했습니다. 배포 라우팅을 확인해주세요.'
            : '서버 응답 형식이 올바르지 않습니다. 다시 시도해주세요.',
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
    return {
        success: false,
        error: standardApiError(kind, {
            status,
            message: normalizeMessage(payload) || ERROR_MESSAGES[kind],
            details: payload
        }),
        message: normalizeMessage(payload),
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
    const { retries, retryDelayMs, timeoutMs: _timeoutMs, signal, ...requestOptions } = options;
    const isProtected = isAuthProtectedUrl(requestUrl);

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
            handleAuthFailure();
        }
        const payload = await readPayload(response).catch((error) => {
            if (isApiError(error)) throw error;
            throw standardApiError('parse', { details: error });
        });

        if (response.status >= 500) {
            return {
                success: false,
                error: standardApiError('server', {
                    status: response.status,
                    message: normalizeMessage(payload) || ERROR_MESSAGES.server,
                    details: payload
                }),
                raw: payload
            };
        }

        if (!response.ok) {
            return {
                success: false,
                error: standardApiError('client', {
                    status: response.status,
                    message: normalizeMessage(payload) || ERROR_MESSAGES.client,
                    details: payload
                }),
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
            message: normalizeMessage(payload),
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
