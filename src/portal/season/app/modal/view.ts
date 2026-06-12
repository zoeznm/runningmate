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
            return 'border-white/10 bg-white/5 text-yellow-600';
        if (this.model.opts.status == 'success')
            return 'border-white/10 bg-[#74f56a]/10 text-[#a7ff8a]';
        return 'border-white/10 bg-white/5 text-red-300';
    }

    public btnColorClass() {
        const base = 'inline-flex h-10 w-full items-center justify-center rounded-lg px-4 text-[13px] font-black shadow-sm transition-shadow hover:shadow-md disabled:opacity-60 sm:w-auto';
        if (this.model.opts.status == 'warning')
            return `${base} bg-yellow-600 text-white`;
        if (this.model.opts.status == 'success')
            return `${base} bg-[#74f56a] text-[#07100a] shadow-[#74f56a]/20`;
        return `${base} bg-red-600 text-white hover:bg-red-500`;
    }

    public cancelButtonClass() {
        return 'inline-flex h-10 w-full items-center justify-center rounded-lg border border-white/10 bg-white/5 px-4 text-[13px] font-black text-slate-200 shadow-sm transition-shadow hover:shadow-md sm:w-auto';
    }
}
