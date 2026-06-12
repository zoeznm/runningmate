import { OnInit } from '@angular/core';
import { Service } from '@wiz/libs/portal/season/service';
import { ensureAuthenticated } from 'src/app/shared/auth';

export class Component implements OnInit {
    constructor(public service: Service) { }

    public async ngOnInit() {
        await this.service.init();
        if (!(await ensureAuthenticated())) {
            location.replace('/access');
        }
    }
}
