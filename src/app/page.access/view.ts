import { ChangeDetectorRef, OnDestroy, OnInit } from '@angular/core';
import { Service } from '@wiz/libs/portal/season/service';
import { apiFetch, jsonRequest } from 'src/app/shared/api';
import { authenticatedUser, clearAuthTokens, refreshAuthTokens, saveAuthTokens } from 'src/app/shared/auth';

export class Component implements OnInit, OnDestroy {
    constructor(public service: Service, public ref: ChangeDetectorRef) { }

    public view: string = 'landing';
    public signupStep: number = 1;
    public policies: any = {
        terms: null,
        privacy: null
    };
    public activePolicy: string = '';

    public data: any = {
        username: '',
        password: '',
        autoLogin: false
    };
    public forgotData: any = {
        email: ''
    };
    public resetData: any = {
        token: '',
        newPassword: '',
        confirmPassword: ''
    };
    public signupData: any = {
        username: '',
        email: '',
        password: '',
        confirm_password: '',
        name: '',
        gender: ''
    };
    public genderOptions: Array<{ id: string; label: string }> = [
        { id: 'female', label: '여자' },
        { id: 'male', label: '남자' }
    ];
    public agreements: any = {
        terms: false,
        privacy: false,
        age: false,
        locationInfo: false,
        photoAccess: false,
        marketing: false
    };
    public allAgreementsChecked: boolean = false;
    private readonly agreementKeys: string[] = ['terms', 'privacy', 'age', 'locationInfo', 'photoAccess', 'marketing'];
    private readonly requiredAgreementKeys: string[] = ['terms', 'privacy', 'age'];
    public identityStatus: any = {
        username: { state: 'idle', message: '' },
        email: { state: 'idle', message: '' }
    };
    public identityTimers: any = {
        username: null,
        email: null
    };
    public identitySeq: any = {
        username: 0,
        email: 0
    };
    public isSessionChecking: boolean = true;
    public isLoginLoading: boolean = false;
    public isSignupLoading: boolean = false;
    public isForgotLoading: boolean = false;
    public isResetLoading: boolean = false;
    public showAccessSplash: boolean = true;
    public socialLoginEnabled: boolean = true;
    public socialProviders: Array<{ id: string; label: string; mark: string }> = [
        { id: 'naver', label: '네이버', mark: 'N' },
        { id: 'google', label: '구글', mark: 'G' },
        { id: 'apple', label: 'Apple', mark: '' }
    ];
    public passwordVisibility: Record<string, boolean> = {
        login: false,
        resetNew: false,
        resetConfirm: false,
        signup: false,
        signupConfirm: false
    };
    private readonly accessViewportProperty: string = '--access-visual-height';
    private readonly accessViewportClass: string = 'is-access-page';
    private readonly updateAccessViewportHeight = () => {
        this.syncAccessViewportHeight();
        if (!this.isAccessFormControlFocused()) this.scheduleAccessScrollReset();
    };
    private readonly accessFocusOutHandler = () => this.scheduleAccessScrollReset(60);
    private readonly accessTouchMoveHandler = (event: TouchEvent) => {
        if (this.view === 'signup' || this.activePolicy || this.accessShellCanScroll()) return;
        event.preventDefault();
    };
    private accessScrollResetTimer: number = 0;
    private themeMeta: HTMLMetaElement | null = null;
    private previousThemeColor: string = '';
    private appRootElement: HTMLElement | null = null;
    private previousRootBackground: string = '';
    private previousBodyBackground: string = '';
    private previousAppRootBackground: string = '';
    private readonly mediaAccessNoticeAcceptedKey: string = 'runningmate-media-access-notice-accepted-v1';
    private readonly locationInfoConsentKey: string = 'runningmate-location-info-consent-v1';
    private readonly sessionBootstrapTimeoutMs: number = 10000;
    private readonly accessSplashMinimumMs: number = 2000;
    private accessSplashStartedAt: number = Date.now();

    public async ngOnInit() {
        this.installAccessViewportSync();
        this.normalizeLoginFields();
        const resetToken = this.resetTokenFromUrl();
        const socialError = this.socialErrorFromUrl();
        if (resetToken) {
            this.resetData.token = resetToken;
            this.view = 'reset';
            this.isSessionChecking = false;
            this.showAccessSplash = false;
        }
        if (!resetToken && this.forwardOAuthReturn()) return;

        await this.withTimeout(this.service.init(null as any), this.sessionBootstrapTimeoutMs).catch(() => null);
        if (!resetToken) {
            if (await this.resumeAuthenticatedSession()) return;
            await this.waitForAccessSplashMinimum();
            this.showAccessSplash = false;
            this.isSessionChecking = false;
            await this.safeRender();
        }
        if (socialError && !resetToken) {
            await this.alert(this.socialErrorMessage(socialError), 'error');
            this.clearSocialErrorFromUrl();
        }
        await this.loadPolicies().catch(() => null);
    }

    public ngOnDestroy() {
        this.uninstallAccessViewportSync();
    }

    private installAccessViewportSync() {
        document.documentElement.classList.add(this.accessViewportClass);
        document.body?.classList.add(this.accessViewportClass);
        this.themeMeta = document.querySelector('meta[name="theme-color"]');
        this.previousThemeColor = this.themeMeta?.getAttribute('content') || '';
        this.themeMeta?.setAttribute('content', '#020406');
        this.appRootElement = document.querySelector('app-root');
        this.previousRootBackground = document.documentElement.style.background;
        this.previousBodyBackground = document.body?.style.background || '';
        this.previousAppRootBackground = this.appRootElement?.style.background || '';
        document.documentElement.style.background = '#020406';
        if (document.body) document.body.style.background = '#020406';
        if (this.appRootElement) this.appRootElement.style.background = '#020406';
        this.syncAccessViewportHeight();
        window.addEventListener('resize', this.updateAccessViewportHeight, { passive: true });
        window.addEventListener('orientationchange', this.updateAccessViewportHeight, { passive: true });
        window.visualViewport?.addEventListener('resize', this.updateAccessViewportHeight, { passive: true });
        window.visualViewport?.addEventListener('scroll', this.updateAccessViewportHeight, { passive: true });
        document.addEventListener('focusout', this.accessFocusOutHandler, true);
        document.addEventListener('visibilitychange', this.accessFocusOutHandler, true);
        document.addEventListener('touchmove', this.accessTouchMoveHandler, { passive: false });
        window.setTimeout(this.updateAccessViewportHeight, 250);
        window.setTimeout(this.accessFocusOutHandler, 450);
    }

    private uninstallAccessViewportSync() {
        window.removeEventListener('resize', this.updateAccessViewportHeight);
        window.removeEventListener('orientationchange', this.updateAccessViewportHeight);
        window.visualViewport?.removeEventListener('resize', this.updateAccessViewportHeight);
        window.visualViewport?.removeEventListener('scroll', this.updateAccessViewportHeight);
        document.removeEventListener('focusout', this.accessFocusOutHandler, true);
        document.removeEventListener('visibilitychange', this.accessFocusOutHandler, true);
        document.removeEventListener('touchmove', this.accessTouchMoveHandler);
        window.clearTimeout(this.accessScrollResetTimer);
        document.documentElement.classList.remove(this.accessViewportClass);
        document.body?.classList.remove(this.accessViewportClass);
        document.documentElement.style.removeProperty(this.accessViewportProperty);
        document.body?.style.removeProperty(this.accessViewportProperty);
        if (this.themeMeta && this.previousThemeColor) {
            this.themeMeta.setAttribute('content', this.previousThemeColor);
        }
        document.documentElement.style.background = this.previousRootBackground;
        if (document.body) document.body.style.background = this.previousBodyBackground;
        if (this.appRootElement) this.appRootElement.style.background = this.previousAppRootBackground;
    }

    private syncAccessViewportHeight() {
        const visualViewportHeight = (window.visualViewport?.height || 0) + (window.visualViewport?.offsetTop || 0);
        const height = Math.ceil(Math.max(
            visualViewportHeight,
            window.innerHeight || 0,
            document.documentElement.clientHeight || 0
        ));
        if (!height) return;

        const value = `${height}px`;
        document.documentElement.style.setProperty(this.accessViewportProperty, value);
        document.body?.style.setProperty(this.accessViewportProperty, value);
    }

    private scheduleAccessScrollReset(delay: number = 0) {
        if (this.view === 'signup' || this.activePolicy || this.accessShellCanScroll()) return;
        window.clearTimeout(this.accessScrollResetTimer);
        this.accessScrollResetTimer = window.setTimeout(() => this.resetAccessScrollPosition(), delay);
    }

    private accessShellCanScroll() {
        const shell = document.querySelector('.access-shell') as HTMLElement | null;
        const authPanel = document.querySelector('.auth-panel') as HTMLElement | null;
        return [shell, authPanel].some((element) => {
            if (!element) return false;
            return element.scrollHeight > element.clientHeight + 2;
        });
    }

    private isAccessFormControlFocused() {
        const element = document.activeElement as HTMLElement | null;
        if (!element || !element.closest('.access-shell')) return false;
        return ['INPUT', 'TEXTAREA', 'SELECT'].includes(element.tagName);
    }

    private resetAccessScrollPosition() {
        if (this.view === 'signup' || this.activePolicy || this.accessShellCanScroll()) return;
        const elements = [
            document.documentElement,
            document.body,
            this.appRootElement,
            document.querySelector('.access-page') as HTMLElement | null,
            document.querySelector('.access-shell') as HTMLElement | null
        ];

        try {
            window.scrollTo(0, 0);
        } catch { }

        elements.forEach((element) => {
            if (!element) return;
            element.scrollTop = 0;
            element.scrollLeft = 0;
        });
    }

    public async loadPolicies() {
        const result = await apiFetch<any>('/api/agreements');
        if (!result.success) {
            this.policies.terms = null;
            this.policies.privacy = null;
            return;
        }

        const current = result.data?.current || {};
        this.policies.terms = current.terms || null;
        this.policies.privacy = current.privacy || null;
    }

    public async alert(message: string, status: string = 'error') {
        return await this.service.modal.show({
            title: "",
            message: message,
            cancel: false,
            actionBtn: status,
            action: '확인',
            status: status
        });
    }

    private async withTimeout<T>(work: Promise<T>, timeoutMs: number): Promise<T> {
        let timeoutId = 0;
        const timeout = new Promise<never>((_, reject) => {
            timeoutId = window.setTimeout(() => reject(new Error('auth_bootstrap_timeout')), timeoutMs);
        });

        try {
            return await Promise.race([work, timeout]);
        } finally {
            window.clearTimeout(timeoutId);
        }
    }

    private async safeRender() {
        try {
            await this.service.render();
        } catch {
            this.refreshAgreementControls();
        }
        this.scheduleAccessScrollReset();
    }

    private async waitForAccessSplashMinimum(): Promise<void> {
        if (typeof window === 'undefined') return;
        const elapsed = Date.now() - this.accessSplashStartedAt;
        const remaining = Math.max(0, this.accessSplashMinimumMs - elapsed);
        if (!remaining) return;
        await new Promise<void>((resolve) => window.setTimeout(resolve, remaining));
    }

    private async resumeAuthenticatedSession() {
        const tokenUser = await this.withTimeout(
            authenticatedUser(),
            this.sessionBootstrapTimeoutMs
        ).catch(() => null);
        if (tokenUser) {
            this.goDashboard();
            return true;
        }

        const refreshed = await this.withTimeout(refreshAuthTokens(), this.sessionBootstrapTimeoutMs).catch(() => false);
        if (!refreshed) {
            clearAuthTokens();
            return false;
        }

        const refreshedUser = await this.withTimeout(
            authenticatedUser(),
            this.sessionBootstrapTimeoutMs
        ).catch(() => null);
        if (refreshedUser) {
            this.goDashboard();
            return true;
        }

        clearAuthTokens();
        return false;
    }

    public async confirmAuthSession(payload: any, autoLogin: boolean) {
        if (!saveAuthTokens(payload, autoLogin)) {
            clearAuthTokens();
            return false;
        }
        const user = await this.withTimeout(
            authenticatedUser(),
            this.sessionBootstrapTimeoutMs
        ).catch(() => null);
        if (user) return true;
        clearAuthTokens();
        return false;
    }

    public goDashboard() {
        try {
            this.service.href("/dashboard");
        } catch {
            location.replace("/dashboard");
        }
    }

    public normalizeUsername(value: any) {
        return String(value || '').trim().toLowerCase();
    }

    public normalizeEmail(value: any) {
        return String(value || '').trim().toLowerCase();
    }

    public validateIdentity(type: string, value: any) {
        if (type === 'username') {
            const username = this.normalizeUsername(value);
            if (!username) return '';
            if (!/^[a-z0-9_]{3,30}$/.test(username)) return '3~30자, 영문/숫자/언더스코어만';
            const reserved = [
                'admin', 'administrator', 'root', 'api', 'auth', 'login', 'logout',
                'signup', 'register', 'system', 'support', 'help', 'user', 'users',
                'me', 'profile', 'settings', 'dashboard', 'null', 'undefined', 'test'
            ];
            if (reserved.includes(username)) return '사용할 수 없는 아이디야';
            return '';
        }

        const email = this.normalizeEmail(value);
        if (!email) return '';
        if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return '올바른 이메일 형식이 아니야';
        return '';
    }

    public resetTokenFromUrl() {
        const params = new URLSearchParams(location.search || '');
        return params.get('reset_token') || params.get('token') || '';
    }

    public oauthReturnUrl() {
        const params = new URLSearchParams(location.search || '');
        const state = params.get('state') || '';
        const hasOAuthResult = params.has('code') || params.has('error');
        if (!state || !hasOAuthResult) return '';

        const next = new URLSearchParams();
        ['code', 'state', 'error', 'error_description'].forEach((key) => {
            const value = params.get(key);
            if (value) next.set(key, value);
        });
        return `/api/auth/oauth/callback?${next.toString()}`;
    }

    public forwardOAuthReturn() {
        const target = this.oauthReturnUrl();
        if (!target) return false;
        location.replace(target);
        return true;
    }

    public socialErrorFromUrl() {
        const params = new URLSearchParams(location.search || '');
        return params.get('social_error') || '';
    }

    public socialErrorMessage(code: string) {
        const normalized = String(code || '').trim();
        const messages: any = {
            access_denied: '소셜 로그인 권한이 승인되지 않았습니다.',
            social_config_missing: '소셜 로그인 설정을 확인해주세요.',
            social_provider_invalid: '지원하지 않는 소셜 로그인입니다.',
            social_state_invalid: '소셜 로그인 요청이 만료되었습니다. 다시 시도해주세요.',
            social_token_failed: '소셜 인증 토큰을 확인하지 못했습니다.',
            social_profile_failed: '소셜 계정 정보를 불러오지 못했습니다.',
            social_profile_missing: '소셜 계정 식별 정보를 확인하지 못했습니다.',
            google_email_not_verified: '인증된 구글 이메일 계정만 사용할 수 있습니다.',
            apple_email_not_verified: '인증된 Apple 이메일 계정만 사용할 수 있습니다.',
            social_login_failed: '소셜 회원가입에 실패했습니다. 잠시 후 다시 시도해주세요.'
        };
        return messages[normalized] || '소셜 회원가입에 실패했습니다. 잠시 후 다시 시도해주세요.';
    }

    public clearSocialErrorFromUrl() {
        try {
            const url = new URL(location.href);
            url.searchParams.delete('social_error');
            history.replaceState({}, document.title, `${url.pathname}${url.search}${url.hash}`);
        } catch { }
    }

    public get pageTitle() {
        if (this.view === 'signup') return '이메일로 회원가입';
        if (this.view === 'forgot') return '비밀번호 찾기';
        if (this.view === 'forgotSent') return '메일을 확인해주세요';
        if (this.view === 'reset') return '비밀번호 재설정';
        return '로그인';
    }

    public get pageDescription() {
        if (this.view === 'signup') return 'RunMate 계정을 만들고 바로 시작하세요.';
        if (this.view === 'forgot') return '가입한 이메일로 재설정 링크를 보내드립니다.';
        if (this.view === 'forgotSent') return '메일함에서 비밀번호 재설정 링크를 확인해주세요.';
        if (this.view === 'reset') return '새 비밀번호를 8자 이상으로 입력해주세요.';
        return '아이디 또는 이메일로 RunMate에 로그인하세요.';
    }

    public get accessShellClass() {
        return {
            'access-shell--landing': this.view === 'landing',
            'access-shell--sheet': this.view !== 'landing',
            'access-shell--signup': this.view === 'signup',
            'access-shell--reset': this.view === 'reset'
        };
    }

    public get showAccessBackButton() {
        return this.view !== 'landing' && !this.isSessionChecking;
    }

    public passwordInputType(key: string) {
        return this.passwordVisibility[key] ? 'text' : 'password';
    }

    public togglePasswordVisibility(key: string) {
        this.passwordVisibility = {
            ...this.passwordVisibility,
            [key]: !this.passwordVisibility[key]
        };
        this.ref.detectChanges();
    }

    public passwordToggleLabel(key: string) {
        return this.passwordVisibility[key] ? '비밀번호 숨기기' : '비밀번호 보기';
    }

    public statusClass(status: any) {
        if (status?.state === 'available') return 'status-good';
        if (['duplicate', 'invalid', 'error'].includes(status?.state)) return 'status-bad';
        return 'status-muted';
    }

    public get usernameStatus() {
        return this.identityStatus.username;
    }

    public get emailStatus() {
        return this.identityStatus.email;
    }

    public get usernameChecksReady() {
        return this.usernameStatus.state === 'available';
    }

    public get emailChecksReady() {
        return this.emailStatus.state === 'available';
    }

    public get identityChecksReady() {
        return this.usernameChecksReady && this.emailChecksReady;
    }

    public setIdentityStatus(type: string, state: string, message: string = '') {
        this.identityStatus = {
            ...this.identityStatus,
            [type]: { state, message }
        };
    }

    public scheduleIdentityCheck(type: string) {
        const value = type === 'username'
            ? this.normalizeUsername(this.signupData.username)
            : this.normalizeEmail(this.signupData.email);
        this.identitySeq[type] += 1;
        clearTimeout(this.identityTimers[type]);

        if (!value) {
            this.setIdentityStatus(type, 'idle', '');
            return;
        }

        const invalidMessage = this.validateIdentity(type, value);
        if (invalidMessage) {
            this.setIdentityStatus(type, 'invalid', invalidMessage);
            return;
        }

        const seq = this.identitySeq[type];
        this.setIdentityStatus(type, 'checking', '확인 중');
        this.identityTimers[type] = setTimeout(() => this.checkIdentity(type, seq), 500);
    }

    public async checkIdentity(type: string, seq: number) {
        const value = type === 'username'
            ? this.normalizeUsername(this.signupData.username)
            : this.normalizeEmail(this.signupData.email);
        const invalidMessage = this.validateIdentity(type, value);

        if (this.identitySeq[type] !== seq) return;
        if (!value) {
            this.setIdentityStatus(type, 'idle', '');
            return;
        }
        if (invalidMessage) {
            this.setIdentityStatus(type, 'invalid', invalidMessage);
            return;
        }

        const param = type === 'username' ? 'username' : 'email';
        const result = await apiFetch<any>(`/api/auth/check-${param}?${param}=${encodeURIComponent(value)}`);
        if (this.identitySeq[type] !== seq) return;

        if (!result.success) {
            if (this.identitySeq[type] !== seq) return;
            this.setIdentityStatus(type, 'error', result.error?.message || '확인에 실패했어');
            return;
        }

        const raw = result.raw as any;
        const available = !!raw?.available || !!result.data?.available;
        const availableMessage = type === 'username' ? '사용 가능한 아이디야' : '사용 가능한 이메일이야';
        const duplicateMessage = type === 'username' ? '이미 사용 중인 아이디야' : '이미 사용 중인 이메일이야';
        this.setIdentityStatus(type, available ? 'available' : 'duplicate', result.message || raw?.message || (available ? availableMessage : duplicateMessage));
    }

    public onUsernameInput(value: any) {
        this.signupData.username = this.normalizeUsername(value);
        this.scheduleIdentityCheck('username');
    }

    public onEmailInput(value: any) {
        this.signupData.email = this.normalizeEmail(value);
        this.scheduleIdentityCheck('email');
    }

    public async login() {
        if (this.isLoginLoading) return;
        this.normalizeLoginFields();
        let user = JSON.parse(JSON.stringify(this.data));
        user.username = this.normalizeUsername(user.username);
        if (!user.username) {
            await this.alert("아이디 또는 이메일을 입력해주세요.");
            return;
        }
        if (!user.password) {
            await this.alert("비밀번호를 입력해주세요.");
            return;
        }

        // user.password = this.service.auth.hash(user.password);

        this.isLoginLoading = true;
        await this.service.render();
        this.scheduleAccessScrollReset();

        const result = await jsonRequest<any>('/api/auth/login', 'POST', {
            username: user.username,
            password: user.password,
            auto_login: !!user.autoLogin
        }, { retries: 0 });
        this.isLoginLoading = false;

        if (result.success) {
            const authReady = await this.confirmAuthSession((result.data || result.raw) as any, !!user.autoLogin);
            if (!authReady) {
                await this.alert("로그인 세션을 확인하지 못했습니다. 다시 로그인해주세요.", 'error');
                await this.service.render();
                return;
            }
            this.goDashboard();
            return;
        } else {
            await this.alert(result.error?.message || "로그인에 실패했습니다.", 'error');
        }
        await this.service.render();
    }

    public async showLogin() {
        this.normalizeLoginFields();
        this.view = 'login';
        this.signupStep = 1;
        this.resetData.newPassword = '';
        this.resetData.confirmPassword = '';
        await this.service.render();
        this.scheduleAccessScrollReset();
    }

    private normalizeLoginFields() {
        this.data.username = typeof this.data.username === 'string' ? this.data.username : '';
        this.data.password = typeof this.data.password === 'string' ? this.data.password : '';
        this.data.autoLogin = this.data.autoLogin === true;
    }

    public async showSignup() {
        await this.showEmailSignup();
    }

    public async showLanding() {
        this.view = 'landing';
        this.signupStep = 1;
        this.activePolicy = '';
        await this.service.render();
        this.scheduleAccessScrollReset();
    }

    public async showEmailSignup() {
        this.view = 'signup';
        this.signupStep = 1;
        await this.service.render();
        this.scheduleAccessScrollReset();
    }

    public async goAccessBack() {
        if (this.view === 'forgotSent') {
            await this.showForgotPassword();
            return;
        }
        if (this.view === 'forgot' || this.view === 'reset') {
            await this.showLogin();
            return;
        }
        if (this.view === 'signup' && this.signupStep > 1) {
            this.signupStep = 1;
            await this.service.render();
            this.scheduleAccessScrollReset();
            return;
        }
        await this.showLanding();
    }

    public startSocialSignup(provider: string) {
        if (!this.socialLoginEnabled) return;
        const normalized = String(provider || '').trim().toLowerCase();
        if (!['naver', 'google', 'apple'].includes(normalized)) return;
        const url = `/api/auth/oauth/${normalized}/start`;
        location.assign(url);
    }

    public async showForgotPassword() {
        this.view = 'forgot';
        this.forgotData.email = this.normalizeEmail(this.forgotData.email);
        await this.service.render();
        this.scheduleAccessScrollReset();
    }

    public async forgotPassword() {
        if (this.isForgotLoading) return;
        const email = this.normalizeEmail(this.forgotData.email);
        const emailError = this.validateIdentity('email', email);

        if (!email) {
            await this.alert("이메일을 입력해주세요.");
            return;
        }
        if (emailError) {
            await this.alert(emailError);
            return;
        }

        this.isForgotLoading = true;
        await this.service.render();

        const result = await jsonRequest('/api/auth/forgot-password', 'POST', { email });
        this.isForgotLoading = false;
        if (!result.success) {
            await this.alert(result.error?.message || "메일 발송 요청에 실패했습니다.");
            await this.service.render();
            return;
        }

        this.forgotData.email = email;
        this.view = 'forgotSent';
        await this.service.render();
        this.scheduleAccessScrollReset();
    }

    public async resetPassword() {
        if (this.isResetLoading) return;

        const token = String(this.resetData.token || '').trim();
        const newPassword = String(this.resetData.newPassword || '');
        const confirmPassword = String(this.resetData.confirmPassword || '');

        if (!token) {
            await this.alert("재설정 토큰이 필요합니다.");
            return;
        }
        if (!newPassword) {
            await this.alert("새 비밀번호를 입력해주세요.");
            return;
        }
        if (newPassword.length < 8) {
            await this.alert("비밀번호는 8자 이상이어야 합니다.");
            return;
        }
        if (newPassword !== confirmPassword) {
            await this.alert("비밀번호가 일치하지 않습니다.");
            return;
        }

        this.isResetLoading = true;
        await this.service.render();

        const result = await jsonRequest('/api/auth/reset-password', 'POST', { token, newPassword });
        this.isResetLoading = false;

        if (!result.success) {
            await this.alert(result.error?.message || result.message || "비밀번호 재설정에 실패했습니다.");
            await this.service.render();
            return;
        }

        this.resetData.token = '';
        this.resetData.newPassword = '';
        this.resetData.confirmPassword = '';
        history.replaceState(null, '', '/access');
        await this.alert(result.message || "비밀번호가 재설정되었습니다. 새 비밀번호로 로그인해주세요.", 'success');
        await this.showLogin();
        await this.service.render();
    }

    public get allAgreed() {
        return this.agreementKeys.every((key) => !!this.agreements[key]);
    }

    public get someAgreed() {
        return this.agreementKeys.some((key) => !!this.agreements[key]);
    }

    public get requiredAgreed() {
        return this.requiredAgreementKeys.every((key) => !!this.agreements[key]);
    }

    public get signupReady() {
        return this.requiredAgreed && this.identityChecksReady && this.signupGenderSelected;
    }

    public get signupGenderSelected() {
        return this.signupData.gender === 'female' || this.signupData.gender === 'male';
    }

    public selectSignupGender(gender: string) {
        this.signupData.gender = gender === 'male' ? 'male' : 'female';
    }

    public setAllAgreements(value: any) {
        const checked = this.checkedValue(value);
        this.agreements = this.agreementKeys.reduce((next: any, key) => {
            next[key] = checked;
            return next;
        }, {});
        this.allAgreementsChecked = checked;
        this.refreshAgreementControls();
    }

    public setSignupAgreement(key: string, value: any) {
        if (!this.agreementKeys.includes(key)) return;
        this.agreements = {
            ...this.agreements,
            [key]: this.checkedValue(value)
        };
        this.allAgreementsChecked = this.allAgreed;
        this.refreshAgreementControls();
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

    public async nextSignupStep() {
        this.signupData.username = this.normalizeUsername(this.signupData.username);
        this.signupData.email = this.normalizeEmail(this.signupData.email);
        const usernameError = this.validateIdentity('username', this.signupData.username);
        const emailError = this.validateIdentity('email', this.signupData.email);

        if (!this.signupData.username) {
            await this.alert("아이디를 입력해주세요.");
            return;
        }
        if (usernameError) {
            await this.alert(usernameError);
            return;
        }
        if (this.usernameStatus.state === 'checking') {
            await this.alert("중복확인 중입니다. 잠시만 기다려주세요.");
            return;
        }
        if (!this.usernameChecksReady) {
            await this.alert(this.usernameStatus.message || "아이디 중복확인을 완료해주세요.");
            return;
        }
        if (!this.signupData.email) {
            await this.alert("이메일을 입력해주세요.");
            return;
        }
        if (emailError) {
            await this.alert(emailError);
            return;
        }
        if (this.emailStatus.state === 'checking') {
            await this.alert("이메일 중복확인 중입니다. 잠시만 기다려주세요.");
            return;
        }
        if (!this.emailChecksReady) {
            await this.alert(this.emailStatus.message || "이메일 중복확인을 완료해주세요.");
            return;
        }
        if (!this.signupData.name) {
            await this.alert("이름을 입력해주세요.");
            return;
        }
        if (!this.signupGenderSelected) {
            await this.alert("성별을 선택해주세요.");
            return;
        }
        if (!this.signupData.password) {
            await this.alert("비밀번호를 입력해주세요.");
            return;
        }
        if (this.signupData.password.length < 8) {
            await this.alert("비밀번호는 8자 이상이어야 합니다.");
            return;
        }
        if (this.signupData.password !== this.signupData.confirm_password) {
            await this.alert("비밀번호가 일치하지 않습니다.");
            return;
        }
        this.signupStep = 2;
        await this.service.render();
    }

    public async signup() {
        if (this.isSignupLoading) return;
        this.signupData.username = this.normalizeUsername(this.signupData.username);
        this.signupData.email = this.normalizeEmail(this.signupData.email);
        if (!this.identityChecksReady) {
            await this.alert("아이디와 이메일 중복확인을 완료해주세요.");
            return;
        }
        if (!this.requiredAgreed) {
            await this.alert("필수 동의 항목을 모두 체크해주세요.");
            return;
        }

        const payload = {
            username: this.signupData.username,
            email: this.signupData.email,
            password: this.signupData.password,
            confirm_password: this.signupData.confirm_password,
            name: this.signupData.name,
            gender: this.signupData.gender,
            terms_agreed: this.agreements.terms,
            privacy_agreed: this.agreements.privacy,
            age_confirmed: this.agreements.age,
            location_info_agreed: this.agreements.locationInfo,
            photo_access_agreed: this.agreements.photoAccess,
            marketing_optin: this.agreements.marketing,
            terms_version: this.policies.terms?.version || '',
            privacy_version: this.policies.privacy?.version || '',
            agreed_at: new Date().toISOString()
        };

        this.isSignupLoading = true;
        await this.service.render();

        const result = await jsonRequest<any>('/api/auth/register', 'POST', payload, { retries: 0 });
        this.isSignupLoading = false;
        if (result.success) {
            const authReady = await this.confirmAuthSession((result.data || result.raw) as any, true);
            if (!authReady) {
                await this.alert("가입은 완료됐지만 로그인 세션을 확인하지 못했습니다. 로그인해주세요.", 'error');
                await this.service.render();
                return;
            }
            this.persistOptionalConsentFlags();
            this.goDashboard();
            return;
        }
        await this.alert(result.error?.message || "회원가입에 실패했습니다.");
        await this.service.render();
    }

    private persistOptionalConsentFlags() {
        if (typeof window === 'undefined' || !window.localStorage) return;
        try {
            if (this.agreements.photoAccess) {
                window.localStorage.setItem(this.mediaAccessNoticeAcceptedKey, '1');
            }
            if (this.agreements.locationInfo) {
                window.localStorage.setItem(this.locationInfoConsentKey, '1');
            }
        } catch {
            return;
        }
    }

    public openPolicy(type: string) {
        this.activePolicy = type;
        this.refreshAgreementControls();
    }

    public closePolicy() {
        this.activePolicy = '';
        this.refreshAgreementControls();
    }

    public activePolicyData() {
        if (!this.activePolicy) return null;
        return this.policies[this.activePolicy] || null;
    }
}
