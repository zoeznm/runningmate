import { OnInit, Input } from '@angular/core';
import { Service } from '@wiz/libs/portal/season/service';

export class Component implements OnInit {
    @Input() model: any = null;

    constructor(public service: Service) {
        if (!this.model) this.model = service.modal;
    }

    public async ngOnInit() {
    }

    public statusIconWrapClass() {
        if (this.model.opts.status == 'warning')
            return 'wiz-app-modal-icon-warning';
        if (this.model.opts.status == 'success')
            return 'wiz-app-modal-icon-success';
        return 'wiz-app-modal-icon-error';
    }

    public btnColorClass() {
        const base = 'wiz-app-modal-button wiz-app-modal-button-primary';
        if (this.model.opts.status == 'warning')
            return `${base} wiz-app-modal-button-warning`;
        if (this.model.opts.status == 'success')
            return `${base} wiz-app-modal-button-success`;
        return `${base} wiz-app-modal-button-error`;
    }

    public cancelButtonClass() {
        return 'wiz-app-modal-button wiz-app-modal-button-cancel';
    }
}
