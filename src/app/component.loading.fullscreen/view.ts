import { Input } from '@angular/core';

export class Component {
    @Input() public message: string = '초기 데이터를 불러오는 중';
    @Input() public detail: string = '';
}
