import { OnInit } from '@angular/core';
import { Service } from '@wiz/libs/portal/season/service';
import { apiErrorMessage, apiFetch, jsonRequest, safeUserMessage } from 'src/app/shared/api';
import { clearAuthTokens, ensureAuthenticated } from 'src/app/shared/auth';
import { ToastService } from 'src/app/shared/toast.service';

export class Component implements OnInit {
    public user: any = null;
    public loading: boolean = false;
    public loadError: string = '';
    public saving: boolean = false;
    public agreement: any = null;
    public agreementSaving: boolean = false;
    public activePolicy: string = '';
    public deleteStep: number = 0;
    public deletingAccount: boolean = false;
    public accountDeleted: boolean = false;
    public accountDeleteForm: any = {
        confirm_text: ''
    };

    public passwordForm: any = {
        current_password: '',
        new_password: '',
        confirm_password: '',
        invalidate_other_sessions: true
    };
    public changingPassword: boolean = false;

    constructor(public service: Service, private readonly toast: ToastService) { }

    public readonly retryLoad = (): void => {
        void this.load();
    };

    public async ngOnInit() {
        await this.service.init(null as any);
        if (!(await ensureAuthenticated())) {
            location.replace('/access');
            return;
        }
        await this.load();
    }

    public async load() {
        this.loading = true;
        this.loadError = '';
        await this.service.render();

        try {
            const { code, data }: any = await wiz.call("get") as any;
            if (code === 200) {
                this.user = data;
            } else {
                this.loadError = safeUserMessage(data?.message || data, '프로필을 불러오지 못했습니다.');
            }
            await this.loadAgreement();
        } catch {
            this.loadError = '인터넷 연결을 확인해줘';
        } finally {
            this.loading = false;
            await this.service.render();
        }
    }

    public async loadAgreement() {
        const result = await apiFetch<any>('/api/agreements');
        if (!result.success) {
            this.agreement = null;
            return;
        }

        this.agreement = result.data;
        if (!this.agreement.latest) {
            this.agreement.latest = { marketing_optin: false };
        }
    }

    public async updateProfile() {
        if (!this.user.name) {
            await this.service.modal.error("이름을 입력해주세요.");
            return;
        }

        this.saving = true;
        await this.service.render();

        const { code, data }: any = await wiz.call("update_profile", {
            name: this.user.name,
            mobile: this.user.mobile || '',
            is_public: !!this.user.is_public
        }) as any;

        await this.service.sleep(500);
        this.saving = false;

        if (code === 200) {
            this.toast.success("프로필이 업데이트되었습니다.");
        } else {
            this.toast.error(safeUserMessage(data, "업데이트에 실패했습니다."));
        }
        await this.service.render();
    }

    public async changePassword() {
        const { current_password, new_password, confirm_password } = this.passwordForm;

        if (!current_password) {
            await this.service.modal.error("현재 비밀번호를 입력해주세요.");
            return;
        }
        if (!new_password) {
            await this.service.modal.error("새 비밀번호를 입력해주세요.");
            return;
        }
        if (new_password.length < 8) {
            await this.service.modal.error("새 비밀번호는 8자 이상이어야 합니다.");
            return;
        }
        if (current_password === new_password) {
            await this.service.modal.error("새 비밀번호는 현재 비밀번호와 달라야 합니다.");
            return;
        }
        if (new_password !== confirm_password) {
            await this.service.modal.error("새 비밀번호가 일치하지 않습니다.");
            return;
        }

        this.changingPassword = true;
        await this.service.render();

        const result = await jsonRequest<any>('/api/auth/password', 'PATCH', {
            currentPassword: current_password,
            newPassword: new_password,
            invalidateOtherSessions: !!this.passwordForm.invalidate_other_sessions
        }, { retries: 0 });

        await this.service.sleep(500);
        this.changingPassword = false;

        if (result.success) {
            this.toast.success("비밀번호가 변경됐어");
            this.passwordForm = { current_password: '', new_password: '', confirm_password: '', invalidate_other_sessions: true };
        } else {
            this.toast.error(apiErrorMessage(result.error, "비밀번호 변경에 실패했습니다."));
        }
        await this.service.render();
    }

    public get passwordMinLengthOk() {
        return String(this.passwordForm.new_password || '').length >= 8;
    }

    public get passwordCombinationOk() {
        const value = String(this.passwordForm.new_password || '');
        return /[A-Za-z]/.test(value) && /\d/.test(value);
    }

    public get passwordMatchTouched() {
        return Boolean(this.passwordForm.confirm_password);
    }

    public get passwordMatches() {
        return this.passwordMatchTouched && this.passwordForm.new_password === this.passwordForm.confirm_password;
    }

    public get passwordMatchText() {
        if (!this.passwordMatchTouched) return '새 비밀번호를 한 번 더 입력해주세요.';
        return this.passwordMatches ? '새 비밀번호가 일치합니다.' : '새 비밀번호가 일치하지 않습니다.';
    }

    public get passwordCanSubmit() {
        return Boolean(this.passwordForm.current_password)
            && this.passwordMinLengthOk
            && this.passwordMatches
            && this.passwordForm.current_password !== this.passwordForm.new_password;
    }

    public policy(type: string) {
        return this.agreement?.current?.[type] || null;
    }

    public openPolicy(type: string) {
        this.activePolicy = type;
    }

    public closePolicy() {
        this.activePolicy = '';
    }

    public async updateMarketingAgreement() {
        if (!this.agreement?.latest || this.agreementSaving) return;

        this.agreementSaving = true;
        await this.service.render();

        const result = await jsonRequest<any>('/api/agreements', 'PATCH', {
            marketing_optin: !!this.agreement.latest.marketing_optin
        });
        if (result.success) {
            this.agreement = result.data;
            if (!this.agreement.latest) {
                this.agreement.latest = { marketing_optin: false };
            }
            this.toast.success("마케팅 수신 동의가 변경되었습니다.");
        } else {
            this.toast.error(apiErrorMessage(result.error, "마케팅 동의 변경에 실패했습니다."));
        }

        this.agreementSaving = false;
        await this.service.render();
    }

    public openAccountDelete() {
        this.deleteStep = 1;
        this.accountDeleteForm = { confirm_text: '' };
    }

    public closeAccountDelete() {
        if (this.deletingAccount) return;
        this.deleteStep = 0;
        this.accountDeleteForm = { confirm_text: '' };
    }

    public continueAccountDelete() {
        this.deleteStep = 2;
    }

    public get accountDeleteReady() {
        return (this.accountDeleteForm.confirm_text || '').trim() === '삭제';
    }

    public async deleteAccount() {
        if (!this.accountDeleteReady || this.deletingAccount) {
            await this.service.modal.error("'삭제'를 정확히 입력해주세요.");
            return;
        }

        const confirmed = await this.service.modal.show({
            title: "계정 삭제",
            message: "계정과 모든 러닝 데이터를 삭제합니다. 이 작업은 되돌릴 수 없습니다.",
            action: "최종 삭제",
            actionBtn: "error",
            status: "error"
        });
        if (!confirmed) return;

        this.deletingAccount = true;
        await this.service.render();

        try {
            const result = await jsonRequest<any>('/api/auth/account', 'DELETE', {
                confirm_text: this.accountDeleteForm.confirm_text
            });
            if (!result.success) {
                await this.service.modal.error(apiErrorMessage(result.error, "계정 삭제에 실패했습니다."));
                return;
            }

            this.accountDeleted = true;
            clearAuthTokens();
            this.deleteStep = 0;
            await this.service.render();
            await this.service.sleep(1200);
            location.href = "/access?account_deleted=1";
        } catch (error) {
            await this.service.modal.error("계정 삭제 중 오류가 발생했습니다.");
        } finally {
            this.deletingAccount = false;
            await this.service.render();
        }
    }
}
