import { ChangeDetectorRef } from '@angular/core';
import { ToastService } from 'src/app/shared/toast.service';

export class Component {
    constructor(public toast: ToastService, public ref: ChangeDetectorRef) { }

    public dismiss(id: number) {
        this.toast.dismiss(id);
        try {
            this.ref.detectChanges();
        } catch { }
    }
}
