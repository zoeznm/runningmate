import { OnInit } from '@angular/core';
import { Service } from '@wiz/libs/portal/season/service';
import { apiFetch } from 'src/app/shared/api';

interface PolicySection {
    title: string;
    body: string;
}

interface PolicyDocument {
    title: string;
    version: string;
    effective_date: string;
    sections: PolicySection[];
}

export class Component implements OnInit {
    public loading: boolean = true;
    public error: string = '';
    public policy: PolicyDocument | null = null;

    constructor(public service: Service) { }

    public async ngOnInit(): Promise<void> {
        await this.service.init(null as any);
        await this.loadPolicy();
    }

    public async loadPolicy(): Promise<void> {
        this.loading = true;
        this.error = '';
        await this.service.render();

        try {
            const result = await apiFetch<any>('/api/agreements', { retries: 0 });
            const policy = result.data?.current?.terms || null;
            if (!result.success || !policy) {
                this.error = result.error?.message || '이용약관을 불러오지 못했습니다.';
                this.policy = null;
            } else {
                this.policy = policy;
            }
        } catch {
            this.error = '인터넷 연결을 확인해주세요.';
            this.policy = null;
        } finally {
            this.loading = false;
            await this.service.render();
        }
    }

    public get sections(): PolicySection[] {
        return Array.isArray(this.policy?.sections) ? this.policy!.sections : [];
    }

    public get effectiveText(): string {
        if (!this.policy) return '';
        return `버전 ${this.policy.version} · 시행일 ${this.policy.effective_date}`;
    }

    public goBack(): void {
        if (window.history.length > 1) {
            window.history.back();
            return;
        }
        location.href = '/dashboard';
    }
}
