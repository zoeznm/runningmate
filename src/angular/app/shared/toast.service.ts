import { Injectable } from '@angular/core';

export type ToastType = 'success' | 'error' | 'info';

export interface ToastItem {
    id: number;
    type: ToastType;
    message: string;
}

@Injectable({ providedIn: 'root' })
export class ToastService {
    public toasts: ToastItem[] = [];
    private nextId = 1;
    private timers = new Map<number, number>();

    public show(message: string, type: ToastType = 'info', durationMs: number = 2800): number {
        const id = this.nextId++;
        this.toasts = [
            ...this.toasts,
            { id, type, message }
        ];

        const timer = window.setTimeout(() => this.dismiss(id), durationMs);
        this.timers.set(id, timer);
        return id;
    }

    public success(message: string, durationMs?: number): number {
        return this.show(message, 'success', durationMs);
    }

    public error(message: string, durationMs?: number): number {
        return this.show(message, 'error', durationMs);
    }

    public info(message: string, durationMs?: number): number {
        return this.show(message, 'info', durationMs);
    }

    public dismiss(id: number): void {
        const timer = this.timers.get(id);
        if (timer !== undefined) {
            window.clearTimeout(timer);
            this.timers.delete(id);
        }
        this.toasts = this.toasts.filter((toast) => toast.id !== id);
    }

    public clear(): void {
        for (const timer of this.timers.values()) {
            window.clearTimeout(timer);
        }
        this.timers.clear();
        this.toasts = [];
    }
}
