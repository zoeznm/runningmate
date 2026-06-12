import { Component, OnInit, ChangeDetectorRef, enableProdMode } from '@angular/core';
import { Router } from '@angular/router';
import { Service } from '@wiz/libs/portal/season/service';
import { TranslateService } from '@ngx-translate/core';
import { apiFetch, jsonRequest } from 'src/app/shared/api';
import { ensureAuthenticated, installAuthFetchInterceptor } from 'src/app/shared/auth';
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
        enableProdMode();
        installAuthFetchInterceptor();
        await this.service.init(this);
        if (!this.isPublicAuthPage() && !(await ensureAuthenticated())) {
            location.href = '/access';
            return;
        }
        await this.checkAgreementRequirement();
    }

    private isPublicAuthPage(): boolean {
        return location.pathname === '/access' || location.pathname.startsWith('/auth/');
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
            this.agreementModalVisible = false;
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
        this.agreementModalVisible = !!result.data?.needs_reagreement;
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
                this.agreementModalVisible = false;
                this.activeAgreementPolicy = '';
                this.toast.clear();
            } else {
                this.toast.error(result.error?.message || '약관 동의를 저장하지 못했습니다.');
            }
        } finally {
            this.agreementSaving = false;
            await this.service.render();
        }
    }
}
