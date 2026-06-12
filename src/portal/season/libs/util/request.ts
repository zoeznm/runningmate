import $ from "jquery";

interface RequestOptions {
    timeout?: number;
}

export default class Request {
    constructor() { }

    public async post(url: string, data: any = {}, options: RequestOptions = {}) {
        const timeout = Math.max(1000, Number(options.timeout || 10000));
        let request = () => {
            return new Promise((resolve) => {
                $.ajax({
                    url: url,
                    type: "POST",
                    data: data,
                    timeout: timeout
                }).always(function (res) {
                    resolve(res);
                });
            });
        }

        return await request();
    }

}
