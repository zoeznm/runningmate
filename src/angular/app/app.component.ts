import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';
import { TranslateService } from '@ngx-translate/core';
import { apiErrorMessage, apiFetch, jsonRequest } from 'src/app/shared/api';
import { ensureAuthenticated, installAuthFetchInterceptor, handleAuthFailure, hasAuthTokens } from 'src/app/shared/auth';
import { ToastService } from 'src/app/shared/toast.service';

@Component({
    selector: 'app-root',
    templateUrl: './app.component.html',
    styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {
    public agreementStatus: any = null;
    public agreementModalVisible: boolean = false;
    public agreementSaving: boolean = false;
    public activeAgreementPolicy: string = '';
    public reconsentAllChecked: boolean = false;
    public reconsent: any = {
        terms: false,
        privacy: false,
        age: false,
        marketing: false
    };
    private readonly reconsentKeys: string[] = ['terms', 'privacy', 'age', 'marketing'];
    private readonly requiredReconsentKeys: string[] = ['terms', 'privacy', 'age'];
    private readonly agreementModalBodyClass: string = 'runningmate-agreement-modal-visible';
    private readonly agreementModalEventName: string = 'runningmate:agreement-modal';
    private readonly appBootstrapTimeoutMs: number = 8000;
    private readonly appBootstrapFallbackMs: number = 6500;
    private readonly appShellLoaderSelector: string = '.app-shell-loader';
    private appBootstrapFallbackTimer: number = 0;

    constructor(
        public service: Service,
        public router: Router,
        public ref: ChangeDetectorRef,
        public translate: TranslateService,
        public toast: ToastService
    ) {
        window['MonacoEnvironment'] = {
            getWorkerUrl: function (moduleId: string, label: string) {
                return `/lib/vs/base/worker/workerMain.js`;
            }
        };
    }

    public async ngOnInit() {
        installAuthFetchInterceptor();
        this.installAppBootstrapFallback();
        try {
            await this.withAppBootstrapTimeout(this.service.init(this), '앱 초기화');
        } catch {
            this.markAppShellReady();
        } finally {
            this.clearAppBootstrapFallback();
            this.markAppShellReady();
        }

        const isPublicPage = this.isPublicPage();
        const authenticated = isPublicPage
            ? true
            : await this.withAppBootstrapTimeout(ensureAuthenticated(), '로그인 상태 확인').catch(() => false);
        if (!isPublicPage && !authenticated) {
            if (hasAuthTokens()) {
                return;
            }
            handleAuthFailure();
            return;
        }
        if (!isPublicPage) {
            void this.withAppBootstrapTimeout(this.checkAgreementRequirement(), '약관 확인').catch(() => {
                this.setAgreementModalVisible(false);
            });
        }
    }

    private installAppBootstrapFallback(): void {
        if (typeof window === 'undefined') return;
        this.clearAppBootstrapFallback();
        this.appBootstrapFallbackTimer = window.setTimeout(() => {
            this.markAppShellReady();
        }, this.appBootstrapFallbackMs);
    }

    private clearAppBootstrapFallback(): void {
        if (!this.appBootstrapFallbackTimer || typeof window === 'undefined') return;
        window.clearTimeout(this.appBootstrapFallbackTimer);
        this.appBootstrapFallbackTimer = 0;
    }

    private markAppShellReady(): void {
        if (!this.service.inited) {
            this.service.inited = true;
        }
        this.removeStaticShellLoader();
        this.dispatchAppReadyEvent();
        this.safeDetectChanges();
    }

    private dispatchAppReadyEvent(): void {
        if (typeof window === 'undefined') return;
        try {
            (window as any).__RUNNINGMATE_APP_READY__ = true;
            const supportsCustomEvent = typeof CustomEvent === 'function';
            const event = supportsCustomEvent
                ? new CustomEvent('runningmate:app-ready')
                : document.createEvent('Event');
            if (!supportsCustomEvent && 'initEvent' in event) {
                event.initEvent('runningmate:app-ready', false, false);
            }
            window.dispatchEvent(event);
        } catch { }
    }

    private removeStaticShellLoader(): void {
        if (typeof document === 'undefined') return;
        try {
            document.querySelectorAll(this.appShellLoaderSelector).forEach((element) => {
                element.parentElement?.removeChild(element);
            });
        } catch { }
    }

    private async withAppBootstrapTimeout<T>(task: Promise<T>, label: string): Promise<T> {
        if (typeof window === 'undefined') return task;

        let timeoutId: number | null = null;
        const timeout = new Promise<T>((_, reject) => {
            timeoutId = window.setTimeout(() => {
                reject(new Error(`${label} timed out`));
            }, this.appBootstrapTimeoutMs);
        });

        try {
            return await Promise.race([task, timeout]);
        } finally {
            if (timeoutId !== null) {
                window.clearTimeout(timeoutId);
            }
        }
    }

    private safeDetectChanges(): void {
        try {
            this.ref.detectChanges();
        } catch {
            window.setTimeout(() => {
                try {
                    this.ref.detectChanges();
                } catch { }
            }, 0);
        }
    }

    private isPublicPage(): boolean {
        const path = location.pathname.replace(/\/+$/, '') || '/';
        return ['/access', '/privacy', '/terms', '/account/delete'].includes(path) || path.startsWith('/auth/');
    }

    public get reconsentReady() {
        return this.requiredReconsentKeys.every((key) => !!this.reconsent[key]);
    }

    public setAllReconsent(value: any) {
        const checked = this.checkedValue(value);
        this.reconsent = this.reconsentKeys.reduce((next: any, key) => {
            next[key] = checked;
            return next;
        }, {});
        this.reconsentAllChecked = checked;
        this.refreshAgreementControls();
    }

    public setReconsent(key: string, value: any) {
        if (!this.reconsentKeys.includes(key)) return;
        this.reconsent = {
            ...this.reconsent,
            [key]: this.checkedValue(value)
        };
        this.reconsentAllChecked = this.allReconsentChecked;
        this.refreshAgreementControls();
    }

    public get allReconsentChecked() {
        return this.reconsentKeys.every((key) => !!this.reconsent[key]);
    }

    public get someReconsentChecked() {
        return this.reconsentKeys.some((key) => !!this.reconsent[key]);
    }

    private checkedValue(value: any) {
        if (typeof value === 'boolean') return value;
        return !!value?.target?.checked;
    }

    private refreshAgreementControls() {
        try {
            this.ref.detectChanges();
        } catch {
            window.setTimeout(() => {
                try {
                    this.ref.detectChanges();
                } catch { }
            }, 0);
        }
    }

    public async checkAgreementRequirement() {
        const result = await apiFetch<any>('/api/agreements');
        if (!result.success) {
            this.setAgreementModalVisible(false);
            return;
        }

        this.agreementStatus = result.data;
        this.reconsent = {
            terms: false,
            privacy: false,
            age: false,
            marketing: !!result.data?.latest?.marketing_optin
        };
        this.reconsentAllChecked = this.allReconsentChecked;
        this.setAgreementModalVisible(!!result.data?.needs_reagreement);
        await this.service.render();
    }

    public agreementPolicy(type: string) {
        return this.agreementStatus?.current?.[type] || null;
    }

    public openAgreementPolicy(type: string) {
        this.activeAgreementPolicy = type;
        this.refreshAgreementControls();
    }

    public closeAgreementPolicy() {
        this.activeAgreementPolicy = '';
        this.refreshAgreementControls();
    }

    public async submitReconsent() {
        if (!this.reconsentReady || this.agreementSaving) return;

        this.agreementSaving = true;
        await this.service.render();

        try {
            const result = await jsonRequest<any>('/api/agreements', 'POST', {
                terms_agreed: this.reconsent.terms,
                privacy_agreed: this.reconsent.privacy,
                age_confirmed: this.reconsent.age,
                marketing_optin: this.reconsent.marketing,
                terms_version: this.agreementPolicy('terms')?.version || '',
                privacy_version: this.agreementPolicy('privacy')?.version || '',
                agreed_at: new Date().toISOString()
            });
            if (result.success) {
                this.agreementStatus = result.data;
                this.setAgreementModalVisible(false);
                this.activeAgreementPolicy = '';
                this.toast.clear();
            } else {
                this.toast.error(apiErrorMessage(result.error, '약관 동의를 저장하지 못했습니다.'));
            }
        } finally {
            this.agreementSaving = false;
            await this.service.render();
        }
    }

    private setAgreementModalVisible(visible: boolean): void {
        this.agreementModalVisible = visible;
        this.publishAgreementModalState();
    }

    private publishAgreementModalState(): void {
        if (typeof document !== 'undefined') {
            document.body?.classList.toggle(this.agreementModalBodyClass, this.agreementModalVisible);
        }
        if (typeof window !== 'undefined' && typeof CustomEvent !== 'undefined') {
            window.dispatchEvent(new CustomEvent(this.agreementModalEventName, {
                detail: { visible: this.agreementModalVisible }
            }));
        }
    }
}
