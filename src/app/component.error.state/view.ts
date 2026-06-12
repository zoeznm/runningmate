import { Input } from '@angular/core';

export class Component {
    @Input() public message: string = '잠깐 문제가 생겼어. 다시 시도해줘';
    @Input() public retryLabel: string = '다시 시도';
    @Input() public onRetry?: () => void;

    public retry(): void {
        this.onRetry?.();
    }
}
