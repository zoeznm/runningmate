import { Input } from '@angular/core';

export class Component {
    @Input() public icon: string = '';
    @Input() public title: string = '';
    @Input() public description: string = '';
    @Input() public actionLabel: string = '';
    @Input() public onAction?: () => void;

    public handleAction(): void {
        this.onAction?.();
    }
}
