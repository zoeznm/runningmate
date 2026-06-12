import { OnInit } from '@angular/core';
import { Service } from '@wiz/libs/portal/season/service';
import { jsonRequest } from 'src/app/shared/api';
import { authenticatedUser, clearAuthTokens, ensureAuthenticated } from 'src/app/shared/auth';

type StatusKind = 'info' | 'success' | 'error';

export class Component implements OnInit {
    public loading: boolean = true;
    public user: any = null;
    public confirmText: string = '';
    public password: string = '';
    public acknowledged: boolean = false;
    public deleting: boolean = false;
    public accountDeleted: boolean = false;
    public statusMessage: string = '';
    public statusKind: StatusKind = 'info';

    constructor(public service: Service) { }

    public async ngOnInit(): Promise<void> {
        await this.service.init(null as any);
        await this.loadAuthState();
    }

    public async loadAuthState(): Promise<void> {
        this.loading = true;
        this.setStatus('', 'info');
        await this.service.render();

        try {
            if (await ensureAuthenticated()) {
                this.user = await authenticatedUser();
            } else {
                this.user = null;
            }
        } catch {
            this.user = null;
        } finally {
            this.loading = false;
            await this.service.render();
        }
    }

    public get isAuthenticated(): boolean {
        return Boolean(this.user);
    }

    public get userLabel(): string {
        return this.user?.email || this.user?.username || this.user?.name || '로그인된 계정';
    }

    public get canDelete(): boolean {
        return this.isAuthenticated && this.acknowledged && this.confirmText.trim() === '삭제' && !this.deleting;
    }

    public goLogin(): void {
        location.href = '/access';
    }

    public goDashboard(): void {
        location.href = '/dashboard';
    }

    public goBack(): void {
        if (window.history.length > 1) {
            window.history.back();
            return;
        }
        this.goDashboard();
    }

    public async deleteAccount(): Promise<void> {
        if (!this.canDelete) {
            this.setStatus("삭제 안내를 확인하고 '삭제'를 정확히 입력해주세요.", 'error');
            await this.service.render();
            return;
        }

        this.deleting = true;
        this.setStatus('계정과 연결 데이터를 삭제하는 중입니다.', 'info');
        await this.service.render();

        try {
            const result = await jsonRequest<any>('/api/auth/account', 'DELETE', {
                confirm_text: this.confirmText,
                password: this.password || ''
            }, { retries: 0, timeoutMs: 30000 });

            if (!result.success) {
                this.setStatus(result.error?.message || result.message || '계정 삭제에 실패했습니다.', 'error');
                return;
            }

            clearAuthTokens();
            this.accountDeleted = true;
            this.setStatus('계정 삭제가 완료되었습니다. 로그인 화면으로 이동합니다.', 'success');
            await this.service.render();
            await this.service.sleep(1200);
            location.href = '/access?account_deleted=1';
        } catch {
            this.setStatus('계정 삭제 중 오류가 발생했습니다.', 'error');
        } finally {
            this.deleting = false;
            await this.service.render();
        }
    }

    private setStatus(message: string, kind: StatusKind): void {
        this.statusMessage = message;
        this.statusKind = kind;
    }
}
