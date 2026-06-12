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

type ThemeMode = 'dark' | 'light' | 'system';

export class Component implements OnInit {
    public loading: boolean = true;
    public error: string = '';
    public isDark: boolean = true;
    public policy: PolicyDocument | null = null;
    private readonly appSettingsStorageKey: string = 'runningmate-settings-v1';

    constructor(public service: Service) { }

    public async ngOnInit(): Promise<void> {
        this.applyThemeMode();
        await this.service.init(null as any);
        await this.loadPolicy();
    }

    public async loadPolicy(): Promise<void> {
        this.loading = true;
        this.error = '';
        await this.service.render();

        try {
            const result = await apiFetch<any>('/api/agreements', { retries: 0 });
            const policy = result.data?.current?.privacy || null;
            if (!result.success || !policy) {
                this.error = result.error?.message || '개인정보처리방침을 불러오지 못했습니다.';
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

    private applyThemeMode(): void {
        let mode: ThemeMode = 'dark';

        try {
            const raw = window.localStorage?.getItem(this.appSettingsStorageKey) || '';
            const parsed = raw ? JSON.parse(raw) : {};
            const themeMode = parsed?.themeMode;
            if (themeMode === 'dark' || themeMode === 'light' || themeMode === 'system') {
                mode = themeMode;
            }
        } catch {
            mode = 'dark';
        }

        this.isDark = mode === 'system'
            ? Boolean(window.matchMedia?.('(prefers-color-scheme: dark)').matches)
            : mode !== 'light';
    }
}
