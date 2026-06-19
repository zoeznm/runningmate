interface RequestOptions {
    timeout?: number;
}

export default class Request {
    constructor() { }

    public async post(url: string, data: any = {}, options: RequestOptions = {}) {
        const timeout = Math.max(1000, Number(options.timeout || 10000));
        const controller = new AbortController();
        const timeoutId = window.setTimeout(() => controller.abort(), timeout);
        const body = new URLSearchParams(Object.entries(data || {}).reduce((params: Record<string, string>, [key, value]) => {
            params[key] = typeof value === "string" ? value : JSON.stringify(value);
            return params;
        }, {}));

        try {
            const response = await fetch(url, {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
                },
                body,
                signal: controller.signal
            });
            const text = await response.text();
            try {
                return JSON.parse(text);
            } catch {
                return text;
            }
        } catch {
            return null;
        } finally {
            window.clearTimeout(timeoutId);
        }
    }

}
