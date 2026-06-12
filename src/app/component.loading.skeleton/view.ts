import { Input } from '@angular/core';

export class Component {
    @Input() public type: 'home' | 'chart' | 'list' | string = 'list';
    @Input() public rows: number | string = 3;
    public statItems: number[] = [0, 1, 2, 3];
    public chartHeights: number[] = [42, 70, 54, 88, 62, 76, 48];

    public rowItems(): number[] {
        const count = Math.max(1, Number(this.rows) || 3);
        return Array.from({ length: count }, (_, index) => index);
    }
}
