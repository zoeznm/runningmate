import datetime
import uuid


TERMS_VERSION = "1.0"
PRIVACY_VERSION = "1.2"
TERMS_EFFECTIVE_DATE = "2026-06-02"
PRIVACY_EFFECTIVE_DATE = "2026-06-09"

TERMS_SECTIONS = [
    {
        "title": "제1조 목적",
        "body": "본 약관은 러닝메이트가 제공하는 러닝 기록, 목표 관리, 커뮤니티 및 관련 서비스의 이용 조건과 절차, 회원과 서비스의 권리와 의무를 정합니다.",
    },
    {
        "title": "제2조 회원 계정",
        "body": "회원은 정확한 정보를 제공해야 하며, 계정과 비밀번호 관리 책임은 회원에게 있습니다. 타인의 정보를 도용하거나 서비스 운영을 방해하는 행위는 제한될 수 있습니다.",
    },
    {
        "title": "제3조 서비스 이용",
        "body": "서비스는 러닝 기록 입력, 이미지 기반 기록 보조, 목표와 챌린지 관리, 게시글 기능을 제공합니다. 서비스 내용은 운영상 필요에 따라 변경될 수 있습니다.",
    },
    {
        "title": "제4조 게시물과 기록",
        "body": "회원이 작성한 러닝 기록과 게시물의 책임은 회원에게 있습니다. 불법 정보, 권리 침해 콘텐츠, 서비스 목적과 무관한 콘텐츠는 숨김 또는 삭제될 수 있습니다.",
    },
    {
        "title": "제5조 서비스 제한",
        "body": "회원이 약관을 위반하거나 보안상 위험을 발생시키는 경우 서비스 이용이 일시 제한될 수 있습니다. 중대한 위반이 반복되면 계정 이용이 중단될 수 있습니다.",
    },
    {
        "title": "제6조 책임의 한계",
        "body": "러닝 기록과 건강 관련 정보는 참고용이며 의학적 판단을 대체하지 않습니다. 회원은 본인의 건강 상태와 안전을 고려하여 서비스를 이용해야 합니다.",
    },
    {
        "title": "제7조 약관 변경",
        "body": "약관이 변경되는 경우 버전과 시행일을 고지합니다. 필수 조항이 변경되면 로그인 후 재동의를 요청할 수 있습니다.",
    },
]

PRIVACY_SECTIONS = [
    {
        "title": "1. 수집하는 개인정보",
        "body": "서비스는 회원가입과 운영을 위해 이메일, 이름, 성별, 비밀번호, 연락처를 수집합니다. 소셜 로그인 이용 시 제공자, 제공자 식별자, 이메일, 이름, 프로필 이미지를 저장할 수 있습니다. 러닝 기록 이용 시 날짜, 거리, 시간, 페이스, 메모, 이미지와 영상 같은 활동 정보가 저장될 수 있습니다.",
    },
    {
        "title": "2. 개인정보 이용 목적",
        "body": "수집한 정보는 회원 식별, 로그인, 러닝 기록 관리, 목표와 챌린지 제공, 고객 지원, 서비스 안정성 개선에 사용됩니다.",
    },
    {
        "title": "3. 보관 기간",
        "body": "회원 정보는 계정 유지 기간 동안 보관됩니다. 회원 탈퇴 또는 계정 삭제 요청이 완료되면 관련 법령과 분쟁 대응에 필요한 범위를 제외하고 지체 없이 삭제합니다. 운영 백업에는 삭제 전 데이터가 일시적으로 남을 수 있으며, 백업 보관 주기가 끝나면 순차적으로 파기합니다.",
    },
    {
        "title": "4. 제3자 제공",
        "body": "서비스는 법령상 근거가 있거나 회원이 별도로 동의한 경우를 제외하고 개인정보를 제3자에게 제공하지 않습니다.",
    },
    {
        "title": "5. 처리 위탁",
        "body": "서비스 운영을 위해 서버, 데이터베이스, 이미지 처리, 메일 발송 등 필요한 범위에서 외부 인프라 또는 개인 서버 운영 환경을 사용할 수 있으며, 위탁이 발생하면 관리 책임을 준수합니다.",
    },
    {
        "title": "6. 회원의 권리",
        "body": "회원은 개인정보 조회, 수정, 삭제, 처리 정지를 요청할 수 있습니다. 마케팅 정보 수신 동의는 언제든 설정에서 변경할 수 있습니다.",
    },
    {
        "title": "7. 계정 삭제",
        "body": "회원은 설정에서 계정 삭제를 요청할 수 있습니다. 삭제가 완료되면 계정 정보, 약관 동의 이력, 소셜 로그인 연결, 비밀번호 재설정 토큰, 러닝 기록, 휴식일, 월간 목표, 사진과 영상, 체중 기록, 뱃지, 채팅 세션, 알림, 친구 관계가 삭제됩니다. 챌린지 생성/참여 이력은 서비스 무결성을 위해 탈퇴한 사용자로 익명화될 수 있습니다. 업로드된 이미지와 영상 파일은 함께 삭제되며, 삭제 후 로그인 세션은 즉시 폐기됩니다. 계정 삭제는 되돌릴 수 없습니다.",
    },
    {
        "title": "8. 개인정보 보호",
        "body": "서비스는 접근 권한 관리, 암호화된 비밀번호 저장, 보안 쿠키 설정, OAuth state 검증, 필요한 범위의 로그 관리 등 개인정보 보호 조치를 적용합니다. 개인 서버 운영 시 데이터베이스와 업로드 파일은 서비스 운영 디렉토리와 백업 디렉토리에서 권한을 제한해 관리합니다.",
    },
]


class Agreement:
    def __init__(self, core):
        self.core = core
        self.db = core.orm.use("user_agreements")

    def current(self):
        return {
            "terms": {
                "title": "이용약관",
                "version": TERMS_VERSION,
                "effective_date": TERMS_EFFECTIVE_DATE,
                "sections": TERMS_SECTIONS,
            },
            "privacy": {
                "title": "개인정보처리방침",
                "version": PRIVACY_VERSION,
                "effective_date": PRIVACY_EFFECTIVE_DATE,
                "sections": PRIVACY_SECTIONS,
            },
        }

    def latest(self, user_id):
        rows = self.db.rows(
            user_id=user_id,
            orderby="agreed_at",
            order="DESC",
            page=1,
            dump=1,
        )
        if rows:
            row = rows[0]
            agreed_at = row.get("agreed_at")
            if hasattr(agreed_at, "strftime"):
                row["agreed_at"] = agreed_at.strftime("%Y-%m-%d %H:%M:%S")
            return row
        return None

    def needs_reagreement(self, user_id):
        latest = self.latest(user_id)
        if latest is None:
            return True
        return (
            str(latest.get("terms_version") or "") != TERMS_VERSION
            or str(latest.get("privacy_version") or "") != PRIVACY_VERSION
        )

    def status(self, user_id=None):
        latest = self.latest(user_id) if user_id else None
        return {
            "current": self.current(),
            "latest": latest,
            "needs_reagreement": self.needs_reagreement(user_id) if user_id else False,
        }

    def record(self, user_id, marketing_optin=False, agreed_at=None, terms_version=None, privacy_version=None):
        if not agreed_at:
            agreed_at = datetime.datetime.now()
        if isinstance(agreed_at, str):
            try:
                agreed_at = datetime.datetime.fromisoformat(agreed_at.replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                agreed_at = datetime.datetime.now()

        return self.db.insert({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "terms_version": str(terms_version or TERMS_VERSION)[:10],
            "privacy_version": str(privacy_version or PRIVACY_VERSION)[:10],
            "marketing_optin": bool(marketing_optin),
            "agreed_at": agreed_at,
        })

    def delete_user(self, user_id):
        self.db.delete(user_id=user_id)


Model = Agreement
