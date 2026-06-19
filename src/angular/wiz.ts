export default class Wiz {
    public namespace: any;
    public baseuri: any;

    constructor(baseuri: any) {
        this.baseuri = baseuri;
    }

    public app(namespace: any) {
        let instance = new Wiz(this.baseuri);
        instance.namespace = namespace;
        return instance;
    }

    public dev() {
        let findcookie = (name) => {
            let ca: Array<string> = document.cookie.split(';');
            let caLen: number = ca.length;
            let cookieName = `${name}=`;
            let c: string;

            for (let i: number = 0; i < caLen; i += 1) {
                c = ca[i].replace(/^\s+/g, '');
                if (c.indexOf(cookieName) == 0) {
                    return c.substring(cookieName.length, c.length);
                }
            }
            return '';
        }

        let isdev = findcookie("season-wiz-devmode");
        if (isdev == 'true') return true;
        return false;
    }

    public project() {
        let findcookie = (name) => {
            let ca: Array<string> = document.cookie.split(';');
            let caLen: number = ca.length;
            let cookieName = `${name}=`;
            let c: string;

            for (let i: number = 0; i < caLen; i += 1) {
                c = ca[i].replace(/^\s+/g, '');
                if (c.indexOf(cookieName) == 0) {
                    return c.substring(cookieName.length, c.length);
                }
            }
            return '';
        }

        let project = findcookie("season-wiz-project");
        if (project) return project;
        return "main";
    }

    public socket() {
        let socketns = this.baseuri + "/app/" + this.project();
        if (this.namespace)
            socketns = socketns + "/" + this.namespace;
        return import("socket.io-client").then(({ io }) => io(socketns));
    };

    public url(function_name: string) {
        if (function_name[0] == "/") function_name = function_name.substring(1);
        return this.baseuri + "/api/" + this.namespace + "/" + function_name;
    }

    public call(function_name: string, data = {}, options = {}) {
        const requestOptions: any = {
            method: "POST",
            credentials: "same-origin",
            ...options
        };
        const body = data instanceof FormData
            ? data
            : new URLSearchParams(Object.entries(data || {}).reduce((params: Record<string, string>, [key, value]) => {
                params[key] = typeof value === "string" ? value : JSON.stringify(value);
                return params;
            }, {}));

        if (!(body instanceof FormData)) {
            requestOptions.headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                ...(requestOptions.headers || {})
            };
        }
        requestOptions.body = body as BodyInit;

        return fetch(this.url(function_name), requestOptions).then(async (response) => {
            const text = await response.text();
            try {
                return JSON.parse(text);
            } catch {
                return text;
            }
        }).catch((error) => {
            return { code: 0, data: null, error: String(error?.message || error || "request_failed") };
        });
    }
}
