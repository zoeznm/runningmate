import { OnInit } from '@angular/core';
import { Service } from '@wiz/libs/portal/season/service';
import { ensureAuthenticated } from 'src/app/shared/auth';
import { safeUserMessage } from 'src/app/shared/api';
import { ToastService } from 'src/app/shared/toast.service';

export class Component implements OnInit {
    public loading: boolean = false;
    public errorMessage: string = '';
    public members: any[] = [];

    public search: any = {
        text: "",
        role: ""
    };

    public roles: string[] = ['admin', 'editor', 'viewer'];

    public showInviteModal: boolean = false;
    public inviteData: any = { email: '', role: 'viewer' };
    public inviting: boolean = false;

    constructor(public service: Service, private readonly toast: ToastService) { }

    public readonly retryLoad = (): void => {
        void this.load();
    };

    public async ngOnInit() {
        await this.service.init();
        if (!(await ensureAuthenticated())) {
            location.replace('/access');
            return;
        }
        await this.load();
    }

    public async load() {
        this.loading = true;
        this.errorMessage = '';
        await this.service.render();

        try {
            const { code, data } = await wiz.call("list", this.search);
            if (code === 200) {
                this.members = data || [];
            } else {
                this.errorMessage = safeUserMessage(data?.message || data, "멤버 목록을 불러오지 못했습니다.");
            }
        } catch {
            this.errorMessage = "인터넷 연결을 확인해줘";
        }

        this.loading = false;
        await this.service.render();
    }

    public async filterByRole(role: string) {
        this.search.role = this.search.role === role ? "" : role;
        await this.load();
    }

    public async openInvite() {
        this.inviteData = { email: '', role: 'viewer' };
        this.showInviteModal = true;
        await this.service.render();
    }

    public async invite() {
        if (this.inviting) return;
        if (!this.inviteData.email) {
            await this.service.modal.error("이메일을 입력해주세요.");
            return;
        }

        this.inviting = true;
        await this.service.render();

        const { code, data } = await wiz.call("invite", this.inviteData);
        this.inviting = false;
        if (code === 200) {
            this.toast.success("초대가 완료되었습니다.");
            this.showInviteModal = false;
            await this.load();
        } else {
            this.toast.error(safeUserMessage(data, "초대에 실패했습니다."));
        }
        await this.service.render();
    }

    public async removeMember(member: any) {
        let res = await this.service.modal.show({
            title: "멤버 제거",
            message: `${member.name}님을 멤버에서 제거하시겠습니까?`,
            action: "제거",
            actionBtn: "error",
            status: "error"
        });
        if (!res) return;

        const { code } = await wiz.call("remove", { id: member.id });
        if (code === 200) {
            this.toast.success("멤버를 제거했습니다.");
            await this.load();
        }
    }

    public roleClass(role: string) {
        switch (role) {
            case 'admin': return 'bg-purple-100 text-purple-700';
            case 'editor': return 'bg-blue-100 text-blue-700';
            case 'viewer': return 'bg-gray-100 text-gray-600';
            default: return 'bg-gray-100 text-gray-600';
        }
    }
}
