import { Input } from '@angular/core';

export class Component {
    @Input() public label: string = '로딩 중';
    @Input() public size: 'sm' | 'md' | 'lg' | string = 'md';
    @Input() public className: string = '';
}
