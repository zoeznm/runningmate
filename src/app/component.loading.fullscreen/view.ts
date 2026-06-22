import { ChangeDetectorRef, Input, OnDestroy, OnInit } from '@angular/core';
import { isNativeLocalOrigin } from 'src/app/shared/api-base';

const DEFAULT_LOADING_TIPS: string[] = [
    '오늘의 러닝 기록을 한곳에 모으고 있어요.',
    '목표 달성률을 계산하고 다음 러닝을 준비하고 있어요.',
    '친구 피드와 랭킹을 최신 상태로 맞추고 있어요.',
    'AI 페이서가 최근 흐름을 읽고 있어요.'
];

export class Component implements OnInit, OnDestroy {
    constructor(private readonly cdr: ChangeDetectorRef) { }

    @Input() public message: string = 'RunMate';
    @Input() public detail: string = '';
    @Input() public tips: string[] = DEFAULT_LOADING_TIPS;

    public activeTipIndex: number = 0;
    private tipTimer: number = 0;

    public ngOnInit(): void {
        this.setNativeSafeAreaBackground('#020406').catch(() => null);
        this.startTipRotation();
    }

    public ngOnDestroy(): void {
        this.stopTipRotation();
    }

    public get currentTip(): string {
        const items = this.normalizedTips();
        return items[this.activeTipIndex % items.length] || DEFAULT_LOADING_TIPS[0];
    }

    private normalizedTips(): string[] {
        const items = Array.isArray(this.tips)
            ? this.tips.filter((item) => typeof item === 'string' && item.trim().length > 0)
            : [];
        return items.length ? items : DEFAULT_LOADING_TIPS;
    }

    private startTipRotation(): void {
        if (typeof window === 'undefined') return;
        this.stopTipRotation();
        this.tipTimer = window.setInterval(() => {
            const items = this.normalizedTips();
            this.activeTipIndex = (this.activeTipIndex + 1) % items.length;
            this.cdr.detectChanges();
        }, 2600);
    }

    private stopTipRotation(): void {
        if (!this.tipTimer || typeof window === 'undefined') return;
        window.clearInterval(this.tipTimer);
        this.tipTimer = 0;
    }

    private nativeAuthPlugin(): any {
        return (window as any).Capacitor?.Plugins?.RunningMateAuth || null;
    }

    private async setNativeSafeAreaBackground(color: string): Promise<void> {
        if (!isNativeLocalOrigin()) return;
        const plugin = this.nativeAuthPlugin();
        if (!plugin?.setSafeAreaBackground) return;
        await plugin.setSafeAreaBackground({ color });
    }
}
