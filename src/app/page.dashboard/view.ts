import { AfterViewInit, ChangeDetectorRef, ElementRef, OnDestroy } from '@angular/core';
import { authHeaderForUrl, clearAuthTokens, ensureAuthenticated, refreshAuthTokens } from 'src/app/shared/auth';
import { apiFetch, apiErrorMessage, jsonRequest, standardApiError } from 'src/app/shared/api';
import { RUNNINGMATE_API_ORIGIN, isNativeLocalOrigin, resolveApiUrl } from 'src/app/shared/api-base';
import { ToastService } from 'src/app/shared/toast.service';
import { PredictionEngine, type HistoryInput } from 'cyclia';

type ScreenKey = 'home' | 'goals' | 'challenges' | 'feed' | 'friends' | 'ranking' | 'achievements' | 'calendar' | 'weight' | 'chart' | 'gallery' | 'chat' | 'ai-settings' | 'settings' | 'profile';
type OnboardingStepKey = 'welcome' | 'menu-record' | 'menu-goal' | 'menu-community' | 'menu-ai' | 'menu-settings' | 'profile' | 'goal' | 'complete';
type CalendarStatus = 'run' | 'rest' | 'no-run' | 'today' | 'future';
type WeatherTone = 'sunny' | 'cloud' | 'rain' | 'snow' | 'mixed';
type MessageSender = 'ai' | 'user';
type ChartPeriod = 'this_week' | 'last_week' | 'monthly';
type TrainingLoadStatus = 'safe' | 'caution' | 'danger';
type WeightPeriod = '1m' | '3m' | 'all';
type RankingPeriod = 'this_week' | 'last_week' | 'this_month';
type RankingScope = 'global' | 'following';
type RunType = 'jogging' | 'long' | 'interval' | 'tempo' | 'race' | 'recovery' | 'strength' | 'home_training';
type GoalType = 'distance' | 'count' | 'duration' | 'pace';
type ChallengeType = 'total_distance' | 'individual_distance' | 'count';
type ChallengeListTab = 'joined' | 'recruiting' | 'owned' | 'ended';
type ChallengeViewMode = 'list' | 'detail' | 'create';
type FriendTab = 'following' | 'followers';
type GalleryTab = 'capture' | 'media' | 'journal';
type RunMediaType = 'photo' | 'video';
type ReactionType = 'like' | 'fire' | 'clap' | 'strong';
type CyclePhase = 'menstrual' | 'follicular' | 'ovulation' | 'luteal';
type CycleSource = 'manual' | 'predicted';
type CycleFlowLevel = 'none' | 'light' | 'normal' | 'heavy';
type ThemeMode = 'dark' | 'light' | 'system';
type DistanceUnit = 'km' | 'mile';
type PaceDisplayMode = 'pace' | 'speed';
type WeekdayId = 'mon' | 'tue' | 'wed' | 'thu' | 'fri' | 'sat' | 'sun';
type PacerPersona = 'balanced' | 'coach' | 'gentle' | 'strict';
type SettingsDetailKey = 'reminder' | 'password' | 'export' | null;
type SettingsExportFormat = 'json' | 'csv';

const KM_PER_MILE = 1.609344;
const AI_PARSE_CONFIGURATION_ERROR_CODES = new Set([
    'missing_api_key',
    'invalid_api_key',
    'insufficient_quota',
    'model_not_found',
    'api_forbidden',
    'openai_error'
]);

interface RunMedia {
    id: string;
    run_id: string;
    media_url: string;
    media_type: RunMediaType;
    created_at?: string;
}

interface MusicTrack {
    id: string;
    title: string;
    artist: string;
    album?: string;
    album_art_url: string;
    url?: string;
}

interface RunRecord {
    id?: string | null;
    date: string;
    distance_km: number;
    avg_pace?: string | null;
    duration?: string | null;
    run_type: RunType;
    calories?: number | null;
    avg_heart_rate?: number | null;
    cadence?: number | null;
    elevation_gain?: number | null;
    water_before_ml?: number | null;
    water_after_ml?: number | null;
    image_url?: string | null;
    journal?: string | null;
    playlist_name?: string | null;
    music_url?: string | null;
    top_tracks?: MusicTrack[];
    media?: RunMedia[];
    is_public?: boolean;
    journal_only?: boolean;
    user_id?: string | null;
    created_at?: string | null;
}

interface DashboardBootstrapData {
    profile?: Partial<UserProfile> | null;
    runs?: unknown[];
    run_count?: number;
    run_limit?: number;
    has_more_runs?: boolean;
    has_media_history?: boolean;
}

interface FeedUser {
    id: string;
    name: string;
    display_id: string;
    profile_image: string;
    is_me: boolean;
}

interface FeedReactionUser {
    user_id: string;
    name: string;
    profile_image: string;
    type: ReactionType;
    created_at: string;
    is_me: boolean;
}

interface FeedReactionSummary {
    type: ReactionType;
    emoji: string;
    label: string;
    count: number;
    reacted: boolean;
    users: FeedReactionUser[];
}

interface FeedComment {
    id: string;
    run_id: string;
    user_id: string;
    user_name: string;
    profile_image: string;
    content: string;
    created_at: string;
    is_mine: boolean;
}

interface CommunityNotification {
    id: string;
    user_id: string;
    actor_id: string;
    actor_name: string;
    type: 'follow' | 'reaction' | 'comment';
    message: string;
    created_at: string;
    read_at: string;
    run_id?: string;
}

interface FeedRun extends RunRecord {
    id: string;
    user: FeedUser;
    reaction_summary: FeedReactionSummary[];
    reaction_count: number;
    comment_count: number;
    comments: FeedComment[];
}

interface WeightLog {
    id?: string | null;
    date: string;
    weight_kg: number;
    created_at?: string;
}

interface HomeData {
    totalKm: number;
    goalKm: number;
    avgPace: string;
    avgHeartRate: number | string;
    totalDurationValue: string;
    totalDurationUnit: string;
    avgCadence: number | string;
    avgKm: number;
    totalCalories: number;
    runCount: number;
    maxKm: number;
    bestPace: string;
    streak: number;
}

interface TabItem {
    id: ScreenKey;
    label: string;
}

interface UserProfile {
    id?: string;
    username?: string;
    display_id?: string;
    display_name?: string;
    email?: string;
    name: string;
    gender?: string;
    mobile?: string;
    running_start_date: string;
    profile_image: string;
    onboarded: boolean;
    is_public: boolean;
    cycle_enabled?: boolean;
    cycle_enabled_configured?: boolean;
}

interface ProfileEditDraft {
    name: string;
    mobile: string;
    running_start_date: string;
    profile_image: string;
    is_public: boolean;
}

interface OnboardingStep {
    id: OnboardingStepKey;
    eyebrow: string;
    title: string;
    body: string;
    icon: string;
    required?: boolean;
}

interface GenderOption {
    id: 'male' | 'female' | 'unspecified';
    label: string;
}

interface GoalRecommendation {
    id: string;
    label: string;
    km: number;
    description: string;
    icon: string;
}

interface NavItem extends TabItem {
    icon: string;
}

interface StatCard {
    icon?: string;
    label: string;
    value: string | number;
    unit: string;
}

interface CalendarCell {
    key: string;
    day: number | null;
    className: string;
    dotClass?: string;
    ariaLabel?: string;
    runCount: number;
    weatherIcon?: string;
    weatherTone?: WeatherTone;
    weatherSummary?: string;
    cyclePhase?: CyclePhase;
    cyclePhaseLabel?: string;
    cycleSource?: CycleSource;
    cycleMarkerClass?: string;
}

interface JournalCalendarCell extends CalendarCell {
    journalCount: number;
    journalRuns: RunRecord[];
}

interface CalendarRunDetail {
    id: string;
    date: string;
    title: string;
    badge: string;
    runType: RunType;
    stats: StatCard[];
    media: RunMedia[];
    waterBeforeMl: number | null;
    waterAfterMl: number | null;
    journal?: string | null;
    playlistName?: string | null;
    musicUrl?: string | null;
    topTracks: MusicTrack[];
    is_public: boolean;
}

interface CalendarNote {
    date: string;
    memo: string;
    updated_at?: string;
}

interface WeatherHourly {
    time: string;
    icon: string;
    tone: WeatherTone;
    summary: string;
    tempText: string;
    popText: string;
    humidityText: string;
    windText: string;
}

interface WeatherDay {
    date: string;
    icon: string;
    tone: WeatherTone;
    summary: string;
    tempText: string;
    popText: string;
    rainText: string;
    snowText: string;
    humidityText: string;
    windText: string;
    hourly: WeatherHourly[];
    locationName?: string;
    locationSource?: string;
    stored?: boolean;
    capturedAt?: string;
}

interface WeatherCoverage {
    startDate: string;
    endDate: string;
    message: string;
}

interface WeatherPosition {
    lat: number;
    lon: number;
}

interface WeatherResponseData {
    year_month?: string;
    location?: {
        name?: string;
        landRegId?: string;
        tempRegId?: string;
        source?: string;
        distanceKm?: number;
    };
    base?: {
        date?: string;
        time?: string;
    };
    coverage?: unknown;
    days?: Record<string, unknown>;
}

interface ChartBar {
    label: string;
    height: number;
    highlight: boolean;
    valueText: string;
}

interface ChartCard {
    title: string;
    bars: ChartBar[];
    footerLeft: string;
    footerRight: string;
}

interface TrendPoint {
    id: string;
    x: number;
    y: number;
    label: string;
    valueText: string;
    title: string;
}

interface TrendSegment {
    id: string;
    left: number;
    top: number;
    width: number;
    transform: string;
}

interface WeightRunBar {
    id: string;
    x: number;
    height: number;
    valueText: string;
    title: string;
}

interface WeightContextStat {
    id: string;
    label: string;
    value: string;
    tone?: string;
}

interface WeightCalendarCell extends CalendarCell {
    weightText?: string;
}

interface WeightSettings {
    target_weight_kg: number | null;
    updated_at?: string;
}

interface ChartPeriodSeries {
    title: string;
    labels: string[];
    groups: RunRecord[][];
    currentLabel: string;
    previousLabel: string;
}

interface Goal {
    id?: string | null;
    year_month: string;
    goal_type: GoalType;
    target_value: number;
    created_at?: string;
}

interface GoalProgress {
    id?: string | null;
    year_month: string;
    goal_type: GoalType;
    label: string;
    target_value: number;
    current_value: number | null;
    remaining_value: number;
    percent: number;
    achieved: boolean;
    unit: string;
    target_text: string;
    current_text: string;
    message: string;
}

interface GoalHistory {
    year_month: string;
    label: string;
    goal_count: number;
    achieved_count: number;
    achieved: boolean;
    items: GoalProgress[];
}

interface GoalTypeOption {
    id: GoalType;
    label: string;
    icon: string;
    unit: string;
    hint: string;
}

interface ChallengeTypeOption {
    id: ChallengeType;
    label: string;
    icon: string;
    unit: string;
    hint: string;
}

interface ChallengeTabOption {
    id: ChallengeListTab;
    label: string;
}

interface FriendTabOption {
    id: FriendTab;
    label: string;
}

interface PublicUserStats {
    total_distance_km: number;
    total_distance_text: string;
    run_count: number;
    this_month_distance_km: number;
    this_month_distance_text: string;
    this_month_run_count: number;
    longest_distance_km: number;
    longest_distance_text: string;
    best_pace: string;
    latest_run_date_text: string;
}

interface SocialProfile {
    id: string;
    email: string;
    display_id: string;
    name: string;
    running_start_date: string;
    profile_image: string;
    is_public: boolean;
    is_me: boolean;
    is_following: boolean;
    is_follower: boolean;
    is_mutual: boolean;
    following_count: number;
    follower_count: number;
    stats_public: boolean;
    stats: PublicUserStats | null;
    badges_public: boolean;
    badges: Badge[];
    earned_badge_count: number;
    total_badge_count: number;
    achievement_rate: number;
}

interface RankingPeriodOption {
    id: RankingPeriod;
    label: string;
}

interface RankingScopeOption {
    id: RankingScope;
    label: string;
}

interface RankingEntry {
    rank: number;
    user_id: string;
    display_id: string;
    name: string;
    profile_image: string;
    distance_km: number;
    distance_text: string;
    run_count: number;
    bar_percent: number;
    is_viewer: boolean;
    is_following: boolean;
    is_follower: boolean;
    is_mutual: boolean;
    highlight: boolean;
    medal: 'gold' | 'silver' | 'bronze' | '';
    privacy: 'public' | 'private';
}

interface RankingPayloadData {
    period: RankingPeriod;
    period_key: string;
    period_label: string;
    start_date: string;
    end_date: string;
    entries: RankingEntry[];
    me: RankingEntry | null;
    motivation_text: string;
    finalized: boolean;
    scope?: RankingScope;
    scope_label?: string;
    target_count?: number;
    viewer?: {
        user_id?: string;
        ranking_enabled?: boolean;
    };
}

interface ChallengeMember {
    challenge_id: string;
    user_id: string;
    user_name: string;
    joined_at: string;
    contributed_value: number;
    contributed_text?: string;
    progress_percent?: number;
    rank?: number;
}

interface Challenge {
    id: string;
    title: string;
    type: ChallengeType;
    type_label: string;
    goal_value: number;
    start_date: string;
    end_date: string;
    creator_id: string;
    creator_name?: string;
    invite_code: string;
    created_at: string;
    members: ChallengeMember[];
    status: string;
    status_label: string;
    member_count: number;
    viewer_joined: boolean;
    viewer_owned: boolean;
    current_value: number;
    target_value: number;
    remaining_value: number;
    progress_percent: number;
    achieved: boolean;
    goal_text: string;
    current_text: string;
    target_text: string;
    remaining_text: string;
    d_day: string;
    period_text: string;
    result_status: 'achieved' | 'missed' | 'in_progress';
    result_text: string;
}

interface ChallengeForm {
    title: string;
    type: ChallengeType;
    goal_value: string;
    start_date: string;
    end_date: string;
}

interface RunTypeOption {
    id: RunType;
    label: string;
}

interface CyclePhaseOption {
    id: CyclePhase;
    label: string;
}

interface CycleConditionOption {
    emoji: string;
    label: string;
}

interface CycleFlowOption {
    id: CycleFlowLevel;
    label: string;
}

interface CycleLog {
    id?: string | null;
    start_date: string;
    end_date: string;
    cycle_phase: CyclePhase;
    flow_level?: CycleFlowLevel | '';
    condition_emoji?: string;
    note?: string;
}

interface CycleWindow {
    start_date: string;
    end_date: string;
    ended_by_none?: boolean;
}

interface CycleSummary {
    average_cycle_days: number;
    average_period_days: number;
    next_start_date?: string | null;
    current_phase?: CyclePhase | null;
    current_phase_label?: string | null;
    log_count: number;
    menstrual_log_count: number;
}

type AppConfirmTone = 'default' | 'danger';

interface AppConfirmOptions {
    title?: string;
    confirmLabel?: string;
    cancelLabel?: string;
    tone?: AppConfirmTone;
    iconClass?: string;
}

interface AppConfirmDialog {
    visible: boolean;
    title: string;
    message: string;
    confirmLabel: string;
    cancelLabel: string;
    tone: AppConfirmTone;
    iconClass: string;
}

interface CycleDayInfo {
    phase: CyclePhase;
    label: string;
    source: CycleSource;
}

interface ConditionDistributionItem {
    emoji: string;
    count: number;
    percent: number;
}

interface CyclePatternStat {
    phase: CyclePhase;
    label: string;
    runCount: number;
    avgPace: string;
    avgDistanceText: string;
    conditionItems: ConditionDistributionItem[];
}

interface RunTypeSummary {
    id: RunType;
    label: string;
    count: number;
    distanceKm: number;
    distanceText: string;
    averagePace: string;
    paceSeconds: number | null;
    countPercent: number;
    distancePercent: number;
}

interface HydrationPattern {
    runCount: number;
    loggedRunCount: number;
    averageMlPerRun: number;
    mlPerKm: number;
    longRunCount: number;
    lowLongRunCount: number;
    coverageText: string;
    guidance: string;
}

interface TrainingLoad {
    streak: number;
    weekly_increase_pct: number | null;
    recommend_rest: boolean;
    reason: string;
    reasons: string[];
    current_week_distance_km: number;
    previous_week_distance_km: number;
    recent_avg_heart_rate: number | null;
    baseline_avg_heart_rate: number | null;
    heart_rate_delta_bpm: number | null;
    negative_condition_streak: number;
    status: TrainingLoadStatus;
    status_label: string;
}

interface TrainingLoadZone {
    id: TrainingLoadStatus;
    label: string;
    width: number;
}

interface GalleryStat {
    label: string;
    value: string | number;
}

interface GalleryItem {
    km: string;
    date: string;
    stats: GalleryStat[];
    runType: RunType;
    altText?: string;
    id?: string;
    imageUrl?: string | null;
    media?: RunMedia;
    run?: RunRecord;
    owner?: FeedUser;
    mediaType?: RunMediaType;
    journal?: string;
    more?: boolean;
}

interface SocialProfileDetail {
    profile: SocialProfile;
    lists_public: boolean;
    following: SocialProfile[];
    followers: SocialProfile[];
    media: GalleryItem[];
}

interface ChatMessage {
    sender: MessageSender;
    text: string;
    created_at?: string;
    streaming?: boolean;
}

interface ChatSession {
    id: string;
    title: string;
    created_at: string;
    updated_at: string;
    day_key: string;
    preview: string;
    message_count: number;
    messages: ChatMessage[];
}

interface ChatHistoryGroup {
    label: string;
    sessions: ChatSession[];
}

interface AiUsage {
    allowed: boolean;
    reason: string;
    message: string;
    action: string;
    day_key: string;
    month_key: string;
    daily_count: number;
    daily_limit: number;
    daily_remaining: number | null;
    monthly_count: number;
    monthly_limit: number;
    monthly_remaining: number | null;
    updated_at?: string;
}

interface BadgeProgress {
    current: number;
    threshold: number;
    percent: number;
    label?: string;
}

interface Badge {
    id: string | number;
    code: string;
    title: string;
    description: string;
    icon: string;
    condition_type: string;
    threshold: number;
    achieved: boolean;
    achieved_at?: string | null;
    progress?: BadgeProgress;
}

interface ChatResponse {
    success: boolean;
    reply?: string;
    message?: string;
    session_id?: string;
    session?: Partial<ChatSession>;
    usage?: Partial<AiUsage>;
}

interface AiConnection {
    configured: boolean;
    provider: string;
    model: string;
    message: string;
    setup_steps: string[];
    mode?: string;
    codex_supported?: boolean;
    codex_authenticated?: boolean;
    codex_status?: string;
    codex_status_message?: string;
    login_refresh_supported?: boolean;
}

interface AppleMusicConnection {
    configured: boolean;
    developer_token: string;
    message: string;
    setup_steps: string[];
}

interface SaveRunResult {
    saved: boolean;
    message?: string;
    run?: RunRecord;
    mediaRunId?: string;
    newlyEarnedBadges?: Badge[];
}

interface AiLoginRefreshResult {
    success: boolean;
    message?: string;
    requires_action?: boolean;
    auth_url?: string;
    user_code?: string;
    expires_in_minutes?: number;
    config?: Partial<AiConnection>;
}

interface SettingsOption<T extends string = string> {
    id: T;
    label: string;
}

interface PacerPersonaOption extends SettingsOption<PacerPersona> {
    description: string;
    examples: ChatMessage[];
}

interface AppSettings {
    unit: DistanceUnit;
    paceDisplay: PaceDisplayMode;
    themeMode: ThemeMode;
    notificationsEnabled: boolean;
    reminderDays: WeekdayId[];
    reminderTime: string;
    restRecommendationEnabled: boolean;
    healthKitConnected: boolean;
    appleMusicConnected: boolean;
    appLockEnabled: boolean;
    pacerPersona: PacerPersona;
}

const EMPTY_HOME_DATA: HomeData = {
    totalKm: 0,
    goalKm: 100,
    avgPace: '-',
    avgHeartRate: '-',
    totalDurationValue: '0h',
    totalDurationUnit: '0m',
    avgCadence: '-',
    avgKm: 0,
    totalCalories: 0,
    runCount: 0,
    maxKm: 0,
    bestPace: '-',
    streak: 0
};

const RUN_TYPE_OPTIONS: RunTypeOption[] = [
    { id: 'jogging', label: '조깅' },
    { id: 'long', label: '장거리' },
    { id: 'interval', label: '인터벌' },
    { id: 'tempo', label: '템포' },
    { id: 'race', label: '대회' },
    { id: 'recovery', label: '회복주' }
];

const SUPPORT_ACTIVITY_OPTIONS: RunTypeOption[] = [
    { id: 'strength', label: '근력운동' },
    { id: 'home_training', label: '홈트' }
];

const SUPPORT_ACTIVITY_TYPES = new Set<RunType>(['strength', 'home_training']);

const GOAL_TYPE_OPTIONS: GoalTypeOption[] = [
    { id: 'distance', label: '월 총 거리', icon: 'fa-route', unit: 'km', hint: '예: 100' },
    { id: 'count', label: '월 러닝 횟수', icon: 'fa-shoe-prints', unit: '회', hint: '예: 12' },
    { id: 'duration', label: '월 총 시간', icon: 'fa-clock', unit: '분', hint: '예: 600' },
    { id: 'pace', label: '평균 페이스', icon: 'fa-gauge-high', unit: '/km', hint: '예: 5:30' }
];

const CHALLENGE_TYPE_OPTIONS: ChallengeTypeOption[] = [
    { id: 'total_distance', label: '다같이 거리 합산', icon: 'fa-route', unit: 'km', hint: '예: 500' },
    { id: 'individual_distance', label: '각자 거리 달성', icon: 'fa-user-check', unit: 'km', hint: '예: 50' },
    { id: 'count', label: '러닝 횟수', icon: 'fa-shoe-prints', unit: '회', hint: '예: 30' }
];

const CHALLENGE_TAB_OPTIONS: ChallengeTabOption[] = [
    { id: 'joined', label: '참여중' },
    { id: 'recruiting', label: '모집중' },
    { id: 'owned', label: '주최' },
    { id: 'ended', label: '종료' }
];

const FRIEND_TAB_OPTIONS: FriendTabOption[] = [
    { id: 'following', label: '팔로잉' },
    { id: 'followers', label: '팔로워' }
];

const FEED_REACTION_SUMMARY: FeedReactionSummary[] = [
    { type: 'like', emoji: '👍', label: '좋아요', count: 0, reacted: false, users: [] },
    { type: 'fire', emoji: '🔥', label: '불꽃', count: 0, reacted: false, users: [] },
    { type: 'clap', emoji: '👏', label: '박수', count: 0, reacted: false, users: [] },
    { type: 'strong', emoji: '💪', label: '힘내', count: 0, reacted: false, users: [] }
];

const RANKING_PERIOD_OPTIONS: RankingPeriodOption[] = [
    { id: 'this_month', label: '이번달' },
    { id: 'this_week', label: '이번주' },
    { id: 'last_week', label: '지난주' }
];

const RANKING_SCOPE_OPTIONS: RankingScopeOption[] = [
    { id: 'global', label: '전체' },
    { id: 'following', label: '내 친구' }
];

const EMPTY_GOAL_DRAFTS: Record<GoalType, string> = {
    distance: '',
    count: '',
    duration: '',
    pace: ''
};

const DEFAULT_AI_CHAT_DAILY_LIMIT = 5;
const DEFAULT_AI_CHAT_MONTHLY_LIMIT = 120;

const ONBOARDING_STEPS: OnboardingStep[] = [
    {
        id: 'welcome',
        eyebrow: 'WELCOME',
        title: '나는 너의 러닝메이트 페이서야!',
        body: '홈에서 오늘 상태를 보고, 아래 메뉴로 기록과 목표, 커뮤니티, AI, 설정을 이동해.',
        icon: 'fa-person-running'
    },
    {
        id: 'menu-record',
        eyebrow: '기록',
        title: '운동 기록 사진을 업로드해주세요',
        body: '운동 앱 캡처나 러닝 기록 사진을 올리면 날짜, 거리, 페이스를 분석해 달력에 저장해.',
        icon: 'fa-cloud-arrow-up'
    },
    {
        id: 'menu-goal',
        eyebrow: '목표',
        title: '목표와 챌린지를 같이 관리해',
        body: '월간 거리 목표를 세우고 챌린지와 업적으로 꾸준히 달리는 흐름을 만들 수 있어.',
        icon: 'fa-bullseye'
    },
    {
        id: 'menu-community',
        eyebrow: '커뮤니티',
        title: '친구 기록과 랭킹을 확인해',
        body: '피드에서 공개 기록을 보고, 랭킹과 내 프로필로 러닝 흐름을 비교할 수 있어.',
        icon: 'fa-user-group'
    },
    {
        id: 'menu-ai',
        eyebrow: 'AI',
        title: '페이서에게 다음 러닝을 물어봐',
        body: '저장된 기록을 바탕으로 회복, 목표, 다음 훈련을 대화로 정리할 수 있어. 베타 기간에는 하루 5회, 월 120회 한도로 제공해.',
        icon: 'fa-message'
    },
    {
        id: 'menu-settings',
        eyebrow: '설정',
        title: '내 러닝 환경을 맞춰줘',
        body: '테마, 거리 단위, 페이서 말투, 계정 관리를 내 사용 방식에 맞게 조정해.',
        icon: 'fa-gear'
    },
    {
        id: 'profile',
        eyebrow: 'PROFILE',
        title: '프로필을 설정해줘',
        body: '닉네임과 러닝 시작일은 첫 기록을 맞추는 데 필요해.',
        icon: 'fa-user-check',
        required: true
    },
    {
        id: 'goal',
        eyebrow: 'GOAL',
        title: '첫 월 목표를 정해보자',
        body: '지금 수준에 맞는 거리로 시작하면 달성 흐름을 만들기 쉬워.',
        icon: 'fa-bullseye',
        required: true
    },
    {
        id: 'complete',
        eyebrow: 'READY',
        title: '러닝을 시작해보세요.',
        body: '준비가 끝났어요. RunMate와 함께 오늘의 러닝을 시작해보세요.',
        icon: 'fa-flag-checkered'
    }
];

const GOAL_RECOMMENDATIONS: GoalRecommendation[] = [
    { id: 'beginner', label: '초보', km: 30, description: '주 2회 가볍게 시작', icon: 'fa-seedling' },
    { id: 'intermediate', label: '중급', km: 60, description: '주 3회 꾸준한 루틴', icon: 'fa-person-running' },
    { id: 'advanced', label: '상급', km: 100, description: '장거리 포함 집중 목표', icon: 'fa-mountain-sun' }
];

const CYCLE_PHASE_OPTIONS: CyclePhaseOption[] = [
    { id: 'menstrual', label: '생리기' },
    { id: 'follicular', label: '난포기' },
    { id: 'ovulation', label: '배란기' },
    { id: 'luteal', label: '황체기' }
];

const CYCLE_CONDITION_OPTIONS: CycleConditionOption[] = [
    { emoji: '😊', label: '좋음' },
    { emoji: '😐', label: '보통' },
    { emoji: '😣', label: '힘듦' }
];

const CYCLE_FLOW_OPTIONS: CycleFlowOption[] = [
    { id: 'none', label: '없음' },
    { id: 'light', label: '적음' },
    { id: 'normal', label: '보통' },
    { id: 'heavy', label: '많음' }
];

const EMPTY_CYCLE_SUMMARY: CycleSummary = {
    average_cycle_days: 28,
    average_period_days: 7,
    next_start_date: null,
    current_phase: null,
    current_phase_label: null,
    log_count: 0,
    menstrual_log_count: 0
};

const EMPTY_HYDRATION_PATTERN: HydrationPattern = {
    runCount: 0,
    loggedRunCount: 0,
    averageMlPerRun: 0,
    mlPerKm: 0,
    longRunCount: 0,
    lowLongRunCount: 0,
    coverageText: '수분 기록 없음',
    guidance: '업로드할 때 러닝 전후 물 섭취량을 남기면 패턴을 볼 수 있어.'
};

const EMPTY_TRAINING_LOAD: TrainingLoad = {
    streak: 0,
    weekly_increase_pct: null,
    recommend_rest: false,
    reason: '회복 지표는 안전 구간이야.',
    reasons: [],
    current_week_distance_km: 0,
    previous_week_distance_km: 0,
    recent_avg_heart_rate: null,
    baseline_avg_heart_rate: null,
    heart_rate_delta_bpm: null,
    negative_condition_streak: 0,
    status: 'safe',
    status_label: '안전'
};

const TRAINING_LOAD_GAUGE_MAX = 60;
const TRAINING_LOAD_ZONES: TrainingLoadZone[] = [
    { id: 'safe', label: '안전', width: 16.67 },
    { id: 'caution', label: '주의', width: 33.33 },
    { id: 'danger', label: '위험', width: 50 }
];

const WEEKDAY_OPTIONS: SettingsOption<WeekdayId>[] = [
    { id: 'mon', label: '월' },
    { id: 'tue', label: '화' },
    { id: 'wed', label: '수' },
    { id: 'thu', label: '목' },
    { id: 'fri', label: '금' },
    { id: 'sat', label: '토' },
    { id: 'sun', label: '일' }
];

const UNIT_OPTIONS: SettingsOption<DistanceUnit>[] = [
    { id: 'km', label: 'km' },
    { id: 'mile', label: 'mile' }
];

const PACE_DISPLAY_OPTIONS: SettingsOption<PaceDisplayMode>[] = [
    { id: 'pace', label: '페이스' },
    { id: 'speed', label: '속도' }
];

const THEME_MODE_OPTIONS: SettingsOption<ThemeMode>[] = [
    { id: 'dark', label: '다크' },
    { id: 'light', label: '라이트' },
    { id: 'system', label: '시스템' }
];

const PACER_PERSONA_OPTIONS: PacerPersonaOption[] = [
    {
        id: 'balanced',
        label: '밸런스',
        description: '기록과 컨디션을 같이 보고 현실적인 선택지를 제안해.',
        examples: [
            { sender: 'user', text: '오늘은 몸이 좀 무거워.' },
            { sender: 'ai', text: '그럼 페이스보다 호흡을 먼저 보자. 20분 회복주로 낮추고 끝나면 수분을 챙겨줘.' }
        ]
    },
    {
        id: 'coach',
        label: '코치형',
        description: '목표 기준으로 훈련 계획과 다음 액션을 또렷하게 잡아줘.',
        examples: [
            { sender: 'user', text: '이번 주 목표 어떻게 갈까?' },
            { sender: 'ai', text: '월/수는 짧게, 주말은 6km로 가자. 오늘은 4km 이지런부터 시작해.' }
        ]
    },
    {
        id: 'gentle',
        label: '다정형',
        description: '부담을 낮추고 회복과 지속성을 먼저 챙겨줘.',
        examples: [
            { sender: 'user', text: '기록이 좀 아쉬워.' },
            { sender: 'ai', text: '괜찮아. 오늘 기록도 다음 러닝을 위한 힌트야. 무리하지 말고 회복부터 챙기자.' }
        ]
    },
    {
        id: 'strict',
        label: '엄격형',
        description: '핑계를 줄이고 약속한 러닝을 실행하도록 단호하게 말해줘.',
        examples: [
            { sender: 'user', text: '오늘도 미뤄도 될까?' },
            { sender: 'ai', text: '미루는 흐름이 반복되고 있어. 15분이라도 나가서 약속을 지키자.' }
        ]
    }
];

const DEFAULT_APP_SETTINGS: AppSettings = {
    unit: 'km',
    paceDisplay: 'pace',
    themeMode: 'dark',
    notificationsEnabled: false,
    reminderDays: ['mon', 'wed', 'fri'],
    reminderTime: '07:30',
    restRecommendationEnabled: true,
    healthKitConnected: false,
    appleMusicConnected: false,
    appLockEnabled: false,
    pacerPersona: 'balanced'
};

export class Component implements AfterViewInit, OnDestroy {
    public activeScreen: ScreenKey = 'home';
    public isDark: boolean = true;
    public appSettings: AppSettings = this.cloneDefaultSettings();
    public activeSettingsDetail: SettingsDetailKey = null;
    public readonly appVersion: string = '1.0.0';
    public readonly weekdayOptions = WEEKDAY_OPTIONS;
    public readonly unitOptions = UNIT_OPTIONS;
    public readonly paceDisplayOptions = PACE_DISPLAY_OPTIONS;
    public readonly themeModeOptions = THEME_MODE_OPTIONS;
    public readonly pacerPersonaOptions = PACER_PERSONA_OPTIONS;
    public pacerPersonaDraft: PacerPersona = DEFAULT_APP_SETTINGS.pacerPersona;
    public isInitialLoading: boolean = true;
    public initialLoadingDetail: string = '러닝 기록을 불러오는 중';
    public readonly initialLoadingTips: string[] = [
        '오늘의 러닝 기록을 한곳에 모으고 있어요.',
        '목표 달성률을 계산하고 다음 러닝을 준비하고 있어요.',
        '친구 피드와 랭킹을 최신 상태로 맞추고 있어요.',
        'AI 페이서가 최근 흐름을 읽고 있어요.',
        '캘린더와 기록 메모를 정리하고 있어요.'
    ];
    public initialErrorMessage: string = '';
    public profile: UserProfile | null = null;
    public isProfileEditOpen: boolean = false;
    public isProfileSaving: boolean = false;
    public profileEditStatus: string = '';
    public profileEditDraft: ProfileEditDraft = {
        name: '',
        mobile: '',
        running_start_date: this.dateKey(new Date()),
        profile_image: '',
        is_public: true
    };
    public onboardingSteps: OnboardingStep[] = ONBOARDING_STEPS;
    public goalRecommendations: GoalRecommendation[] = GOAL_RECOMMENDATIONS;
    public isOnboardingVisible: boolean = false;
    public isOnboardingSaving: boolean = false;
    public isOnboardingSkipConfirmVisible: boolean = false;
    public onboardingIndex: number = 0;
    public onboardingStatus: string = '';
    public onboardingProfile: Pick<UserProfile, 'name' | 'running_start_date' | 'profile_image' | 'gender'> = {
        name: '',
        running_start_date: this.dateKey(new Date()),
        profile_image: '',
        gender: ''
    };
    public readonly onboardingGenderOptions: GenderOption[] = [
        { id: 'male', label: '남성' },
        { id: 'female', label: '여성' },
        { id: 'unspecified', label: '선택 안함' }
    ];
    public onboardingGoalKm: number = 30;
    public notificationPermissionState: NotificationPermission | 'unsupported' = 'unsupported';
    public healthKitAcknowledged: boolean = false;
    public readonly homeEmptyAction = (): void => this.openTodayUpload();
    public homeData: HomeData = { ...EMPTY_HOME_DATA };
    public statCards: StatCard[] = [];
    public summaryCards: StatCard[] = [];
    public goals: Goal[] = [];
    public goalProgressCards: GoalProgress[] = [];
    public goalHistory: GoalHistory[] = [];
    public goalTypeOptions: GoalTypeOption[] = GOAL_TYPE_OPTIONS;
    public goalDrafts: Record<GoalType, string> = { ...EMPTY_GOAL_DRAFTS };
    public goalStatus: string = '';
    public isGoalSaving: boolean = false;
    public deletingGoalType: GoalType | null = null;
    public challenges: Challenge[] = [];
    public challengeTypeOptions: ChallengeTypeOption[] = CHALLENGE_TYPE_OPTIONS;
    public challengeTabOptions: ChallengeTabOption[] = CHALLENGE_TAB_OPTIONS;
    public activeChallengeTab: ChallengeListTab = 'joined';
    public challengeViewMode: ChallengeViewMode = 'list';
    public selectedChallengeId: string | null = null;
    public challengeInviteCode: string = '';
    public challengeStatus: string = '';
    public isChallengeLoading: boolean = false;
    public isChallengeSaving: boolean = false;
    public isChallengeJoining: boolean = false;
    public deletingChallengeId: string | null = null;
    public challengeForm: ChallengeForm = {
        title: '',
        type: 'total_distance',
        goal_value: '',
        start_date: this.dateKey(new Date()),
        end_date: this.dateKey(this.addDays(new Date(), 30))
    };
    public feedItems: FeedRun[] = [];
    public feedStatus: string = '';
    public isFeedLoading: boolean = false;
    public feedBusyKey: string = '';
    public feedCommentDrafts: Record<string, string> = {};
    public expandedReactionRunId: string | null = null;
    public expandedCommentsRunId: string | null = null;
    public deletingFeedCommentId: string | null = null;
    public privacyBusyRunId: string | null = null;
    public communityNotifications: CommunityNotification[] = [];
    public isCommunityNotificationLoading: boolean = false;
    public friendTabOptions: FriendTabOption[] = FRIEND_TAB_OPTIONS;
    public activeFriendTab: FriendTab = 'following';
    public friendSearchQuery: string = '';
    public friendSearchResults: SocialProfile[] = [];
    public friendCode: string = '';
    public friendCodeInput: string = '';
    public friendCodeStatus: string = '';
    public followingUsers: SocialProfile[] = [];
    public followerUsers: SocialProfile[] = [];
    public selectedFriendProfile: SocialProfile | null = null;
    public profileSocialPanelTab: FriendTab | null = null;
    public viewedProfile: SocialProfile | null = null;
    public viewedProfileFollowingUsers: SocialProfile[] = [];
    public viewedProfileFollowerUsers: SocialProfile[] = [];
    public viewedProfileMediaItems: GalleryItem[] = [];
    public viewedProfileListsPublic: boolean = true;
    public viewedProfileListTab: FriendTab | null = null;
    public viewedProfileStatus: string = '';
    public isViewedProfileLoading: boolean = false;
    public friendStatus: string = '';
    public isFriendSearchLoading: boolean = false;
    public isFriendCodeLoading: boolean = false;
    public isFriendCodeAdding: boolean = false;
    public isFriendListLoading: boolean = false;
    public followBusyUserId: string | null = null;
    public rankingPeriodOptions: RankingPeriodOption[] = RANKING_PERIOD_OPTIONS;
    public rankingScopeOptions: RankingScopeOption[] = RANKING_SCOPE_OPTIONS;
    public activeRankingPeriod: RankingPeriod = 'this_month';
    public activeRankingScope: RankingScope = 'global';
    public rankingEntries: RankingEntry[] = [];
    public rankingMe: RankingEntry | null = null;
    public rankingPeriodLabel: string = '';
    public rankingScopeLabel: string = '전체 랭킹';
    public rankingTargetCount: number = 0;
    public rankingMotivationText: string = '';
    public rankingStatus: string = '';
    public isRankingLoading: boolean = false;
    public isRankingSaving: boolean = false;
    public rankingParticipationEnabled: boolean = true;
    public rankingFinalized: boolean = false;
    public calendarCells: CalendarCell[] = [];
    public calendarStats: StatCard[] = [];
    public restDays: string[] = [];
    public selectedCalendarDate: string | null = null;
    public calendarMemoText: string = '';
    public calendarMemoStatus: string = '';
    public isCalendarMemoSaving: boolean = false;
    public selectedCalendarRuns: CalendarRunDetail[] = [];
    public isCycleFeatureEnabled: boolean = false;
    public isCycleOverlayEnabled: boolean = true;
    public cycleLogs: CycleLog[] = [];
    public cycleSummary: CycleSummary = { ...EMPTY_CYCLE_SUMMARY };
    public cyclePhaseOptions: CyclePhaseOption[] = CYCLE_PHASE_OPTIONS;
    public cycleConditionOptions: CycleConditionOption[] = CYCLE_CONDITION_OPTIONS;
    public cycleFlowOptions: CycleFlowOption[] = CYCLE_FLOW_OPTIONS;
    public cycleStartDate: string = this.dateKey(new Date());
    public cycleEndDate: string = this.dateKey(new Date());
    public selectedCycleFlowLevel: CycleFlowLevel = 'normal';
    public selectedCycleConditionEmoji: string = '😐';
    public cycleNoteText: string = '';
    public isCycleNoteEditing: boolean = false;
    public cycleStatus: string = '';
    public isCycleSaving: boolean = false;
    public deletingCycleId: string | null = null;
    public cyclePatternStats: CyclePatternStat[] = [];
    public isWeatherLoading: boolean = false;
    public weatherStatus: string = '';
    public weatherLocationText: string = '';
    public weatherUpdatedText: string = '';
    public isWeatherLocationBusy: boolean = false;
    public activeWeightPeriod: WeightPeriod = '3m';
    public weightLogs: WeightLog[] = [];
    public visibleWeightLogs: WeightLog[] = [];
    public weightDate: string = this.dateKey(new Date());
    public weightInput: string = '';
    public weightStatus: string = '';
    public isWeightSaving: boolean = false;
    public deletingWeightDate: string | null = null;
    public targetWeightKg: number | null = null;
    public weightTargetInput: string = '';
    public weightTargetStatus: string = '';
    public isWeightTargetSaving: boolean = false;
    public isWeightTargetEditing: boolean = false;
    public weightCalendarCells: WeightCalendarCell[] = [];
    public weightChartPoints: TrendPoint[] = [];
    public weightChartSegments: TrendSegment[] = [];
    public weightRunBars: WeightRunBar[] = [];
    public weightContextStats: WeightContextStat[] = [];
    public activeChartPeriod: ChartPeriod = 'this_week';
    public chartCards: ChartCard[] = [];
    public runTypeStats: RunTypeSummary[] = [];
    public miniStats: StatCard[] = [];
    public homeRecentRuns: RunRecord[] = [];
    public badges: Badge[] = [];
    public selectedBadge: Badge | null = null;
    public newlyEarnedBadges: Badge[] = [];
    public galleryItems: GalleryItem[] = [];
    public galleryTab: GalleryTab = 'capture';
    public journalCalendarCells: JournalCalendarCell[] = [];
    public selectedJournalDate: string | null = null;
    public selectedJournalRuns: RunRecord[] = [];
    public runTypeOptions: RunTypeOption[] = RUN_TYPE_OPTIONS;
    public selectedRunType: RunType = 'jogging';
    public hydrationQuickOptions: number[] = [250, 500, 750];
    public waterBeforeInput: string = '';
    public waterAfterInput: string = '';
    public uploadJournalText: string = '';
    public appleMusicConnection: AppleMusicConnection = {
        configured: false,
        developer_token: '',
        message: '',
        setup_steps: []
    };
    public appleMusicStatus: string = '';
    public appleMusicRecentTracks: MusicTrack[] = [];
    public selectedMusicTrackIds: string[] = [];
    public playlistNameInput: string = '';
    public musicUrlInput: string = '';
    public isAppleMusicLoading: boolean = false;
    public appleMusicTracksVisible: boolean = false;
    public hydrationPattern: HydrationPattern = { ...EMPTY_HYDRATION_PATTERN };
    public trainingLoad: TrainingLoad = { ...EMPTY_TRAINING_LOAD };
    public readonly trainingLoadZones: TrainingLoadZone[] = TRAINING_LOAD_ZONES;
    public isRestBannerDismissed: boolean = false;
    public chatMessages: ChatMessage[] = [];
    public chatSessions: ChatSession[] = [];
    public activeChatSessionId: string | null = null;
    public chatDayPromptSession: ChatSession | null = null;
    public aiUsage: AiUsage | null = null;
    public isChatHistoryOpen: boolean = false;
    public isChatHistoryLoading: boolean = false;
    public deletingChatSessionId: string | null = null;
    public uploadStatus: string = '';
    public uploadProgress: number = 0;
    public isUploading: boolean = false;
    public parseErrorMessage: string = '';
    public uploadJournalStatus: string = '';
    public isUploadJournalSaving: boolean = false;
    public calendarMediaDraftFiles: File[] = [];
    public calendarMediaDraftStatus: string = '';
    public calendarUploadIsPublic: boolean = true;
    public manualEntryVisible: boolean = false;
    public manualEntryRunId: string | null = null;
    public recordReuploadTargetId: string | null = null;
    public manualRunForm: any = {
        distance_km: '',
        avg_pace: '',
        duration: '',
        calories: '',
        avg_heart_rate: '',
        cadence: ''
    };
    public isManualRunSaving: boolean = false;
    public aiConnection: AiConnection | null = null;
    public chatText: string = '';
    public isChatSending: boolean = false;
    public aiLoginRefreshStatus: string = '';
    public aiLoginRefreshPending: boolean = false;
    public aiLoginDeviceUrl: string = '';
    public aiLoginDeviceCode: string = '';
    public aiLoginDeviceExpiresIn: number | null = null;
    public runMediaStatus: string = '';
    public uploadingMediaRunId: string | null = null;
    public deletingMediaId: string | null = null;
    public activeMediaViewer: RunMedia | null = null;
    public activeProfileFeedItem: GalleryItem | null = null;
    public activeProfileFeedMedia: RunMedia | null = null;
    public activeProfileFeedRun: FeedRun | null = null;
    public profileFeedSocialStatus: string = '';
    public isProfileFeedSocialLoading: boolean = false;
    public activeJournalViewer: RunRecord | null = null;
    public editingJournalRunId: string | null = null;
    public savingJournalRunId: string | null = null;
    public journalDraftText: string = '';
    public journalStatusRunId: string | null = null;
    public journalStatusText: string = '';
    public deleteStep: number = 0;
    public deletingAccount: boolean = false;
    public accountDeleted: boolean = false;
    public isLoggingOut: boolean = false;
    public accountDeleteForm: { confirm_text: string } = {
        confirm_text: ''
    };
    public passwordForm = {
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
        invalidateOtherSessions: true
    };
    public changingPassword: boolean = false;
    public confirmDialog: AppConfirmDialog = {
        visible: false,
        title: '확인',
        message: '',
        confirmLabel: '확인',
        cancelLabel: '취소',
        tone: 'default',
        iconClass: 'fa-circle-question'
    };

    private runs: RunRecord[] = [];
    private confirmDialogResolver: ((confirmed: boolean) => void) | null = null;
    private pendingMediaRunId: string | null = null;
    private calendarNotes = new Map<string, CalendarNote>();
    private cycleDayMap = new Map<string, CycleDayInfo>();
    private cyclePredictionEngine = new PredictionEngine({ strategy: 'wma', lutealPhaseDays: 14, timezone: 'Asia/Seoul' });
    private weatherDays = new Map<string, WeatherDay>();
    private weatherCoverage: WeatherCoverage | null = null;
    private initialRunsTruncated: boolean = false;
    private runMediaLoaded: boolean = false;
    private deferredDashboardDataStarted: boolean = false;
    private initialCoreDataLoaded: boolean = false;
    private agreementModalVisibleForLoading: boolean = false;
    private activeYearMonth: string = this.yearMonthKey(new Date());
    private activeWeightYearMonth: string = this.yearMonthKey(new Date());
    private readonly cleanupHandlers: Array<() => void> = [];
    private readonly initialDashboardRunLimit: number = 60;
    private readonly initialRunFields: string[] = [
        'id',
        'date',
        'distance_km',
        'avg_pace',
        'duration',
        'run_type',
        'calories',
        'avg_heart_rate',
        'cadence',
        'elevation_gain',
        'water_before_ml',
        'water_after_ml',
        'journal',
        'is_public',
        'user_id',
        'created_at'
    ];
    private readonly mediaAccessNoticeAcceptedKey: string = 'runningmate-media-access-notice-accepted-v1';
    private readonly cycleEnabledStorageKey: string = 'runningmate-cycle-enabled-v1';
    private readonly cycleOverlayStorageKey: string = 'runningmate-cycle-overlay-v1';
    private readonly restBannerDismissStorageKey: string = 'runningmate-rest-banner-dismissed-v1';
    private readonly appSettingsStorageKey: string = 'runningmate-settings-v1';
    private readonly pacerPersonaStorageKey: string = 'runningmate-pacer-persona-v1';
    private readonly appleMusicUserTokenStorageKey: string = 'runningmate-apple-music-user-token-v1';
    private readonly weightTargetStorageKey: string = 'runningmate-weight-target-v1';
    private readonly weatherPositionStorageKey: string = 'runningmate-weather-position-v1';
    private readonly agreementModalBodyClass: string = 'runningmate-agreement-modal-visible';
    private readonly agreementModalEventName: string = 'runningmate:agreement-modal';
    private readonly onboardingScreenMap: Partial<Record<OnboardingStepKey, ScreenKey>> = {
        welcome: 'home',
        'menu-record': 'calendar',
        'menu-goal': 'goals',
        'menu-community': 'feed',
        'menu-ai': 'chat',
        'menu-settings': 'settings',
        profile: 'home',
        goal: 'goals',
        complete: 'calendar'
    };
    private readonly weatherRefreshIntervalMs: number = 30 * 60 * 1000;
    private readonly initialDashboardTaskTimeoutMs: number = 9000;
    private isCyclePreferenceSaving: boolean = false;
    private readonly initialLoadingStepPriority: string[] = [
        'auth',
        'location',
        'weather',
        'ai',
        'runs',
        'profile',
        'chat',
        'feed',
        'friends',
        'friendCode',
        'ranking',
        'goals',
        'challenges',
        'notifications',
        'weights',
        'training',
        'badges',
        'dayNotes',
        'restDays',
        'music',
        'cycles'
    ];
    private initialLoadingSteps = new Map<string, string>();
    private onboardingTouchStartX: number | null = null;
    private weatherRequestSeq: number = 0;
    private weatherRefreshTimer: number | null = null;
    private weatherPosition: WeatherPosition | null = null;
    private calendarSwipeStartX: number | null = null;
    private calendarSwipeStartY: number | null = null;
    private calendarDateClickSuppressUntil: number = 0;
    private accountDeleteRedirectTimer: number | null = null;
    private lastWeatherLoadedAt: number = 0;
    private systemThemeQuery: MediaQueryList | null = null;
    private readonly dashboardViewportClass: string = 'is-dashboard-page';
    private readonly dashboardViewportProperty: string = '--dashboard-visual-height';
    private readonly dashboardScreenBgProperty: string = '--dashboard-screen-bg';
    private dashboardThemeMeta: HTMLMetaElement | null = null;
    private dashboardAppRootElement: HTMLElement | null = null;
    private previousDashboardThemeColor: string = '';
    private previousRootBackground: string = '';
    private previousBodyBackground: string = '';
    private previousAppRootBackground: string = '';
    private previousRootScreenBg: string = '';
    private previousBodyScreenBg: string = '';
    private previousAppRootScreenBg: string = '';
    private readonly updateDashboardViewportHeight = (): void => {
        this.syncDashboardViewportHeight();
    };
    private readonly systemThemeListener = (event: MediaQueryListEvent): void => {
        if (this.appSettings.themeMode !== 'system') return;
        this.isDark = event.matches;
        this.syncDashboardChrome();
        this.cdr.detectChanges();
    };

    constructor(
        private readonly elementRef: ElementRef<HTMLElement>,
        private readonly cdr: ChangeDetectorRef,
        private readonly toast: ToastService
    ) {
        this.loadAppSettings();
        this.weatherPosition = this.readStoredWeatherPosition();
        this.applyInitialScreenFromLocation();
        this.startSystemThemeListener();
        this.refreshDerivedState();
    }

    public readonly retryInitialLoad = (): void => {
        void this.loadInitialDashboardData();
    };

    private setInitialLoadingStep(key: string, detail: string): void {
        if (!this.isInitialLoading) return;
        this.initialLoadingSteps.set(key, detail);
        this.refreshInitialLoadingDetail();
    }

    private clearInitialLoadingStep(key: string): void {
        if (!this.isInitialLoading || !this.initialLoadingSteps.has(key)) return;
        this.initialLoadingSteps.delete(key);
        this.refreshInitialLoadingDetail();
    }

    private refreshInitialLoadingDetail(): void {
        if (this.agreementModalVisibleForLoading) {
            this.initialLoadingDetail = '이용 약관 동의 중';
            this.cdr.detectChanges();
            return;
        }

        const activeKey = this.initialLoadingStepPriority.find((key) => this.initialLoadingSteps.has(key));
        this.initialLoadingDetail = activeKey
            ? this.initialLoadingSteps.get(activeKey) || '초기 데이터를 준비하는 중'
            : '초기 데이터를 정리하는 중';
        this.cdr.detectChanges();
    }

    private async runInitialLoadingStep<T>(key: string, detail: string, task: () => Promise<T>): Promise<T> {
        this.setInitialLoadingStep(key, detail);
        try {
            return await task();
        } finally {
            this.clearInitialLoadingStep(key);
        }
    }

    private async withInitialTaskTimeout<T>(task: Promise<T>, detail: string, timeoutMs: number = this.initialDashboardTaskTimeoutMs): Promise<T> {
        if (typeof window === 'undefined') return task;

        let timeoutId: number | null = null;
        const timeout = new Promise<T>((_, reject) => {
            timeoutId = window.setTimeout(() => {
                reject(standardApiError('timeout', {
                    message: `${detail} 시간이 초과됐어. 다시 시도해줘`
                }));
            }, timeoutMs);
        });

        try {
            return await Promise.race([task, timeout]);
        } finally {
            if (timeoutId !== null) {
                window.clearTimeout(timeoutId);
            }
        }
    }

    private async runDeferredDashboardTask(task: () => Promise<void>, detail: string = '요청 처리'): Promise<void> {
        try {
            await this.withInitialTaskTimeout(task(), detail);
        } catch {
            // Deferred dashboard data should never block the first usable screen.
        }
    }

    private async runInitialDashboardTask(key: string, detail: string, task: () => Promise<void>): Promise<void> {
        await this.runInitialLoadingStep(key, detail, () => this.runDeferredDashboardTask(task, detail));
    }

    private async loadDeferredDashboardEssentials(): Promise<void> {
        await Promise.all([
            this.runDeferredDashboardTask(() => this.loadDayNotes(), '기록 메모를 불러오는 중'),
            this.runDeferredDashboardTask(() => this.loadRestDays(), '휴식일을 불러오는 중'),
            this.runDeferredDashboardTask(() => this.loadWeights(), '체중 설정을 불러오는 중'),
            this.runDeferredDashboardTask(() => this.loadBadges(), '업적을 불러오는 중'),
            this.runDeferredDashboardTask(() => this.loadGoalsForActiveMonth(), '목표를 불러오는 중'),
            this.runDeferredDashboardTask(() => this.loadChallenges(), '챌린지를 불러오는 중'),
            this.runDeferredDashboardTask(() => this.loadFeed(true), '커뮤니티를 불러오는 중'),
            this.runDeferredDashboardTask(() => this.loadFriendLists(true), '친구 목록을 불러오는 중'),
            this.runDeferredDashboardTask(() => this.loadFriendCode(), '친구 코드를 불러오는 중'),
            this.runDeferredDashboardTask(() => this.loadCommunityNotifications(true), '알림을 불러오는 중'),
            this.runDeferredDashboardTask(() => this.loadRanking(), '랭킹을 불러오는 중'),
            this.runDeferredDashboardTask(() => this.loadChatHistory(true), 'AI 대화 기록을 불러오는 중'),
            this.runDeferredDashboardTask(() => this.loadAiConnection(), 'AI 설정을 불러오는 중'),
            this.runDeferredDashboardTask(() => this.loadAppleMusicConnection(), '음악 설정을 불러오는 중'),
            this.runDeferredDashboardTask(() => this.loadTrainingLoad(), '분석 데이터를 불러오는 중')
        ]);

        if (this.shouldShowCycleFeature && this.isCycleFeatureEnabled) {
            await this.runDeferredDashboardTask(() => this.loadCycles(), '주기 설정을 불러오는 중');
        }
    }

    private async loadDeferredDashboardExtras(): Promise<void> {
        await Promise.all([
            this.runDeferredDashboardTask(() => this.loadWeights(), '체중 설정을 불러오는 중'),
            this.runDeferredDashboardTask(() => this.loadBadges(), '업적을 불러오는 중'),
            this.runDeferredDashboardTask(() => this.loadChatHistory(true), 'AI 대화 기록을 불러오는 중'),
            this.runDeferredDashboardTask(() => this.loadAiConnection(), 'AI 설정을 불러오는 중'),
            this.runDeferredDashboardTask(() => this.loadAppleMusicConnection(), '음악 설정을 불러오는 중'),
            this.runDeferredDashboardTask(() => this.loadTrainingLoad(), '분석 데이터를 불러오는 중')
        ]);

        if (this.shouldShowCycleFeature && this.isCycleFeatureEnabled) {
            await this.runDeferredDashboardTask(() => this.loadCycles(), '주기 설정을 불러오는 중');
        }
    }

    private async loadInitialDashboardCoreData(): Promise<void> {
        if (this.initialRunsTruncated) {
            const allRunsLoaded = await this.runInitialLoadingStep('runs', '전체 러닝 기록을 정리하는 중', () => (
                this.loadRuns(true, false, true, this.runsUrl({ includeMedia: false }), false)
            ));
            if (!allRunsLoaded) return;
            this.initialRunsTruncated = false;
        }

        const coreTasks: Array<Promise<void>> = [
            this.runInitialDashboardTask('dayNotes', '기록 메모를 정리하는 중', () => this.loadDayNotes()),
            this.runInitialDashboardTask('restDays', '휴식일을 확인하는 중', () => this.loadRestDays()),
            this.runInitialDashboardTask('weather', '기록 달력 날씨를 확인하는 중', () => this.loadWeatherForActiveMonth()),
            this.runInitialDashboardTask('goals', '목표 달성률을 계산하는 중', () => this.loadGoalsForActiveMonth()),
            this.runInitialDashboardTask('challenges', '챌린지를 확인하는 중', () => this.loadChallenges()),
            this.runInitialDashboardTask('feed', '커뮤니티 피드를 불러오는 중', () => this.loadFeed(true)),
            this.runInitialDashboardTask('friends', '친구 목록을 불러오는 중', () => this.loadFriendLists(true)),
            this.runInitialDashboardTask('friendCode', '친구 코드를 준비하는 중', () => this.loadFriendCode()),
            this.runInitialDashboardTask('notifications', '알림을 확인하는 중', () => this.loadCommunityNotifications(true)),
            this.runInitialDashboardTask('ranking', '랭킹을 계산하는 중', () => this.loadRanking())
        ];
        if (this.shouldShowCycleFeature && this.isCycleFeatureEnabled) {
            coreTasks.push(this.runInitialDashboardTask('cycles', '주기 기록을 정리하는 중', () => this.loadCycles()));
        }
        await Promise.all(coreTasks);
        this.initialCoreDataLoaded = true;
    }

    private async deferredDashboardYield(delayMs: number = 80): Promise<void> {
        if (typeof window === 'undefined') return;
        await new Promise<void>((resolve) => window.setTimeout(resolve, delayMs));
    }

    private scheduleDeferredDashboardData(): void {
        if (this.deferredDashboardDataStarted) return;
        this.deferredDashboardDataStarted = true;

        const run = (): void => {
            void this.loadDeferredDashboardData();
        };

        if (typeof window === 'undefined') {
            run();
            return;
        }

        window.setTimeout(run, 0);
    }

    private async loadDeferredDashboardData(): Promise<void> {
        if (this.initialCoreDataLoaded) {
            await this.loadDeferredDashboardExtras();
        } else {
            await this.loadDeferredDashboardEssentials();
        }
        await this.deferredDashboardYield();

        if (this.initialRunsTruncated) {
            await this.runDeferredDashboardTask(() => this.loadRuns(false, false, true, this.runsUrl({ includeMedia: false }), false));
            this.initialRunsTruncated = false;
            await this.deferredDashboardYield();
        }

        if (this.activeScreen === 'calendar') {
            await this.runDeferredDashboardTask(() => this.loadWeatherForActiveMonth());
        }
        if (this.activeScreen === 'gallery' && !this.runMediaLoaded) {
            await this.runDeferredDashboardTask(() => this.loadRuns(false, false, true, this.runsUrl({ includeMedia: true }), true));
        }
        this.cdr.detectChanges();
    }

    public readonly switchToManualInput = (): void => {
        this.openManualEntry();
    };

    public navItems: NavItem[] = [
        { id: 'home', label: '홈', icon: 'fa-house' },
        { id: 'calendar', label: '기록', icon: 'fa-calendar-days' },
        { id: 'goals', label: '목표', icon: 'fa-bullseye' },
        { id: 'feed', label: '커뮤니티', icon: 'fa-user-group' },
        { id: 'chat', label: 'AI', icon: 'fa-message' },
        { id: 'settings', label: '설정', icon: 'fa-gear' }
    ];

    public recordGroupItems: NavItem[] = [
        { id: 'calendar', label: '달력', icon: 'fa-calendar-days' },
        { id: 'weight', label: '체중', icon: 'fa-weight-scale' },
        { id: 'chart', label: '분석', icon: 'fa-chart-simple' },
        { id: 'gallery', label: '갤러리', icon: 'fa-images' }
    ];

    public goalGroupItems: NavItem[] = [
        { id: 'goals', label: '목표', icon: 'fa-bullseye' },
        { id: 'challenges', label: '챌린지', icon: 'fa-people-group' },
        { id: 'achievements', label: '업적', icon: 'fa-medal' }
    ];

    public communityGroupItems: NavItem[] = [
        { id: 'feed', label: '피드', icon: 'fa-heart' },
        { id: 'friends', label: '친구', icon: 'fa-user-plus' },
        { id: 'ranking', label: '랭킹', icon: 'fa-ranking-star' },
        { id: 'profile', label: '내 프로필', icon: 'fa-user' }
    ];

    private readonly navActiveGroups: Partial<Record<ScreenKey, ScreenKey[]>> = {
        calendar: ['calendar', 'weight', 'chart', 'gallery'],
        goals: ['goals', 'challenges', 'achievements'],
        feed: ['feed', 'friends', 'ranking', 'profile'],
        chat: ['chat', 'ai-settings'],
        settings: ['settings']
    };
    private readonly routeScreenMap: Record<string, ScreenKey> = {
        home: 'home',
        calendar: 'calendar',
        goals: 'goals',
        feed: 'feed',
        chat: 'chat',
        settings: 'settings'
    };

    public get phoneClass(): string {
        return this.isDark ? 'phone-frame dark-screen' : 'phone-frame light-screen';
    }

    public get currentOnboardingStep(): OnboardingStep {
        return this.onboardingSteps[this.onboardingIndex] || this.onboardingSteps[0];
    }

    public get onboardingProgressPercent(): number {
        return Math.round(((this.onboardingIndex + 1) / this.onboardingSteps.length) * 100);
    }

    public get canSkipOnboardingStep(): boolean {
        if (this.currentOnboardingStep?.id === 'complete') return false;
        const profileIndex = this.onboardingSteps.findIndex((step) => step.id === 'profile');
        return profileIndex >= 0 && this.onboardingIndex > profileIndex;
    }

    public get onboardingPrimaryText(): string {
        if (this.isOnboardingSaving) return '저장 중';
        if (this.currentOnboardingStep?.id === 'complete') return 'RunMate와 시작하기';
        return '다음';
    }

    public get onboardingGoalMonth(): string {
        const [year, month] = this.activeYearMonth.split('-');
        return `${year}년 ${Number(month)}월`;
    }

    public get remainingKm(): number {
        const remaining = this.homeData.goalKm - this.homeData.totalKm;
        return Math.max(0, this.round2(remaining));
    }

    public get progressPercent(): number {
        if (!this.homeData.goalKm) {
            return 0;
        }

        return Math.min(100, Math.round((this.homeData.totalKm / this.homeData.goalKm) * 100));
    }

    public get progressStyle(): { width: string } {
        return {
            width: `${this.progressPercent}%`
        };
    }

    public get primaryGoalProgress(): GoalProgress | null {
        return this.goalProgressCards[0] || null;
    }

    public get goalProgressStyle(): { width: string } {
        return {
            width: `${this.primaryGoalProgress?.percent || 0}%`
        };
    }

    public get hasGoalProgress(): boolean {
        return this.goalProgressCards.length > 0;
    }

    public get goalSmallCards(): GoalProgress[] {
        return this.goalProgressCards.filter((goal) => ['distance', 'count', 'duration'].includes(goal.goal_type));
    }

    public get paceGoalCard(): GoalProgress | null {
        return this.goalProgressCards.find((goal) => goal.goal_type === 'pace') || null;
    }

    public get goalMonthTitle(): string {
        const [year, month] = this.activeYearMonth.split('-');
        return `${year}년 ${Number(month)}월 목표`;
    }

    public get joinedChallenges(): Challenge[] {
        return this.challenges.filter((challenge) => challenge.viewer_joined && challenge.status !== 'ended');
    }

    public get recruitingChallenges(): Challenge[] {
        return this.challenges.filter((challenge) => challenge.status !== 'ended');
    }

    public get ownedChallenges(): Challenge[] {
        return this.challenges.filter((challenge) => challenge.viewer_owned);
    }

    public get endedChallenges(): Challenge[] {
        return this.challenges.filter((challenge) => challenge.status === 'ended');
    }

    public get activeChallengeList(): Challenge[] {
        if (this.activeChallengeTab === 'recruiting') return this.recruitingChallenges;
        if (this.activeChallengeTab === 'owned') return this.ownedChallenges;
        if (this.activeChallengeTab === 'ended') return this.endedChallenges;
        return this.joinedChallenges;
    }

    public get selectedChallenge(): Challenge | null {
        if (this.selectedChallengeId) {
            const selected = this.challenges.find((challenge) => challenge.id === this.selectedChallengeId);
            if (selected) return selected;
        }
        return this.activeChallengeList[0] || this.joinedChallenges[0] || this.challenges[0] || null;
    }

    public get challengeCreateButtonText(): string {
        return this.isChallengeSaving ? '생성 중' : '챌린지 생성';
    }

    public get challengeJoinButtonText(): string {
        return this.isChallengeJoining ? '참여 중' : '참여';
    }

    public get challengeGoalUnit(): string {
        return this.challengeForm.type === 'count' ? '회' : this.distanceUnitLabel;
    }

    public get challengeGoalPlaceholder(): string {
        if (this.challengeForm.type !== 'count') {
            return this.appSettings.unit === 'mile' ? '예: 31' : '예: 50';
        }
        return this.challengeTypeOptions.find((option) => option.id === this.challengeForm.type)?.hint || '예: 100';
    }

    public get challengeSummaryText(): string {
        return `${this.joinedChallenges.length}개 참여 · ${this.recruitingChallenges.length}개 모집 · ${this.ownedChallenges.length}개 주최`;
    }

    public get feedSummaryText(): string {
        if (this.isFeedLoading && !this.feedItems.length) return '피드 불러오는 중';
        if (!this.feedItems.length) return '최근 공개 기록 없음';
        return `최근 공개 기록 ${this.feedItems.length}개`;
    }

    public get feedEmptyDescription(): string {
        if (!this.followingUsers.length) return '친구를 팔로우하면 공개 러닝 기록이 여기에 모여.';
        return '팔로잉한 친구의 공개 기록이 생기면 피드에 표시돼.';
    }

    public get communityUnreadCount(): number {
        return this.communityNotifications.filter((item) => !item.read_at).length;
    }

    public get communityNotificationSummaryText(): string {
        if (this.isCommunityNotificationLoading && !this.communityNotifications.length) return '알림 확인 중';
        return this.communityUnreadCount ? `읽지 않은 알림 ${this.communityUnreadCount}개` : '새 알림 없음';
    }

    public get activeFriendList(): SocialProfile[] {
        return this.activeFriendTab === 'followers' ? this.followerUsers : this.followingUsers;
    }

    public get activeProfileSocialList(): SocialProfile[] {
        return this.profileSocialPanelTab === 'followers' ? this.followerUsers : this.followingUsers;
    }

    public get activeViewedProfileSocialList(): SocialProfile[] {
        return this.viewedProfileListTab === 'followers' ? this.viewedProfileFollowerUsers : this.viewedProfileFollowingUsers;
    }

    public get profileSocialPanelTitle(): string {
        return this.profileSocialPanelTab === 'followers' ? '팔로워' : '팔로잉';
    }

    public get profileSocialPanelCount(): number {
        return this.activeProfileSocialList.length;
    }

    public get viewedProfileListTitle(): string {
        return this.viewedProfileListTab === 'followers' ? '팔로워' : '팔로잉';
    }

    public get viewedProfileListCount(): number {
        return this.activeViewedProfileSocialList.length;
    }

    public get viewedProfileFeedEmptyTitle(): string {
        return this.viewedProfileListsPublic ? '표시할 사진/영상 피드가 없어' : '맞팔이 되면 피드를 볼 수 있어';
    }

    public get friendSummaryText(): string {
        if (this.isFriendListLoading && !this.followingUsers.length && !this.followerUsers.length) return '친구 목록 불러오는 중';
        return `팔로잉 ${this.followingUsers.length}명 · 팔로워 ${this.followerUsers.length}명`;
    }

    public get friendCodeText(): string {
        if (this.isFriendCodeLoading && !this.friendCode) return '불러오는 중';
        return this.friendCode || '-';
    }

    public get friendCodeShareText(): string {
        return this.friendCode ? `러닝메이트 친구코드 ${this.friendCode}` : '';
    }

    public get friendCodeCanSubmit(): boolean {
        return Boolean(this.friendCodeInput.trim()) && !this.isFriendCodeAdding;
    }

    public get selectedFriendInitial(): string {
        return this.avatarText(this.selectedFriendProfile?.name || this.selectedFriendProfile?.display_id || '');
    }

    public get selectedFriendRelationText(): string {
        const profile = this.selectedFriendProfile;
        if (!profile) return '';
        if (profile.is_me) return '내 프로필';
        if (profile.is_mutual) return '서로 팔로우';
        if (profile.is_following) return '팔로잉';
        if (profile.is_follower) return '나를 팔로우';
        return '미팔로우';
    }

    public profileBadgeItems(profile: SocialProfile | null): Badge[] {
        return (profile?.badges || []).filter((badge) => badge.achieved);
    }

    public profileBadgeSummaryText(profile: SocialProfile | null): string {
        if (!profile?.badges_public) return '뱃지 비공개';
        if (!profile.earned_badge_count) return '획득 뱃지 없음';
        return `뱃지 ${profile.earned_badge_count}/${profile.total_badge_count || profile.earned_badge_count}`;
    }

    public viewedProfileDistanceText(profile: SocialProfile | null): string {
        return profile?.stats ? this.distanceText(profile.stats.total_distance_km) : this.distanceText(0);
    }

    public viewedProfileStartDateText(profile: SocialProfile | null): string {
        return profile?.running_start_date || this.todayDateKey;
    }

    public get myProfileRunCount(): number {
        return this.runs
            .filter((run) => run.is_public !== false)
            .reduce((sum, run) => sum + (run.media || []).length, 0);
    }

    public get myProfileFollowingCount(): number {
        return this.followingUsers.length;
    }

    public get myProfileFollowerCount(): number {
        return this.followerUsers.length;
    }

    public get myProfileDistanceText(): string {
        return this.distanceText(this.runs.reduce((sum, run) => sum + run.distance_km, 0));
    }

    public get myProfileDisplayIdText(): string {
        return this.profile?.email || this.profile?.mobile || this.profile?.id || '@runningmate';
    }

    public get myProfileStartDateText(): string {
        return this.effectiveRunningStartDate(this.profile);
    }

    public get myProfileMediaItems(): GalleryItem[] {
        return this.runs
            .filter((run) => run.is_public !== false)
            .flatMap((run) => (run.media || []).map((media) => {
                const km = this.distanceText(run.distance_km, true);
                const date = this.displayDate(run.date, false);
                return {
                    id: media.id,
                    km,
                    date,
                    stats: [],
                    runType: run.run_type,
                    altText: `${date} ${km} 러닝 첨부 ${this.mediaTypeLabel(media.media_type)}`,
                    imageUrl: media.media_url,
                    media,
                    run,
                    owner: this.myFeedUser(),
                    mediaType: media.media_type
                } as GalleryItem;
            }))
            .slice(0, 12);
    }

    public get rankingTitleText(): string {
        return this.activeRankingScope === 'following' ? '내 친구 랭킹' : '전체 랭킹';
    }

    public get rankingScopeDescription(): string {
        if (this.activeRankingScope === 'following') {
            const targetCount = this.rankingTargetCount || this.followingUsers.length;
            if (!targetCount) return '내 친구 없음 · 내 기록만 표시';
            return `내 친구 ${targetCount}명 + 내 기록`;
        }
        return '앱 전체 참여자 기준';
    }

    public get rankingLeaderLabelText(): string {
        return this.activeRankingScope === 'following' ? '내 친구 1위' : '전체 1위';
    }

    public get rankingMeSubText(): string {
        const period = this.rankingPeriodLabel || '현재 기간';
        return `${period} · ${this.rankingLeaderLabelText} ${this.rankingTopDistanceText}`;
    }

    public get rankingSummaryText(): string {
        if (this.isRankingLoading && !this.rankingEntries.length) return '랭킹 불러오는 중';
        if (!this.rankingEntries.length) return '참여자 없음';
        const finalized = this.rankingFinalized ? '마감' : '진행중';
        return `${this.rankingEntries.length}명 · ${finalized}`;
    }

    public get rankingMotivationDisplayText(): string {
        return this.convertDistanceTextUnits(this.rankingMotivationText);
    }

    public get rankingMyTitle(): string {
        if (!this.rankingMe) return '내 순위 없음';
        return `내 순위 ${this.rankingMe.rank}위`;
    }

    public get rankingMyDistanceText(): string {
        return this.rankingMe ? this.formatDistance(this.rankingMe.distance_km) : '0.00';
    }

    public get rankingParticipationStatusText(): string {
        if (this.isRankingSaving) return '저장 중';
        return this.rankingParticipationEnabled ? '참여 중' : '숨김';
    }

    public get rankingTopDistanceText(): string {
        return this.rankingEntries[0] ? this.distanceText(this.rankingEntries[0].distance_km) : this.distanceText(0);
    }

    public rankingDistanceText(entry: RankingEntry): string {
        return this.distanceText(entry.distance_km);
    }

    public get rankingEmptyDescription(): string {
        if (!this.rankingParticipationEnabled) return '참여를 켜면 내 거리만 공개하고 상세 기록은 비공개로 유지돼.';
        if (this.activeRankingScope === 'following' && !this.followingUsers.length) return '내 친구가 없어 내 기록만 표시돼.';
        if (this.activeRankingScope === 'following') return '내 친구의 공개 기록이 쌓이면 표시돼.';
        return '랭킹 참여자의 기록이 쌓이면 표시돼.';
    }

    public get earnedBadgeCount(): number {
        return this.badges.filter((badge) => badge.achieved).length;
    }

    public get totalBadgeCount(): number {
        return this.badges.length;
    }

    public get badgeAchievementRate(): number {
        return this.totalBadgeCount ? Math.round((this.earnedBadgeCount / this.totalBadgeCount) * 100) : 0;
    }

    public get badgeRateText(): string {
        return `${this.earnedBadgeCount}/${this.totalBadgeCount || 30}`;
    }

    public get badgeProgressText(): string {
        if (!this.totalBadgeCount) return '업적 불러오는 중';
        return `${this.badgeRateText} 획득 · ${this.badgeAchievementRate}%`;
    }

    public get selectedBadgeDateText(): string {
        return this.selectedBadge?.achieved_at ? this.formatBadgeDate(this.selectedBadge.achieved_at) : '미획득';
    }

    public get celebrationLeadBadge(): Badge | null {
        return this.newlyEarnedBadges[0] || null;
    }

    public get uploadProgressStyle(): { width: string } {
        return {
            width: `${this.uploadProgress}%`
        };
    }

    public get goalMessage(): string {
        const pending = this.goalProgressCards.find((goal) => !goal.achieved);
        if (pending?.message) return pending.message;
        if (this.goalProgressCards.length) return '이번달 목표를 모두 달성했어.';
        return '이번달 목표를 설정해보자.';
    }

    public get showRestRecommendationBanner(): boolean {
        return Boolean(
            this.appSettings.restRecommendationEnabled &&
            this.trainingLoad.recommend_rest &&
            !this.isRestBannerDismissed &&
            !this.isRestDate(this.todayDateKey)
        );
    }

    public get restRecommendationMessage(): string {
        const reason = this.trainingLoad.reason || '회복이 필요한 신호가 있어';
        return `🛌 오늘은 쉬는 게 어때? ${reason}`;
    }

    public get trainingLoadStatusClass(): string {
        return `load-${this.trainingLoad.status || 'safe'}`;
    }

    public get trainingLoadIncreaseText(): string {
        const pct = this.trainingLoad.weekly_increase_pct;
        return pct === null ? '비교 없음' : `${Math.round(pct)}%`;
    }

    public get trainingLoadNeedleStyle(): Record<string, string> {
        const raw = this.trainingLoad.weekly_increase_pct ?? 0;
        const percent = Math.max(0, Math.min(100, (raw / TRAINING_LOAD_GAUGE_MAX) * 100));
        return { left: `${percent}%` };
    }

    public get trainingLoadDistanceText(): string {
        return `이번주 ${this.distanceText(this.trainingLoad.current_week_distance_km)} / 지난주 ${this.distanceText(this.trainingLoad.previous_week_distance_km)}`;
    }

    public get trainingLoadGuidanceText(): string {
        if (this.trainingLoad.recommend_rest) {
            return `${this.trainingLoad.reason} 부상 위험을 낮추려면 오늘은 회복일로 두는 게 좋아.`;
        }
        if (this.trainingLoad.status === 'caution') {
            return `${this.trainingLoad.reason} 뛰더라도 회복주 강도로 낮춰보자.`;
        }
        return this.trainingLoad.reason;
    }

    public get formattedTotalKm(): string {
        return this.formatDistance(this.homeData.totalKm);
    }

    public get formattedAvgKm(): string {
        return this.formatDistance(this.homeData.avgKm);
    }

    public get formattedCalories(): string {
        return new Intl.NumberFormat('ko-KR').format(this.homeData.totalCalories);
    }

    public get homeTitle(): string {
        return `${Number(this.activeYearMonth.slice(5, 7))}월 러닝`;
    }

    public get calendarTitle(): string {
        const [year, month] = this.activeYearMonth.split('-');
        return `${year}년 ${Number(month)}월`;
    }

    public get activeMonthRunCount(): number {
        return this.runs.filter((run) => run.date.startsWith(this.activeYearMonth)).length;
    }

    public get activeMonthJournalCount(): number {
        return this.buildJournalRuns().filter((run) => run.date.startsWith(this.activeYearMonth)).length;
    }

    public get selectedCalendarDateText(): string {
        return this.selectedCalendarDate ? this.displayDate(this.selectedCalendarDate, true) : '';
    }

    public get selectedCalendarEmptyText(): string {
        if (!this.selectedCalendarDate) return '';
        if (this.isRestDate(this.selectedCalendarDate)) return '휴식일로 지정한 날이야.';

        const todayKey = this.dateKey(new Date());
        return this.selectedCalendarDate > todayKey
            ? '아직 기록할 수 없는 날짜야.'
            : '이 날짜의 러닝 기록이 없어.';
    }

    public get restActionDate(): string | null {
        return this.selectedCalendarDate;
    }

    public get isRestActionDate(): boolean {
        return this.isRestDate(this.restActionDate);
    }

    public get canToggleRestDay(): boolean {
        const date = this.restActionDate;
        if (!date) return false;
        return this.isRestDate(date) || !this.hasRunsOnDate(date);
    }

    public get restButtonText(): string {
        const date = this.restActionDate;
        if (date && this.isRestDate(date)) return '휴식일 해제';
        return '휴식일로 지정';
    }

    public get canUploadSelectedCalendarDate(): boolean {
        return Boolean(
            this.selectedCalendarDate &&
            this.selectedCalendarDate <= this.dateKey(new Date()) &&
            !this.isRestDate(this.selectedCalendarDate)
        );
    }

    public get calendarUploadHelpText(): string {
        if (!this.selectedCalendarDate) return '날짜를 선택하면 기록을 업로드할 수 있어.';
        if (this.isRestDate(this.selectedCalendarDate)) return '휴식일 해제 후 기록을 업로드할 수 있어.';
        if (!this.canUploadSelectedCalendarDate) return '미래 날짜는 지나간 뒤 업로드할 수 있어.';

        return '운동 앱 캡처 이미지를 선택하면 날짜, 거리, 페이스를 읽어 저장해.';
    }

    public get shouldShowCalendarMediaAccessNotice(): boolean {
        return !this.hasAcceptedMediaAccessNotice();
    }

    public get calendarUploadButtonText(): string {
        if (this.isUploading) return '처리 중';
        return this.canUploadSelectedCalendarDate ? '캡처 이미지 업로드' : '업로드 불가';
    }

    public get calendarMediaDraftText(): string {
        if (this.calendarMediaDraftFiles.length) return `${this.calendarMediaDraftFiles.length}개 선택됨`;
        return '기록 저장 후 함께 보관할 사진이나 영상을 선택해줘.';
    }

    public get calendarMediaDraftButtonText(): string {
        if (this.isUploading) return '업로드 중';
        return this.calendarMediaDraftFiles.length ? '추가 선택' : '사진/영상 추가';
    }

    public get canSaveSelectedCalendarActivity(): boolean {
        return Boolean(
            this.selectedCalendarDate &&
            this.selectedCalendarDate <= this.dateKey(new Date()) &&
            !this.isRestDate(this.selectedCalendarDate) &&
            !this.hasRunsOnDate(this.selectedCalendarDate)
        );
    }

    public get calendarUploadPrivacyText(): string {
        return this.calendarUploadIsPublic ? '피드 공개' : '피드 비공개';
    }

    public get hasSavedUploadJournal(): boolean {
        return Boolean(this.memoForDate(this.selectedCalendarDate).trim());
    }

    public get uploadJournalSaveButtonText(): string {
        if (this.isUploadJournalSaving) return '저장 중';
        if (!this.uploadJournalText.trim() && this.hasSavedUploadJournal) return '일기 지우기';
        return '일기 저장';
    }

    public get isUploadJournalSaveDisabled(): boolean {
        if (this.isUploadJournalSaving || this.isUploading || this.isManualRunSaving) return true;
        if (!this.canUploadSelectedCalendarDate) return true;

        const draft = this.uploadJournalText.trim();
        const saved = this.memoForDate(this.selectedCalendarDate).trim();
        return !draft && !saved;
    }

    public isRunRecordUploadActive(runId?: string | null): boolean {
        return Boolean(runId && this.recordReuploadTargetId === runId);
    }

    public isRunRecordReuploading(runId?: string | null): boolean {
        return Boolean(runId && this.isUploading && this.recordReuploadTargetId === runId);
    }

    public runRecordReuploadButtonText(run: CalendarRunDetail): string {
        return this.isRunRecordReuploading(run.id) ? '업로드 중' : '기록 다시 업로드';
    }

    public runRecordManualButtonText(run: CalendarRunDetail): string {
        return this.manualEntryVisible && this.manualEntryRunId === run.id ? '수동 입력 중' : '수동 수정';
    }

    public get hydrationDraftTotalMl(): number {
        return (this.waterAmountFromInput(this.waterBeforeInput) || 0) + (this.waterAmountFromInput(this.waterAfterInput) || 0);
    }

    public get hydrationUploadHelpText(): string {
        if (!this.hydrationDraftTotalMl) return '선택 사항';
        return `총 ${this.hydrationDraftTotalMl}ml 함께 저장`;
    }

    public get hasSelectedCalendarMemo(): boolean {
        return Boolean(this.selectedCalendarDate && this.calendarNotes.has(this.selectedCalendarDate));
    }

    public get selectedCalendarWeather(): WeatherDay | null {
        return this.selectedCalendarDate ? this.weatherDays.get(this.selectedCalendarDate) || null : null;
    }

    public get selectedCalendarWeatherEmptyText(): string {
        if (this.isWeatherLoading) return '날씨 불러오는 중';
        const coverageText = this.selectedCalendarDate ? this.selectedWeatherCoverageText(this.selectedCalendarDate) : '';
        if (coverageText) return coverageText;
        if (this.weatherStatus) return this.weatherStatus;
        return '날씨 정보 없음';
    }

    public get selectedCalendarWeatherSourceText(): string {
        const weather = this.selectedCalendarWeather;
        if (weather?.stored) {
            return weather.capturedAt ? `저장된 날씨 · ${weather.capturedAt.slice(0, 10)}` : '저장된 날씨';
        }
        return this.weatherUpdatedText;
    }

    public get calendarMemoButtonText(): string {
        if (this.isCalendarMemoSaving) return '저장 중';
        return this.calendarMemoText.trim() ? '메모 저장' : '메모 지우기';
    }

    public get cycleFeatureStatusText(): string {
        if (!this.isCycleFeatureEnabled) return '꺼짐';
        return this.cycleSummary.menstrual_log_count ? `생리 기록 ${this.cycleSummary.menstrual_log_count}개` : '켜짐';
    }

    public get cycleNextDateText(): string {
        return this.cycleSummary.next_start_date ? this.displayDate(this.cycleSummary.next_start_date, false) : '기록 대기';
    }

    public get cycleAverageText(): string {
        return `${this.cycleSummary.average_cycle_days || 28}일 평균`;
    }

    public get cycleCurrentPhaseText(): string {
        return this.cycleSummary.current_phase_label || '예측 대기';
    }

    public get cycleSaveButtonText(): string {
        if (this.isCycleSaving) return '저장 중';
        if (this.isCycleNoteEditing) return '저장하기';
        return this.selectedCalendarCycleLog ? '수정하기' : '저장하기';
    }

    public get cyclePrimaryIconClass(): string {
        if (this.isCycleSaving) return 'fa-spinner';
        if (this.isCycleNoteEditing) return 'fa-floppy-disk';
        return this.selectedCalendarCycleLog ? 'fa-pen-to-square' : 'fa-floppy-disk';
    }

    public get isCycleFormReadOnly(): boolean {
        return Boolean(this.selectedCalendarCycleLog && !this.isCycleNoteEditing);
    }

    public get selectedCalendarCycleText(): string {
        const info = this.selectedCalendarDate ? this.cycleDayMap.get(this.selectedCalendarDate) : null;
        if (info?.phase === 'menstrual' && info.source === 'predicted') return '생리 예정';
        if (info) return info.label;
        const log = this.selectedCalendarCycleLog;
        return log?.flow_level === 'none' ? '생리 없음' : '주기 예측 대기';
    }

    public get selectedCalendarCyclePhase(): CyclePhase | null {
        const info = this.selectedCalendarDate ? this.cycleDayMap.get(this.selectedCalendarDate) : null;
        return info?.phase || null;
    }

    public get selectedCalendarCycleLog(): CycleLog | null {
        const date = this.selectedCalendarDate;
        if (!date) return null;
        const noneLog = this.cycleLogs.find((log) => (
            log.cycle_phase === 'menstrual' &&
            log.flow_level === 'none' &&
            log.start_date <= date &&
            log.end_date >= date
        ));
        if (noneLog) return noneLog;

        return this.cycleLogs.find((log) => (
            log.cycle_phase === 'menstrual' &&
            log.flow_level !== 'none' &&
            log.start_date <= date &&
            log.end_date >= date
        )) || null;
    }

    public get recentCycleLogs(): CycleLog[] {
        const date = this.selectedCalendarDate;
        if (!date) return [];

        return this.cycleLogs
            .filter((log) => log.cycle_phase === 'menstrual' && log.start_date <= date && log.end_date >= date)
            .slice(0, 5);
    }

    public get hasCyclePatternStats(): boolean {
        return this.cyclePatternStats.some((item) => item.runCount > 0);
    }

    public get cyclePatternInsightText(): string {
        if (!this.isCycleFeatureEnabled) return '';
        const candidates = this.cyclePatternStats
            .map((item) => ({ item, pace: this.paceSeconds(item.avgPace) }))
            .filter((entry): entry is { item: CyclePatternStat; pace: number } => entry.pace !== null && entry.item.runCount > 0);
        if (!candidates.length) {
            return '주기 기록과 러닝 기록이 같이 쌓이면 단계별 차이를 볼 수 있어.';
        }

        const best = candidates.sort((a, b) => a.pace - b.pace)[0].item;
        return `기록상 ${best.label}에 페이스가 가장 좋았어. 컨디션 개인차가 크니 참고 지표로만 보자.`;
    }

    public get todayDateKey(): string {
        return this.dateKey(new Date());
    }

    public get currentWeightLog(): WeightLog | null {
        return this.weightLogs[0] || null;
    }

    public get startWeightLog(): WeightLog | null {
        return this.weightLogs.length ? this.weightLogs[this.weightLogs.length - 1] : null;
    }

    public get currentWeightText(): string {
        const current = this.currentWeightLog;
        return current ? current.weight_kg.toFixed(1) : '-';
    }

    public get weightChangeText(): string {
        const current = this.currentWeightLog;
        const start = this.startWeightLog;
        if (!current || !start || current.date === start.date) return '변화 없음';

        const diff = this.round1(current.weight_kg - start.weight_kg);
        if (diff === 0) return '0.0kg';
        const arrow = diff < 0 ? '▼' : '▲';
        const sign = diff > 0 ? '+' : '';
        return `${arrow} ${sign}${diff.toFixed(1)}kg`;
    }

    public get weightChangeTone(): string {
        const current = this.currentWeightLog;
        const start = this.startWeightLog;
        if (!current || !start) return '';

        const diff = this.round1(current.weight_kg - start.weight_kg);
        if (diff < 0) return 'down';
        if (diff > 0) return 'up';
        return 'same';
    }

    public get weightPeriodTitle(): string {
        if (this.activeWeightPeriod === '1m') return '최근 1개월';
        if (this.activeWeightPeriod === 'all') return '전체';
        return '최근 3개월';
    }

    public get weightCalendarTitle(): string {
        const [year, month] = this.activeWeightYearMonth.split('-');
        return `${year}년 ${Number(month)}월`;
    }

    public get selectedWeightDateText(): string {
        const date = this.normalizeDateKey(this.weightDate);
        return date ? this.displayDate(date, true) : '';
    }

    public get selectedWeightLog(): WeightLog | null {
        const date = this.normalizeDateKey(this.weightDate);
        return date ? this.weightLogs.find((log) => log.date === date) || null : null;
    }

    public get targetWeightText(): string {
        return this.targetWeightKg !== null ? this.targetWeightKg.toFixed(1) : '-';
    }

    public get weightGoalRemainingText(): string {
        const current = this.currentWeightLog?.weight_kg ?? null;
        const target = this.targetWeightKg;
        if (current === null || target === null) return '목표 대기';

        const diff = this.round1(current - target);
        if (diff > 0) return `${diff.toFixed(1)}kg 감량 필요`;
        if (diff === 0) return '목표 도달';
        return `목표보다 ${Math.abs(diff).toFixed(1)}kg 낮음`;
    }

    public get weightGoalTone(): string {
        const current = this.currentWeightLog?.weight_kg ?? null;
        const target = this.targetWeightKg;
        if (current === null || target === null) return '';
        return this.round1(current - target) > 0 ? 'up' : 'down';
    }

    public get hasWeightChart(): boolean {
        return this.weightChartPoints.length > 0 || this.weightRunBars.length > 0;
    }

    public get weightChartStartLabel(): string {
        const bounds = this.weightChartAxisBounds();
        return bounds ? this.displayDate(this.dateKey(bounds.start), false) : '';
    }

    public get weightChartEndLabel(): string {
        const bounds = this.weightChartAxisBounds();
        return bounds ? this.displayDate(this.dateKey(bounds.end), false) : '';
    }

    public get weightSaveButtonText(): string {
        return this.isWeightSaving ? '저장 중' : '저장';
    }

    public get weightTargetSaveButtonText(): string {
        return this.isWeightTargetSaving ? '저장 중' : '목표 저장';
    }

    public get weightInsightText(): string {
        if (!this.weightLogs.length) {
            return '체중 기록을 추가하면 러닝량과 함께 변화 흐름을 볼 수 있어.';
        }

        const monthKey = this.yearMonthKey(new Date());
        const monthRuns = this.runs.filter((run) => run.date.startsWith(monthKey));
        const monthDistance = this.round2(monthRuns.reduce((sum, run) => sum + run.distance_km, 0));
        const monthWeights = [...this.weightLogs]
            .filter((log) => log.date.startsWith(monthKey))
            .sort((a, b) => a.date.localeCompare(b.date));

        if (monthWeights.length >= 2) {
            const diff = this.round1(monthWeights[monthWeights.length - 1].weight_kg - monthWeights[0].weight_kg);
            const amount = Math.abs(diff).toFixed(1);
            const verb = diff < 0 ? '감량했어' : diff > 0 ? '증가했어' : '유지했어';
            return `이번달 ${this.distanceText(monthDistance)} 뛰면서 ${diff === 0 ? '' : amount + 'kg '}${verb}. 무리한 감량보다 회복 가능한 페이스를 우선하자.`;
        }

        if (monthDistance > 0) {
            return `이번달 ${this.distanceText(monthDistance)}를 뛰었어. 체중 기록을 한 번 더 남기면 러닝량과 변화량을 같이 볼 수 있어.`;
        }

        return '체중 변화는 러닝 거리, 식사, 수면을 함께 봐야 정확해. 급한 목표보다 꾸준한 기록을 우선하자.';
    }

    public get galleryCaptureCount(): number {
        return this.runs.filter((run) => Boolean(run.image_url)).length;
    }

    public get galleryMediaCount(): number {
        return this.runs.reduce((total, run) => total + (run.media?.length || 0), 0);
    }

    public get galleryJournalCount(): number {
        return this.buildJournalRuns().length;
    }

    public get gallerySummaryText(): string {
        if (this.galleryTab === 'journal') {
            return `${this.calendarTitle} ${this.activeMonthJournalCount}개 / 총 ${this.galleryJournalCount}개 일기`;
        }

        const total = this.galleryTab === 'media'
            ? this.galleryMediaCount
            : this.galleryCaptureCount;
        const unit = this.galleryTab === 'media' ? '개 첨부' : '개 캡처';
        if (total > this.galleryItems.length) {
            return `최근 ${this.galleryItems.length}개 / 총 ${total}${unit}`;
        }
        return `총 ${total}${unit}`;
    }

    public get galleryEmptyText(): string {
        if (this.galleryTab === 'journal') return '저장된 일기가 없어';
        return this.galleryTab === 'media' ? '첨부한 사진/영상이 없어' : '저장된 캡처가 없어';
    }

    public get galleryEmptyTitle(): string {
        if (this.galleryTab === 'journal') return '아직 저장된 일기가 없어';
        if (this.galleryTab === 'media') return '아직 첨부한 사진/영상이 없어';
        return '아직 저장된 캡처가 없어';
    }

    public get galleryEmptyDescription(): string {
        if (this.galleryTab === 'journal') return '러닝 일기를 남기면 여기에서 다시 볼 수 있어.';
        if (this.galleryTab === 'media') return '러닝 사진이나 영상을 추가하면 모아볼 수 있어.';
        return '러닝 기록 캡처를 업로드하면 갤러리에 쌓여.';
    }

    public get selectedJournalDateText(): string {
        return this.selectedJournalDate ? this.displayDate(this.selectedJournalDate, true) : '';
    }

    public get weatherLocationTags(): string[] {
        const selectedLocation = this.selectedCalendarWeather?.locationName || '';
        const text = String(selectedLocation || this.weatherLocationText || '').replace(/\s*(기준|근처)\s*$/, '').trim();
        if (!text) return [];

        const tags = text
            .split(/[·,/|]+/)
            .map((item) => item.trim())
            .filter(Boolean);
        return tags.length ? tags.slice(0, 3) : [text];
    }

    public get weatherLocationButtonText(): string {
        if (this.isWeatherLocationBusy) return '위치 확인 중';
        return this.weatherPosition ? '현재 위치 갱신' : '현재 위치로 보기';
    }

    public async useCurrentLocationWeather(): Promise<void> {
        if (this.isWeatherLocationBusy || this.isWeatherLoading) return;
        if (typeof navigator === 'undefined' || !navigator.geolocation) {
            this.showToast('이 기기에서는 위치 권한을 사용할 수 없어.', 'error');
            return;
        }

        this.isWeatherLocationBusy = true;
        this.weatherStatus = '';
        this.cdr.detectChanges();

        try {
            const position = await this.requestCurrentWeatherPosition();
            this.weatherPosition = position;
            this.storeWeatherPosition(position);
            await this.loadWeatherForActiveMonth();
            this.showToast('현재 위치 기준으로 날씨를 불러왔어.', 'success');
        } catch (error) {
            const message = error instanceof Error && error.message
                ? error.message
                : '위치 권한을 허용하면 현재 위치 기준 날씨를 볼 수 있어.';
            this.showToast(message, 'error');
        } finally {
            this.isWeatherLocationBusy = false;
            this.cdr.detectChanges();
        }
    }

    public get activeJournalStats(): StatCard[] {
        return this.activeJournalViewer ? this.buildRunStatCards(this.activeJournalViewer) : [];
    }

    public get activeChatTitle(): string {
        const session = this.chatSessions.find((item) => item.id === this.activeChatSessionId);
        if (this.isChatSending) return '답변 준비 중';
        if (session) return `${this.pacerPersonaText} 페이서`;
        if (this.shouldShowChatDayPrompt) return '새 하루 준비';
        return '새 대화';
    }

    public get aiUsageSummaryText(): string {
        const usage = this.aiUsage;
        if (!usage) {
            return `하루 ${DEFAULT_AI_CHAT_DAILY_LIMIT}회, 월 ${DEFAULT_AI_CHAT_MONTHLY_LIMIT}회까지 사용할 수 있어.`;
        }

        const daily = this.aiUsagePeriodText(usage.daily_remaining, usage.daily_limit, '일');
        const monthly = this.aiUsagePeriodText(usage.monthly_remaining, usage.monthly_limit, '월');
        if (this.isAiUsageExhausted) {
            return this.aiUsageLimitNotice(usage) || `${daily}, ${monthly} 한도 중 하나를 모두 사용했어.`;
        }
        return `${daily}, ${monthly} 남았어.`;
    }

    public get aiUsageBadgeText(): string {
        const usage = this.aiUsage;
        if (!usage) return '확인 중';
        const daily = usage.daily_remaining === null ? '일 무제한' : `일 ${usage.daily_remaining}`;
        const monthly = usage.monthly_remaining === null ? '월 무제한' : `월 ${usage.monthly_remaining}`;
        return `${daily} · ${monthly}`;
    }

    public get isAiUsageExhausted(): boolean {
        const usage = this.aiUsage;
        if (!usage) return false;
        return !usage.allowed
            || usage.reason === 'daily_limit'
            || usage.reason === 'monthly_limit'
            || usage.daily_remaining === 0
            || usage.monthly_remaining === 0;
    }

    public get isChatInputDisabled(): boolean {
        return this.isChatSending || this.isAiUsageExhausted;
    }

    public get chatInputPlaceholder(): string {
        if (!this.isAiUsageExhausted) return '페이서한테 물어봐...';
        const usage = this.aiUsage;
        if (usage?.reason === 'monthly_limit' || usage?.monthly_remaining === 0) {
            return '이번 달 페이서 AI 한도를 모두 사용했어';
        }
        return '오늘 페이서 AI 한도를 모두 사용했어';
    }

    public get shouldShowChatDayPrompt(): boolean {
        return Boolean(this.chatDayPromptSession && !this.activeChatSessionId);
    }

    public get chatDayPromptText(): string {
        const session = this.chatDayPromptSession;
        const label = session ? this.chatDayLabel(this.chatSessionDayKey(session)) : '이전';
        return `${label} 대화는 기록에 보관했어. 오늘 대화를 새로 시작할까?`;
    }

    public get chatHistoryGroups(): ChatHistoryGroup[] {
        const groups = new Map<string, ChatSession[]>();
        for (const session of this.chatSessions) {
            const label = this.chatDayLabel(this.chatSessionDayKey(session));
            groups.set(label, [...(groups.get(label) || []), session]);
        }

        return Array.from(groups.entries()).map(([label, sessions]) => ({ label, sessions }));
    }

    public get hasRuns(): boolean {
        return this.runs.length > 0;
    }

    public get hasRunTypeStats(): boolean {
        return this.runTypeStats.some((item) => item.count > 0);
    }

    public get hasEnoughAnalysisData(): boolean {
        return this.runs.length >= 2;
    }

    public get aiConnectionStatusText(): string {
        if (!this.aiConnection) {
            return '연결 상태 확인 중';
        }

        return this.aiConnection.configured ? `${this.aiConnection.provider} 연결됨` : 'AI 백엔드 설정 필요';
    }

    public get aiConnectionModelText(): string {
        return this.aiConnection?.model || '-';
    }

    public get aiConnectionSteps(): string[] {
        return this.aiConnection?.setup_steps || [];
    }

    public get aiSettingsStatusText(): string {
        if (!this.aiConnection) return '확인 중';
        return this.aiConnection.configured ? '연결됨' : '갱신 필요';
    }

    public get aiSettingsStatusDetail(): string {
        if (!this.aiConnection) return 'AI 연결 상태를 확인하고 있어.';
        return this.aiConnection.codex_status_message || this.aiConnection.message || this.aiConnectionStatusText;
    }

    public get aiLoginRefreshButtonText(): string {
        if (this.aiLoginRefreshPending) return '갱신 중';
        return this.aiConnection?.mode === 'codex' ? '로그인 갱신' : '상태 다시 확인';
    }

    public get aiLoginDeviceExpiryText(): string {
        if (!this.aiLoginDeviceExpiresIn) return '';
        return `${this.aiLoginDeviceExpiresIn}분 안에 인증`;
    }

    public get profileNameText(): string {
        return this.profile?.name || '프로필 설정';
    }

    public get profileMetaText(): string {
        if (!this.profile) return '이름과 사진을 설정';
        return this.profile.email || this.profile.mobile || '프로필 화면으로 이동';
    }

    public get profileAvatarText(): string {
        return this.avatarText(this.profile?.name);
    }

    public get homeProfileImage(): string {
        return this.profile?.profile_image || '';
    }

    public get homeAvatarText(): string {
        return this.avatarText(this.profile?.name || this.profile?.display_name || this.profile?.username || '나');
    }

    public get monthlyGoalSettingsText(): string {
        if (!this.goalProgressCards.length) return '미설정';
        const achievedCount = this.goalProgressCards.filter((goal) => goal.achieved).length;
        return `${this.goalProgressCards.length}개 설정 · ${achievedCount}개 달성`;
    }

    public get reminderSettingsText(): string {
        if (!this.appSettings.notificationsEnabled) return '꺼짐';
        const days = this.appSettings.reminderDays
            .map((id) => WEEKDAY_OPTIONS.find((option) => option.id === id)?.label)
            .filter(Boolean)
            .join('');
        return `${days || '요일 없음'} ${this.appSettings.reminderTime}`;
    }

    public get healthKitStatusText(): string {
        return this.appSettings.healthKitConnected ? '연결됨' : '미연동';
    }

    public get appleMusicStatusText(): string {
        if (this.appSettings.appleMusicConnected) return '연결됨';
        return this.appleMusicConnection.configured ? '미연동' : '서버 설정 필요';
    }

    public get appleMusicConnectButtonText(): string {
        if (this.isAppleMusicLoading) return '확인 중';
        return this.appSettings.appleMusicConnected ? '해제' : '연결';
    }

    public get appleMusicUploadHelpText(): string {
        if (!this.appleMusicConnection.configured) {
            return this.appleMusicConnection.message || 'Apple Music Developer Token 설정이 필요해.';
        }
        if (!this.appSettings.appleMusicConnected) {
            return 'Apple Music을 연결하면 최근 재생곡 30개에서 고를 수 있어.';
        }
        return this.selectedMusicTrackIds.length
            ? `${this.selectedMusicTrackIds.length}곡 선택됨`
            : '최근 재생곡을 불러와 그날 들은 곡을 골라줘.';
    }

    public get selectedMusicTracks(): MusicTrack[] {
        const selected = new Set(this.selectedMusicTrackIds);
        return this.appleMusicRecentTracks.filter((track) => selected.has(track.id));
    }

    public get unitSettingsText(): string {
        return this.appSettings.unit === 'mile' ? 'mile' : 'km';
    }

    public get distanceUnitLabel(): string {
        return this.appSettings.unit === 'mile' ? 'mile' : 'km';
    }

    public get paceMetricLabel(): string {
        return this.appSettings.paceDisplay === 'speed' ? '평균 속도' : '평균 페이스';
    }

    public get bestPaceMetricLabel(): string {
        return this.appSettings.paceDisplay === 'speed' ? '최고 속도' : '최고 페이스';
    }

    public get paceUnitLabel(): string {
        return this.appSettings.paceDisplay === 'speed'
            ? `${this.distanceUnitLabel}/h`
            : `/${this.distanceUnitLabel}`;
    }

    public get paceDisplaySettingsText(): string {
        return this.appSettings.paceDisplay === 'speed' ? '속도' : '페이스';
    }

    public get themeModeText(): string {
        return THEME_MODE_OPTIONS.find((option) => option.id === this.appSettings.themeMode)?.label || '다크';
    }

    public get shouldShowCycleFeature(): boolean {
        return this.profile?.gender !== 'male';
    }

    public get cycleFeatureStatusText(): string {
        return this.isCycleFeatureEnabled ? '켜짐' : '꺼짐';
    }

    public get appLockStatusText(): string {
        return this.appSettings.appLockEnabled ? '켜짐' : '꺼짐';
    }

    public get pacerPersonaText(): string {
        return PACER_PERSONA_OPTIONS.find((option) => option.id === this.appSettings.pacerPersona)?.label || '밸런스';
    }

    public get pacerPersonaDraftOption(): PacerPersonaOption {
        return PACER_PERSONA_OPTIONS.find((option) => option.id === this.pacerPersonaDraft) || PACER_PERSONA_OPTIONS[0];
    }

    public get pacerPersonaDraftExamples(): ChatMessage[] {
        return this.pacerPersonaDraftOption.examples;
    }

    public get pacerPersonaHasChanges(): boolean {
        return this.pacerPersonaDraft !== this.appSettings.pacerPersona;
    }

    public get pacerPersonaSaveText(): string {
        return this.pacerPersonaHasChanges ? '저장' : '저장됨';
    }

    public get accountDeleteReady(): boolean {
        return this.accountDeleteForm.confirm_text.trim() === '삭제';
    }

    public get passwordMinLengthOk(): boolean {
        return String(this.passwordForm.newPassword || '').length >= 8;
    }

    public get passwordCombinationOk(): boolean {
        const value = String(this.passwordForm.newPassword || '');
        return /[A-Za-z]/.test(value) && /\d/.test(value);
    }

    public get passwordMatchTouched(): boolean {
        return Boolean(this.passwordForm.confirmPassword);
    }

    public get passwordMatches(): boolean {
        return this.passwordMatchTouched && this.passwordForm.newPassword === this.passwordForm.confirmPassword;
    }

    public get passwordMatchText(): string {
        if (!this.passwordMatchTouched) return '새 비밀번호를 한 번 더 입력해줘.';
        return this.passwordMatches ? '새 비밀번호가 일치해.' : '새 비밀번호가 일치하지 않아.';
    }

    public get passwordCanSubmit(): boolean {
        return Boolean(this.passwordForm.currentPassword)
            && this.passwordMinLengthOk
            && this.passwordMatches
            && this.passwordForm.currentPassword !== this.passwordForm.newPassword;
    }

    public setScreen(screen: ScreenKey): void {
        this.activeScreen = screen;
        this.updateRouteScreen(screen);
        void this.loadActiveScreenData(true);
    }

    private async loadActiveScreenData(showLoading: boolean = true): Promise<void> {
        const screen = this.activeScreen;
        if (screen === 'feed' || screen === 'friends' || screen === 'ranking' || screen === 'profile') {
            await this.runDeferredDashboardTask(() => this.loadCommunityNotifications(false));
        }
        if (screen === 'achievements' && !this.badges.length) {
            await this.runDeferredDashboardTask(() => this.loadBadges());
        }
        if (screen === 'goals') {
            this.syncGoalDrafts();
        }
        if (screen === 'challenges') {
            await this.runDeferredDashboardTask(() => this.loadChallenges());
        }
        if (screen === 'feed') {
            await this.runDeferredDashboardTask(() => this.loadFeed(showLoading));
        }
        if (screen === 'friends') {
            await this.runDeferredDashboardTask(() => this.loadFriendLists(showLoading));
            await this.runDeferredDashboardTask(() => this.loadFriendCode());
        }
        if (screen === 'ranking') {
            await this.runDeferredDashboardTask(() => this.loadRanking());
        }
        if (screen === 'profile') {
            this.isProfileEditOpen = false;
            await this.runDeferredDashboardTask(() => this.loadFriendLists(false));
        }
        if (screen === 'calendar') {
            await this.runDeferredDashboardTask(() => this.loadDayNotes());
            await this.runDeferredDashboardTask(() => this.loadRestDays());
            await this.runDeferredDashboardTask(() => this.loadWeatherForActiveMonth());
        }
        if (screen === 'weight') {
            await this.runDeferredDashboardTask(() => this.loadWeights());
        }
        if (screen === 'chart') {
            await this.runDeferredDashboardTask(() => this.loadTrainingLoad());
        }
        if (screen === 'gallery' && !this.runMediaLoaded) {
            await this.runDeferredDashboardTask(() => this.loadRuns(false, false, true, this.runsUrl({ includeMedia: true }), true));
        }
        if (screen === 'chat' || screen === 'ai-settings') {
            if (!this.aiConnection) {
                await this.runDeferredDashboardTask(() => this.loadAiConnection());
            }
            if (!this.chatSessions.length) {
                await this.runDeferredDashboardTask(() => this.loadChatHistory(true));
            }
            if (!this.appleMusicConnection.configured) {
                await this.runDeferredDashboardTask(() => this.loadAppleMusicConnection());
            }
        }
    }

    private applyInitialScreenFromLocation(): void {
        if (typeof window === 'undefined') return;
        const screen = this.routeScreenMap[new URLSearchParams(window.location.search).get('screen') || ''];
        if (screen) this.activeScreen = screen;
    }

    private updateRouteScreen(screen: ScreenKey): void {
        if (typeof window === 'undefined') return;
        if (!Object.values(this.routeScreenMap).includes(screen)) return;
        const url = new URL(window.location.href);
        url.searchParams.set('screen', screen);
        window.history.replaceState({}, '', `${url.pathname}${url.search}${url.hash}`);
    }

    public openProfileSettings(): void {
        void this.openProfileEdit();
    }

    public async openProfileEdit(): Promise<void> {
        this.setScreen('profile');
        if (!this.profile) {
            await this.loadProfile();
        }
        this.profileEditDraft = this.profileEditDraftFromProfile(this.profile);
        this.profileEditStatus = '';
        this.isProfileEditOpen = true;
        this.cdr.detectChanges();
    }

    public closeProfileEdit(): void {
        if (this.isProfileSaving) return;
        this.isProfileEditOpen = false;
        this.profileEditStatus = '';
        this.cdr.detectChanges();
    }

    public openProfilePasswordPanel(): void {
        this.activeSettingsDetail = 'password';
        this.cdr.detectChanges();
    }

    public get profileEditPublicText(): string {
        return this.profileEditDraft.is_public ? '공개 프로필' : '비공개 프로필';
    }

    public toggleProfileEditPublic(event?: Event): void {
        event?.preventDefault();
        event?.stopPropagation();
        this.profileEditDraft = {
            ...this.profileEditDraft,
            is_public: !this.profileEditDraft.is_public
        };
        this.cdr.detectChanges();
    }

    public onProfileEditPhotoSelected(event: Event): void {
        const input = event.target instanceof HTMLInputElement ? event.target : null;
        const file = input?.files?.[0];
        if (!file) return;

        if (file.size > 2 * 1024 * 1024) {
            this.profileEditStatus = '프로필 사진은 2MB 이하로 선택해줘.';
            if (input) input.value = '';
            this.cdr.detectChanges();
            return;
        }

        const reader = new FileReader();
        reader.onload = () => {
            this.profileEditDraft = {
                ...this.profileEditDraft,
                profile_image: typeof reader.result === 'string' ? reader.result : ''
            };
            this.profileEditStatus = '';
            this.cdr.detectChanges();
        };
        reader.onerror = () => {
            this.profileEditStatus = '프로필 사진을 읽지 못했어.';
            this.cdr.detectChanges();
        };
        reader.readAsDataURL(file);
    }

    public clearProfileEditPhoto(): void {
        this.profileEditDraft = {
            ...this.profileEditDraft,
            profile_image: ''
        };
        this.cdr.detectChanges();
    }

    public async saveProfileEdit(): Promise<void> {
        if (this.isProfileSaving) return;

        const name = String(this.profileEditDraft.name || '').trim();
        const runningStartDate = this.normalizeDateKey(this.profileEditDraft.running_start_date);
        if (!name) {
            this.profileEditStatus = '이름을 입력해줘.';
            this.cdr.detectChanges();
            return;
        }
        if (!runningStartDate) {
            this.profileEditStatus = '러닝 시작일을 확인해줘.';
            this.cdr.detectChanges();
            return;
        }

        this.isProfileSaving = true;
        this.profileEditStatus = '프로필 저장 중';
        this.cdr.detectChanges();

        try {
            const result = await jsonRequest<any>('/api/profile', 'PATCH', {
                name,
                mobile: String(this.profileEditDraft.mobile || '').trim(),
                running_start_date: runningStartDate,
                profile_image: this.profileEditDraft.profile_image || '',
                is_public: this.profileEditDraft.is_public
            }, { retries: 0 });

            if (!result.success) {
                this.profileEditStatus = result.error?.message || '프로필을 저장하지 못했어.';
                this.showToast(this.profileEditStatus, 'error');
                return;
            }

            const source = (result.raw as any)?.data || result.data;
            const profile = this.normalizeProfile(source);
            this.profile = profile;
            this.profileEditDraft = this.profileEditDraftFromProfile(profile);
            this.syncPacerPersonaLocalForProfile();
            this.profileEditStatus = '';
            this.isProfileEditOpen = false;
            this.showToast('프로필을 저장했어.', 'success');
            void this.loadFriendLists(false);
        } finally {
            this.isProfileSaving = false;
            this.cdr.detectChanges();
        }
    }

    public openGoalSettings(event?: Event): void {
        event?.preventDefault();
        event?.stopPropagation();
        this.activeSettingsDetail = null;
        this.setScreen('goals');
        this.cdr.detectChanges();
    }

    public toggleSettingsDetail(detail: SettingsDetailKey): void {
        this.activeSettingsDetail = this.activeSettingsDetail === detail ? null : detail;
        this.cdr.detectChanges();
    }

    public async changePassword(): Promise<void> {
        if (this.changingPassword) return;

        const currentPassword = String(this.passwordForm.currentPassword || '');
        const newPassword = String(this.passwordForm.newPassword || '');
        const confirmPassword = String(this.passwordForm.confirmPassword || '');

        if (!currentPassword) {
            this.showToast('현재 비밀번호를 입력해줘.', 'error');
            return;
        }
        if (!newPassword) {
            this.showToast('새 비밀번호를 입력해줘.', 'error');
            return;
        }
        if (newPassword.length < 8) {
            this.showToast('새 비밀번호는 8자 이상이어야 해.', 'error');
            return;
        }
        if (currentPassword === newPassword) {
            this.showToast('새 비밀번호는 현재 비밀번호와 달라야 해.', 'error');
            return;
        }
        if (newPassword !== confirmPassword) {
            this.showToast('새 비밀번호가 일치하지 않아.', 'error');
            return;
        }

        this.changingPassword = true;
        this.cdr.detectChanges();

        try {
            const result = await jsonRequest('/api/auth/password', 'PATCH', {
                currentPassword,
                newPassword,
                invalidateOtherSessions: this.passwordForm.invalidateOtherSessions
            }, { retries: 0 });

            if (!result.success) {
                this.showToast(result.error?.message || '비밀번호 변경에 실패했어.', 'error');
                return;
            }

            this.passwordForm = {
                currentPassword: '',
                newPassword: '',
                confirmPassword: '',
                invalidateOtherSessions: true
            };
            this.activeSettingsDetail = null;
            this.showToast('비밀번호가 변경됐어', 'success');
        } catch {
            this.showToast('비밀번호 변경 중 오류가 발생했어.', 'error');
        } finally {
            this.changingPassword = false;
            this.cdr.detectChanges();
        }
    }

    public async toggleNotifications(): Promise<void> {
        const nextValue = !this.appSettings.notificationsEnabled;
        if (nextValue) {
            await this.requestNotificationPermission();
            if (this.notificationPermissionState === 'denied') {
                this.showToast('브라우저 알림 권한이 꺼져 있어.', 'error');
                this.appSettings.notificationsEnabled = false;
                this.persistAppSettings();
                this.cdr.detectChanges();
                return;
            }
        }

        this.appSettings.notificationsEnabled = nextValue;
        this.persistAppSettings();
        this.cdr.detectChanges();
    }

    public toggleReminderDay(day: WeekdayId): void {
        const days = new Set(this.appSettings.reminderDays);
        if (days.has(day)) {
            days.delete(day);
        } else {
            days.add(day);
        }
        this.appSettings.reminderDays = WEEKDAY_OPTIONS
            .map((option) => option.id)
            .filter((id) => days.has(id));
        this.persistAppSettings();
        this.cdr.detectChanges();
    }

    public updateReminderTime(value: string): void {
        if (!/^\d{2}:\d{2}$/.test(value)) return;
        this.appSettings.reminderTime = value;
        this.persistAppSettings();
        this.cdr.detectChanges();
    }

    public isReminderDaySelected(day: WeekdayId): boolean {
        return this.appSettings.reminderDays.includes(day);
    }

    public toggleRestRecommendationSetting(): void {
        this.appSettings.restRecommendationEnabled = !this.appSettings.restRecommendationEnabled;
        this.persistAppSettings();
        this.cdr.detectChanges();
    }

    public toggleHealthKitConnection(): void {
        this.appSettings.healthKitConnected = !this.appSettings.healthKitConnected;
        this.healthKitAcknowledged = this.appSettings.healthKitConnected;
        this.persistAppSettings();
        this.showToast(this.appSettings.healthKitConnected ? 'Apple Watch 연동 상태를 저장했어.' : 'Apple Watch 연동을 해제했어.', 'success');
        this.cdr.detectChanges();
    }

    public async toggleAppleMusicConnection(): Promise<void> {
        if (this.isAppleMusicLoading) return;
        if (this.appSettings.appleMusicConnected) {
            await this.disconnectAppleMusic();
            return;
        }

        await this.connectAppleMusic();
    }

    public setUnit(unit: DistanceUnit): void {
        if (!UNIT_OPTIONS.some((option) => option.id === unit)) return;
        if (this.appSettings.unit === unit) return;
        this.appSettings.unit = unit;
        this.refreshDerivedState();
        this.persistAppSettings();
        this.cdr.detectChanges();
    }

    public setPaceDisplay(mode: PaceDisplayMode): void {
        if (!PACE_DISPLAY_OPTIONS.some((option) => option.id === mode)) return;
        if (this.appSettings.paceDisplay === mode) return;
        this.appSettings.paceDisplay = mode;
        this.refreshDerivedState();
        this.persistAppSettings();
        this.cdr.detectChanges();
    }

    public setThemeMode(mode: ThemeMode): void {
        if (!THEME_MODE_OPTIONS.some((option) => option.id === mode)) return;
        this.appSettings.themeMode = mode;
        this.applyThemeMode();
        this.syncDashboardChrome();
        this.persistAppSettings();
        this.cdr.detectChanges();
    }

    public toggleAppLock(): void {
        this.appSettings.appLockEnabled = !this.appSettings.appLockEnabled;
        this.persistAppSettings();
        this.cdr.detectChanges();
    }

    public selectPacerPersona(persona: PacerPersona): void {
        const normalized = this.normalizePacerPersona(persona);
        if (!normalized) return;
        this.pacerPersonaDraft = normalized;
        this.cdr.detectChanges();
    }

    public savePacerPersona(): void {
        const persona = this.normalizePacerPersona(this.pacerPersonaDraft);
        if (!persona) return;
        this.appSettings.pacerPersona = persona;
        this.persistAppSettings();
        this.persistPacerPersonaLocal();
        this.showToast(`페이서 페르소나를 ${this.pacerPersonaText}(으)로 저장했어.`, 'success');
        this.cdr.detectChanges();
    }

    public setPacerPersona(persona: PacerPersona): void {
        this.selectPacerPersona(persona);
        this.savePacerPersona();
    }

    public exportData(format: SettingsExportFormat): void {
        if (format === 'csv') {
            this.downloadTextFile('runningmate-runs.csv', this.buildRunsCsv(), 'text/csv;charset=utf-8');
            return;
        }

        const payload = {
            exported_at: new Date().toISOString(),
            profile: this.profile,
            settings: this.appSettings,
            goals: this.goals,
            runs: this.runs,
            rest_days: this.restDays,
            weights: this.weightLogs,
            cycles: this.cycleLogs,
            day_notes: Array.from(this.calendarNotes.values())
        };
        this.downloadTextFile('runningmate-data.json', JSON.stringify(payload, null, 2), 'application/json;charset=utf-8');
    }

    public backupSettings(): void {
        const payload = {
            exported_at: new Date().toISOString(),
            version: this.appVersion,
            settings: this.appSettings,
            cycle: {
                enabled: this.isCycleFeatureEnabled,
                overlay: this.isCycleOverlayEnabled
            }
        };
        this.downloadTextFile('runningmate-settings-backup.json', JSON.stringify(payload, null, 2), 'application/json;charset=utf-8');
    }

    public restoreSettingsFromFile(input: HTMLInputElement): void {
        const file = input.files?.[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = () => {
            try {
                const parsed = JSON.parse(String(reader.result || '{}'));
                const settingsSource = parsed?.settings && typeof parsed.settings === 'object' ? parsed.settings : parsed;
                this.appSettings = this.normalizeAppSettings(settingsSource);

                const cycle = parsed?.cycle && typeof parsed.cycle === 'object' ? parsed.cycle : null;
                if (cycle) {
                    this.isCycleFeatureEnabled = Boolean(cycle.enabled);
                    this.isCycleOverlayEnabled = cycle.overlay === undefined ? this.isCycleOverlayEnabled : Boolean(cycle.overlay);
                    this.persistCycleLocalSettings();
                }

                this.applyThemeMode();
                this.persistAppSettings();
                this.showToast('설정 백업을 복원했어.', 'success');
            } catch {
                this.showToast('설정 백업 파일을 읽지 못했어.', 'error');
            } finally {
                input.value = '';
                this.cdr.detectChanges();
            }
        };
        reader.onerror = () => {
            input.value = '';
            this.showToast('설정 백업 파일을 읽지 못했어.', 'error');
            this.cdr.detectChanges();
        };
        reader.readAsText(file);
    }

    public openLegalPage(path: string): void {
        if (!path || !path.startsWith('/')) return;
        window.location.href = path;
    }

    public openFullDataDelete(): void {
        this.openLegalPage('/account/delete');
    }

    public openConfirmDialog(message: string, options: AppConfirmOptions = {}): Promise<boolean> {
        if (this.confirmDialogResolver) {
            this.resolveConfirmDialog(false);
        }

        const tone = options.tone || 'default';
        this.confirmDialog = {
            visible: true,
            title: options.title || '확인',
            message,
            confirmLabel: options.confirmLabel || '확인',
            cancelLabel: options.cancelLabel || '취소',
            tone,
            iconClass: options.iconClass || (tone === 'danger' ? 'fa-triangle-exclamation' : 'fa-circle-question')
        };
        this.cdr.detectChanges();

        return new Promise((resolve) => {
            this.confirmDialogResolver = resolve;
        });
    }

    public resolveConfirmDialog(confirmed: boolean): void {
        const resolver = this.confirmDialogResolver;
        this.confirmDialogResolver = null;
        this.confirmDialog = {
            ...this.confirmDialog,
            visible: false
        };
        this.cdr.detectChanges();
        if (resolver) resolver(confirmed);
    }

    public openAccountDelete(): void {
        if (this.deletingAccount) return;
        this.deleteStep = 1;
        this.accountDeleteForm = { confirm_text: '' };
        this.cdr.detectChanges();
    }

    public closeAccountDelete(): void {
        if (this.deletingAccount) return;
        this.deleteStep = 0;
        this.accountDeleteForm = { confirm_text: '' };
        this.cdr.detectChanges();
    }

    public continueAccountDelete(): void {
        if (this.deletingAccount) return;
        this.deleteStep = 2;
        this.cdr.detectChanges();
    }

    public async deleteAccount(): Promise<void> {
        if (this.deletingAccount) return;

        if (!this.accountDeleteReady) {
            this.showToast("'삭제'를 정확히 입력해줘.", 'error');
            return;
        }

        const confirmed = await this.openConfirmDialog(
            '계정과 모든 러닝 데이터를 삭제합니다. 이 작업은 되돌릴 수 없습니다. 최종 삭제할까요?',
            {
                title: '계정 삭제',
                confirmLabel: '최종 삭제',
                tone: 'danger',
                iconClass: 'fa-user-slash'
            }
        );
        if (!confirmed) return;

        this.deletingAccount = true;
        this.cdr.detectChanges();

        try {
            const result = await jsonRequest<any>('/api/auth/account', 'DELETE', {
                confirm_text: this.accountDeleteForm.confirm_text
            }, { retries: 0, timeoutMs: 30000 });

            if (!result.success) {
                this.showToast(result.error?.message || result.message || '계정 삭제에 실패했어.', 'error');
                return;
            }

            clearAuthTokens();
            this.deleteStep = 0;
            this.accountDeleted = true;
            this.accountDeleteForm = { confirm_text: '' };
            this.accountDeleteRedirectTimer = window.setTimeout(() => {
                window.location.href = '/access?account_deleted=1';
            }, 1200);
        } catch {
            this.showToast('계정 삭제 중 오류가 발생했어.', 'error');
        } finally {
            this.deletingAccount = false;
            this.cdr.detectChanges();
        }
    }

    public async logout(): Promise<void> {
        if (this.isLoggingOut) return;
        this.isLoggingOut = true;
        this.cdr.detectChanges();

        try {
            await apiFetch('/api/auth/logout', {
                method: 'POST',
                cache: 'no-store',
                credentials: 'include',
                retries: 0,
                timeoutMs: 5000
            });
        } catch {
            // Local auth state is cleared below even if the server request fails.
        }

        clearAuthTokens();
        window.location.replace('/access');
    }

    public async nextOnboardingStep(): Promise<void> {
        if (this.isOnboardingSaving) return;

        if (!this.validateOnboardingStep()) {
            this.cdr.detectChanges();
            return;
        }

        if (this.currentOnboardingStep.id === 'complete') {
            await this.finishOnboarding(false);
            return;
        }

        this.moveOnboardingTo(this.onboardingIndex + 1);
        this.cdr.detectChanges();
    }

    public previousOnboardingStep(): void {
        if (this.isOnboardingSaving) return;
        this.moveOnboardingTo(this.onboardingIndex - 1);
        this.cdr.detectChanges();
    }

    public skipOnboardingStep(): void {
        if (!this.canSkipOnboardingStep || this.isOnboardingSaving) return;
        this.isOnboardingSkipConfirmVisible = true;
        this.onboardingStatus = '';
        this.cdr.detectChanges();
    }

    public cancelOnboardingSkip(): void {
        if (this.isOnboardingSaving) return;
        this.isOnboardingSkipConfirmVisible = false;
        this.cdr.detectChanges();
    }

    public async confirmOnboardingSkip(): Promise<void> {
        if (this.isOnboardingSaving) return;
        this.isOnboardingSkipConfirmVisible = false;
        await this.finishOnboarding(true);
        this.cdr.detectChanges();
    }

    public selectOnboardingGoal(km: number): void {
        if (!Number.isFinite(km) || km <= 0) return;
        this.onboardingGoalKm = km;
        this.onboardingStatus = '';
        this.cdr.detectChanges();
    }

    public onboardingGoalDistanceText(km: number): string {
        return this.distanceText(km);
    }

    public async requestNotificationPermission(): Promise<void> {
        if (typeof window === 'undefined' || !('Notification' in window)) {
            this.notificationPermissionState = 'unsupported';
            this.cdr.detectChanges();
            return;
        }

        if (Notification.permission === 'granted' || Notification.permission === 'denied') {
            this.notificationPermissionState = Notification.permission;
            this.cdr.detectChanges();
            return;
        }

        try {
            this.notificationPermissionState = await Notification.requestPermission();
        } catch {
            this.notificationPermissionState = 'default';
        }
        this.cdr.detectChanges();
    }

    public startOnboardingSwipe(event: TouchEvent): void {
        this.onboardingTouchStartX = event.touches[0]?.clientX ?? null;
    }

    public endOnboardingSwipe(event: TouchEvent): void {
        if (this.onboardingTouchStartX === null) return;

        const endX = event.changedTouches[0]?.clientX ?? this.onboardingTouchStartX;
        const delta = endX - this.onboardingTouchStartX;
        this.onboardingTouchStartX = null;
        if (Math.abs(delta) < 56) return;

        if (delta < 0) {
            void this.nextOnboardingStep();
        } else {
            this.previousOnboardingStep();
        }
    }

    public onOnboardingPhotoSelected(event: Event): void {
        const input = event.target instanceof HTMLInputElement ? event.target : null;
        const file = input?.files?.[0];
        if (!file) return;

        if (file.size > 2 * 1024 * 1024) {
            this.onboardingStatus = '프로필 사진은 2MB 이하로 선택해줘.';
            if (input) input.value = '';
            this.cdr.detectChanges();
            return;
        }

        const reader = new FileReader();
        reader.onload = () => {
            this.onboardingProfile.profile_image = typeof reader.result === 'string' ? reader.result : '';
            this.onboardingStatus = '';
            this.cdr.detectChanges();
        };
        reader.onerror = () => {
            this.onboardingStatus = '프로필 사진을 읽지 못했어.';
            this.cdr.detectChanges();
        };
        reader.readAsDataURL(file);
    }

    public clearOnboardingPhoto(): void {
        this.onboardingProfile.profile_image = '';
        this.cdr.detectChanges();
    }

    public selectOnboardingGender(gender: string): void {
        this.onboardingProfile.gender = gender === 'unspecified' ? 'unspecified' : this.normalizeGender(gender);
        this.onboardingStatus = '';
        this.cdr.detectChanges();
    }

    public goalByType(goalType: GoalType): Goal | null {
        return this.goals.find((goal) => goal.goal_type === goalType) || null;
    }

    public goalProgressByType(goalType: GoalType): GoalProgress | null {
        return this.goalProgressCards.find((goal) => goal.goal_type === goalType) || null;
    }

    public goalOptionLabel(goalType: GoalType): string {
        return this.goalTypeLabel(goalType);
    }

    public goalOptionUnit(goalType: GoalType): string {
        return this.goalTypeUnit(goalType);
    }

    public goalPlaceholder(goalType: GoalType): string {
        if (goalType === 'distance') return this.appSettings.unit === 'mile' ? '예: 62' : '예: 100';
        if (goalType === 'pace') return this.appSettings.paceDisplay === 'speed' ? '예: 10.0' : '예: 5:30';
        return GOAL_TYPE_OPTIONS.find((option) => option.id === goalType)?.hint || '';
    }

    public goalActionText(goalType: GoalType): string {
        if (this.isGoalSaving) return '저장 중';
        return this.goalByType(goalType) ? '수정' : '추가';
    }

    public goalStatusText(goalType: GoalType): string {
        const progress = this.goalProgressByType(goalType);
        if (!progress) return '미설정';
        return progress.achieved ? '달성' : `${progress.percent}%`;
    }

    public async saveGoal(goalType: GoalType): Promise<void> {
        if (this.isGoalSaving) return;

        const targetValue = this.goalTargetFromInput(goalType, this.goalDrafts[goalType]);
        if (targetValue === null) {
            this.goalStatus = goalType === 'pace'
                ? `${this.paceDisplaySettingsText}는 ${this.appSettings.paceDisplay === 'speed' ? '10.0' : '5:30'}처럼 입력해줘.`
                : '목표값을 0보다 크게 입력해줘.';
            this.cdr.detectChanges();
            return;
        }

        this.isGoalSaving = true;
        this.goalStatus = '목표 저장 중';
        this.cdr.detectChanges();

        try {
            const response = await fetch(`/api/goals/${encodeURIComponent(this.activeYearMonth)}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ goal_type: goalType, target_value: targetValue })
            });
            const payload = await response.json().catch(() => null);
            if (!payload?.success) {
                this.goalStatus = payload?.message || '목표를 저장하지 못했어.';
                return;
            }

            this.applyGoalsPayload(payload);
            this.goalStatus = '목표 저장됨';
            this.showToast('목표를 저장했어.', 'success');
        } catch {
            this.goalStatus = '목표 저장 중 오류가 발생했어.';
        } finally {
            this.isGoalSaving = false;
            this.cdr.detectChanges();
        }
    }

    public async deleteGoal(goalType: GoalType): Promise<void> {
        if (this.deletingGoalType || !this.goalByType(goalType)) return;
        if (!(await this.openConfirmDialog(`${this.goalTypeLabel(goalType)} 목표를 삭제할까요?`, {
            title: '목표 삭제',
            confirmLabel: '삭제',
            tone: 'danger',
            iconClass: 'fa-trash-can'
        }))) return;

        this.deletingGoalType = goalType;
        this.goalStatus = '목표 삭제 중';
        this.cdr.detectChanges();

        try {
            const response = await fetch(`/api/goals/${encodeURIComponent(this.activeYearMonth)}?goal_type=${encodeURIComponent(goalType)}`, {
                method: 'DELETE'
            });
            const payload = await response.json().catch(() => null);
            if (!payload?.success) {
                this.goalStatus = payload?.message || '목표를 삭제하지 못했어.';
                return;
            }

            this.applyGoalsPayload(payload);
            this.goalStatus = '목표 삭제됨';
            this.showToast('목표를 삭제했어.', 'success');
        } catch {
            this.goalStatus = '목표 삭제 중 오류가 발생했어.';
        } finally {
            this.deletingGoalType = null;
            this.cdr.detectChanges();
        }
    }

    public setChallengeTab(tab: ChallengeListTab): void {
        this.activeChallengeTab = tab;
        this.challengeViewMode = 'list';
        this.challengeStatus = '';
        const first = this.activeChallengeList[0];
        this.selectedChallengeId = first?.id || null;
        this.cdr.detectChanges();
    }

    public selectChallenge(challenge: Challenge): void {
        this.selectedChallengeId = challenge.id;
        this.challengeViewMode = 'detail';
        this.challengeStatus = '';
        this.cdr.detectChanges();
    }

    public openChallengeCreate(): void {
        this.challengeViewMode = 'create';
        this.challengeStatus = '';
        this.cdr.detectChanges();
    }

    public backToChallengeList(): void {
        this.challengeViewMode = 'list';
        this.challengeStatus = '';
        this.cdr.detectChanges();
    }

    public challengeStatusClass(challenge: Challenge): string {
        if (challenge.status === 'ended') return 'ended';
        if (challenge.viewer_joined) return 'active';
        return 'recruiting';
    }

    public async saveChallenge(): Promise<void> {
        if (this.isChallengeSaving) return;

        const title = this.challengeForm.title.trim();
        const rawGoalValue = this.toNumber(this.challengeForm.goal_value);
        const goalValue = rawGoalValue === null
            ? null
            : this.challengeForm.type === 'count'
                ? rawGoalValue
                : this.displayDistanceToKm(rawGoalValue);
        if (!title) {
            this.challengeStatus = '제목을 입력해줘.';
            this.cdr.detectChanges();
            return;
        }
        if (goalValue === null || goalValue <= 0) {
            this.challengeStatus = '목표값을 0보다 크게 입력해줘.';
            this.cdr.detectChanges();
            return;
        }
        if (!this.normalizeDateKey(this.challengeForm.start_date) || !this.normalizeDateKey(this.challengeForm.end_date)) {
            this.challengeStatus = '기간을 확인해줘.';
            this.cdr.detectChanges();
            return;
        }
        if (this.challengeForm.end_date < this.challengeForm.start_date) {
            this.challengeStatus = '종료일은 시작일 이후로 설정해줘.';
            this.cdr.detectChanges();
            return;
        }

        this.isChallengeSaving = true;
        this.challengeStatus = '챌린지 생성 중';
        this.cdr.detectChanges();

        try {
            const response = await fetch('/api/challenges', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title,
                    type: this.challengeForm.type,
                    goal_value: this.challengeForm.type === 'count' ? Math.round(goalValue) : goalValue,
                    start_date: this.challengeForm.start_date,
                    end_date: this.challengeForm.end_date
                })
            });
            const payload = await response.json().catch(() => null);
            if (!payload?.success) {
                this.challengeStatus = payload?.message || '챌린지를 만들지 못했어.';
                return;
            }

            this.applyChallengesPayload(payload);
            const created = this.normalizeChallenge(payload.data);
            if (created) {
                this.selectedChallengeId = created.id;
                this.activeChallengeTab = 'owned';
                this.challengeViewMode = 'detail';
            }
            this.resetChallengeForm();
            this.challengeStatus = '';
            this.showToast('챌린지를 만들었어.', 'success');
        } catch {
            this.challengeStatus = '챌린지 생성 중 오류가 발생했어.';
        } finally {
            this.isChallengeSaving = false;
            this.cdr.detectChanges();
        }
    }

    public async joinChallengeByCode(): Promise<void> {
        await this.joinChallenge({ invite_code: this.challengeInviteCode.trim() });
    }

    public async joinRecruitingChallenge(challenge: Challenge, event?: Event): Promise<void> {
        event?.stopPropagation();
        await this.joinChallenge({ challenge_id: challenge.id });
    }

    public async deleteChallenge(challenge: Challenge, event?: Event): Promise<void> {
        event?.stopPropagation();
        if (this.deletingChallengeId || !challenge.viewer_owned) return;
        if (!(await this.openConfirmDialog('이 챌린지를 삭제할까요?', {
            title: '챌린지 삭제',
            confirmLabel: '삭제',
            tone: 'danger',
            iconClass: 'fa-flag'
        }))) return;

        this.deletingChallengeId = challenge.id;
        this.challengeStatus = '챌린지 삭제 중';
        this.cdr.detectChanges();

        try {
            const response = await fetch(`/api/challenges/${encodeURIComponent(challenge.id)}`, {
                method: 'DELETE'
            });
            const result = await response.json().catch(() => null);
            if (!result?.success) {
                this.challengeStatus = result?.message || '챌린지를 삭제하지 못했어.';
                return;
            }

            this.applyChallengesPayload(result);
            if (this.selectedChallengeId === challenge.id) {
                this.selectedChallengeId = this.activeChallengeList[0]?.id || null;
                this.challengeViewMode = 'list';
            }
            this.challengeStatus = '';
            this.showToast('챌린지를 삭제했어.', 'success');
        } catch {
            this.challengeStatus = '챌린지 삭제 중 오류가 발생했어.';
        } finally {
            this.deletingChallengeId = null;
            this.cdr.detectChanges();
        }
    }

    public setFriendTab(tab: FriendTab): void {
        this.activeFriendTab = tab;
        if (!this.activeFriendList.length) {
            void this.loadFriendLists();
        } else if (this.selectedFriendProfile && !this.activeFriendList.some((profile) => profile.id === this.selectedFriendProfile?.id)) {
            this.selectedFriendProfile = null;
        }
        this.cdr.detectChanges();
    }

    public openProfileSocialPanel(tab: FriendTab): void {
        this.profileSocialPanelTab = tab;
        this.activeFriendTab = tab;
        if (!this.activeProfileSocialList.length) {
            void this.loadFriendLists();
        }
        this.cdr.detectChanges();
    }

    public setProfileSocialPanelTab(tab: FriendTab): void {
        this.profileSocialPanelTab = tab;
        this.activeFriendTab = tab;
        if (!this.activeProfileSocialList.length) {
            void this.loadFriendLists();
        }
        this.cdr.detectChanges();
    }

    public closeProfileSocialPanel(): void {
        this.profileSocialPanelTab = null;
        this.cdr.detectChanges();
    }

    public openViewedProfile(profile: SocialProfile, event?: Event): void {
        event?.preventDefault();
        event?.stopPropagation();
        if (!profile?.id) return;
        if (profile.is_me) {
            this.viewedProfile = null;
            this.viewedProfileListTab = null;
            this.profileSocialPanelTab = null;
            this.cdr.detectChanges();
            return;
        }

        this.viewedProfile = profile;
        this.viewedProfileStatus = '프로필 불러오는 중';
        this.viewedProfileListTab = null;
        this.cdr.detectChanges();
        void this.loadViewedProfile(profile.id);
    }

    public closeViewedProfile(): void {
        this.viewedProfile = null;
        this.viewedProfileFollowingUsers = [];
        this.viewedProfileFollowerUsers = [];
        this.viewedProfileMediaItems = [];
        this.viewedProfileListsPublic = true;
        this.viewedProfileListTab = null;
        this.viewedProfileStatus = '';
        this.isViewedProfileLoading = false;
        this.cdr.detectChanges();
    }

    public openViewedProfileList(tab: FriendTab): void {
        this.viewedProfileListTab = tab;
        this.cdr.detectChanges();
    }

    public setViewedProfileListTab(tab: FriendTab): void {
        this.viewedProfileListTab = tab;
        this.cdr.detectChanges();
    }

    public closeViewedProfileList(): void {
        this.viewedProfileListTab = null;
        this.cdr.detectChanges();
    }

    public openRankingProfile(entry: RankingEntry, event?: Event): void {
        event?.preventDefault();
        event?.stopPropagation();
        if (!entry?.user_id) return;

        if (entry.is_viewer) {
            this.closeViewedProfile();
            this.setScreen('profile');
            return;
        }

        this.openViewedProfile(this.rankingEntryToSocialProfile(entry));
    }

    public rankingEntryProfileLabel(entry: RankingEntry): string {
        const name = entry?.name || '러너';
        return entry?.is_viewer ? '내 프로필 보기' : `${name} 프로필 보기`;
    }

    public selectFriendProfile(profile: SocialProfile): void {
        this.selectedFriendProfile = profile;
        this.friendStatus = '';
        this.cdr.detectChanges();
    }

    public async searchFriends(): Promise<void> {
        const query = this.friendSearchQuery.trim();
        if (!query) {
            this.friendSearchResults = [];
            this.friendStatus = '아이디나 이름을 입력해줘.';
            this.cdr.detectChanges();
            return;
        }

        this.isFriendSearchLoading = true;
        this.friendStatus = '친구 찾는 중';
        this.cdr.detectChanges();

        try {
            const response = await fetch(`/api/users/search?q=${encodeURIComponent(query)}`, {
                cache: 'no-store'
            });
            const payload = await response.json().catch(() => null);
            if (!response.ok || !payload?.success) {
                this.friendStatus = payload?.message || '친구 검색에 실패했어.';
                return;
            }

            this.friendSearchResults = this.normalizeSocialProfiles(payload.data);
            this.friendStatus = this.friendSearchResults.length ? '검색 완료' : '검색 결과가 없어.';
        } catch {
            this.friendStatus = '친구 검색 중 오류가 발생했어.';
        } finally {
            this.isFriendSearchLoading = false;
            this.cdr.detectChanges();
        }
    }

    public clearFriendSearch(): void {
        this.friendSearchQuery = '';
        this.friendSearchResults = [];
        this.friendStatus = '';
        this.cdr.detectChanges();
    }

    public async loadFriendCode(force: boolean = false): Promise<void> {
        if (this.friendCode && !force) return;
        if (this.isFriendCodeLoading) return;

        this.isFriendCodeLoading = true;
        this.cdr.detectChanges();

        try {
            const result = await apiFetch<any>('/api/friends/code');
            if (!result.success) {
                this.friendCodeStatus = result.error?.message || '친구코드를 불러오지 못했어.';
                return;
            }

            const payload = (result.data || result.raw || {}) as any;
            const data = payload.data || payload;
            this.friendCode = typeof data?.code === 'string' ? data.code : '';
            this.friendCodeStatus = this.friendCode ? '' : '친구코드를 불러오지 못했어.';
        } catch {
            this.friendCodeStatus = '친구코드 확인 중 오류가 발생했어.';
        } finally {
            this.isFriendCodeLoading = false;
            this.cdr.detectChanges();
        }
    }

    public async copyFriendCode(): Promise<void> {
        if (!this.friendCode) {
            await this.loadFriendCode(true);
        }
        if (!this.friendCode) return;

        try {
            await navigator.clipboard?.writeText(this.friendCodeShareText || this.friendCode);
            this.friendCodeStatus = '친구코드를 복사했어.';
            this.showToast('친구코드를 복사했어.', 'success');
        } catch {
            this.friendCodeStatus = this.friendCode;
            this.showToast('친구코드를 화면에서 확인해줘.', 'info');
        } finally {
            this.cdr.detectChanges();
        }
    }

    public async shareFriendCode(): Promise<void> {
        if (!this.friendCode) {
            await this.loadFriendCode(true);
        }
        if (!this.friendCode) return;

        const text = this.friendCodeShareText || this.friendCode;
        try {
            if (navigator.share) {
                await navigator.share({ title: '러닝메이트 친구코드', text });
                return;
            }
        } catch {
            // Fall back to clipboard when native share is cancelled or unavailable.
        }
        await this.copyFriendCode();
    }

    public async addFriendByCode(): Promise<void> {
        const code = this.friendCodeInput.trim();
        if (!code) {
            this.friendCodeStatus = '친구코드를 입력해줘.';
            this.cdr.detectChanges();
            return;
        }

        this.isFriendCodeAdding = true;
        this.friendCodeStatus = '런메이트 추가 중';
        this.cdr.detectChanges();

        try {
            const result = await jsonRequest<any>('/api/friends/code', 'POST', { code }, { retries: 0 });
            if (!result.success) {
                this.friendCodeStatus = result.error?.message || '친구코드를 확인하지 못했어.';
                return;
            }

            const payload = (result.data || result.raw || {}) as any;
            const updated = this.normalizeSocialProfile(payload.data || payload);
            if (updated) {
                this.applySocialProfileUpdate(updated);
                this.selectedFriendProfile = updated;
            }
            this.friendCodeInput = '';
            await this.loadFriendLists(false);
            this.friendCodeStatus = '런메이트를 추가했어.';
            this.showToast('런메이트를 추가했어.', 'success');
            void this.loadRanking();
            void this.loadCommunityNotifications(false);
        } catch {
            this.friendCodeStatus = '친구코드 추가 중 오류가 발생했어.';
        } finally {
            this.isFriendCodeAdding = false;
            this.cdr.detectChanges();
        }
    }

    public async toggleFollow(profile: SocialProfile, event?: Event): Promise<void> {
        event?.stopPropagation();
        if (!profile?.id || profile.is_me || this.followBusyUserId) return;

        const nextFollowing = !profile.is_following;
        this.followBusyUserId = profile.id;
        this.friendStatus = nextFollowing ? '팔로우 중' : '언팔로우 중';
        this.cdr.detectChanges();

        try {
            const response = await fetch(`/api/follows/${encodeURIComponent(profile.id)}`, {
                method: nextFollowing ? 'POST' : 'DELETE'
            });
            const payload = await response.json().catch(() => null);
            if (!response.ok || !payload?.success) {
                this.friendStatus = payload?.message || '팔로우 상태를 바꾸지 못했어.';
                return;
            }

            const updated = this.normalizeSocialProfile(payload.data);
            if (updated) {
                this.applySocialProfileUpdate(updated);
            }
            const shouldRefreshViewedProfile = this.viewedProfile?.id === profile.id;
            await this.loadFriendLists(false);
            if (shouldRefreshViewedProfile) {
                await this.loadViewedProfile(profile.id);
            }
            this.friendStatus = '';
            if (nextFollowing) {
                void this.loadCommunityNotifications(false);
            }
        } catch {
            this.friendStatus = '팔로우 처리 중 오류가 발생했어.';
        } finally {
            this.followBusyUserId = null;
            this.cdr.detectChanges();
        }
    }

    public followButtonText(profile: SocialProfile): string {
        if (this.followBusyUserId === profile.id) return '처리 중';
        return profile.is_following ? '언팔로우' : '팔로우';
    }

    public friendFeedCount(profile: SocialProfile): number {
        return Math.max(0, Math.round(profile.stats?.run_count || 0));
    }

    public refreshFeed(): void {
        void this.loadFeed();
    }

    public feedMediaItems(run: FeedRun): RunMedia[] {
        return Array.isArray(run.media) ? run.media : [];
    }

    public communityNotificationIcon(item: CommunityNotification): string {
        if (item.type === 'follow') return 'fa-user-plus';
        if (item.type === 'comment') return 'fa-comment';
        return 'fa-heart';
    }

    public communityNotificationTimeText(item: CommunityNotification): string {
        return this.feedTimeText(item.created_at);
    }

    public async markCommunityNotificationsRead(): Promise<void> {
        if (!this.communityNotifications.length) return;
        try {
            const result = await jsonRequest<any[]>('/api/notifications', 'PATCH', {});
            if (result.success) {
                const rows = Array.isArray(result.data) ? result.data : [];
                this.communityNotifications = this.normalizeCommunityNotifications(rows);
            }
        } finally {
            this.cdr.detectChanges();
        }
    }

    public toggleReactionUsers(runId: string): void {
        this.expandedReactionRunId = this.expandedReactionRunId === runId ? null : runId;
        this.cdr.detectChanges();
    }

    public toggleFeedComments(runId: string): void {
        this.expandedCommentsRunId = this.expandedCommentsRunId === runId ? null : runId;
        this.cdr.detectChanges();
    }

    public visibleFeedComments(run: FeedRun): FeedComment[] {
        if (this.expandedCommentsRunId === run.id) return run.comments;
        return run.comments.slice(-2);
    }

    public feedReactionUsers(run: FeedRun): FeedReactionUser[] {
        return run.reaction_summary.flatMap((item) => item.users);
    }

    public feedCommentDraft(run: FeedRun): string {
        return this.feedCommentDrafts[run.id] || '';
    }

    public get activeProfileFeedLike(): FeedReactionSummary {
        return this.profileFeedLikeSummary(this.activeProfileFeedRun);
    }

    public profileFeedLikeSummary(run: FeedRun | null): FeedReactionSummary {
        const fallback = FEED_REACTION_SUMMARY[0];
        return run?.reaction_summary.find((item) => item.type === 'like') || { ...fallback, users: [] };
    }

    public openProfileFeedViewer(item: GalleryItem): void {
        if (!item?.media) return;

        const run = this.profileFeedRunFromItem(item);
        if (!run) {
            this.openMediaViewer(item.media);
            return;
        }

        this.activeProfileFeedItem = item;
        this.activeProfileFeedMedia = item.media;
        this.activeProfileFeedRun = run;
        this.expandedCommentsRunId = run.id;
        this.profileFeedSocialStatus = '';
        this.cdr.detectChanges();
        void this.loadProfileFeedSocial(run.id);
    }

    public closeProfileFeedViewer(): void {
        this.activeProfileFeedItem = null;
        this.activeProfileFeedMedia = null;
        this.activeProfileFeedRun = null;
        this.profileFeedSocialStatus = '';
        this.isProfileFeedSocialLoading = false;
        this.cdr.detectChanges();
    }

    public async toggleFeedReaction(run: FeedRun, reactionType: ReactionType): Promise<void> {
        if (!run?.id) return;
        const key = `${run.id}:${reactionType}`;
        if (this.feedBusyKey) return;

        const current = run.reaction_summary.find((item) => item.type === reactionType);
        const method = current?.reacted ? 'DELETE' : 'POST';
        this.feedBusyKey = key;
        this.cdr.detectChanges();

        try {
            const result = await jsonRequest<any>(`/api/runs/${encodeURIComponent(run.id)}/reactions`, method, { type: reactionType });
            if (!result.success) {
                this.showToast(result.error?.message || '반응을 저장하지 못했어.', 'error');
                return;
            }
            this.applyFeedSocial(run.id, (result.raw as any)?.social || result.data);
        } finally {
            this.feedBusyKey = '';
            this.cdr.detectChanges();
        }
    }

    public async submitFeedComment(run: FeedRun): Promise<void> {
        if (!run?.id || this.feedBusyKey) return;
        const content = this.feedCommentDraft(run).trim();
        if (!content) return;

        this.feedBusyKey = `${run.id}:comment`;
        this.cdr.detectChanges();

        try {
            const result = await jsonRequest<any>(`/api/runs/${encodeURIComponent(run.id)}/comments`, 'POST', { content });
            if (!result.success) {
                this.showToast(result.error?.message || '댓글을 저장하지 못했어.', 'error');
                return;
            }
            this.feedCommentDrafts = { ...this.feedCommentDrafts, [run.id]: '' };
            this.expandedCommentsRunId = run.id;
            this.applyFeedSocial(run.id, (result.raw as any)?.social || result.data);
        } finally {
            this.feedBusyKey = '';
            this.cdr.detectChanges();
        }
    }

    public async deleteFeedComment(run: FeedRun, comment: FeedComment, event?: Event): Promise<void> {
        event?.preventDefault();
        event?.stopPropagation();
        if (!run?.id || !comment?.id || !comment.is_mine || this.deletingFeedCommentId) return;
        if (!(await this.openConfirmDialog('댓글을 삭제할까요?', {
            title: '댓글 삭제',
            confirmLabel: '삭제',
            tone: 'danger',
            iconClass: 'fa-comment-slash'
        }))) return;

        this.deletingFeedCommentId = comment.id;
        this.cdr.detectChanges();

        try {
            const result = await jsonRequest<any>(`/api/runs/${encodeURIComponent(run.id)}/comments`, 'DELETE', { comment_id: comment.id });
            if (!result.success) {
                this.showToast(result.error?.message || '댓글을 삭제하지 못했어.', 'error');
                return;
            }
            this.applyFeedSocial(run.id, (result.raw as any)?.social || result.data);
        } finally {
            this.deletingFeedCommentId = null;
            this.cdr.detectChanges();
        }
    }

    public isFeedReactionBusy(run: FeedRun, reactionType: ReactionType): boolean {
        return this.feedBusyKey === `${run.id}:${reactionType}`;
    }

    public isFeedCommentBusy(run: FeedRun): boolean {
        return this.feedBusyKey === `${run.id}:comment`;
    }

    public feedTimeText(value?: string | null): string {
        if (!value) return '';
        const date = this.parseDateTime(value) || this.parseDate(String(value).slice(0, 10));
        if (!date) return '';
        return `${this.displayDate(String(value).slice(0, 10), false)} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
    }

    public feedRouteAltText(run: FeedRun): string {
        return `${run.user.name}의 ${this.displayDate(run.date, false)} 러닝 루트`;
    }

    public runPrivacyText(run: CalendarRunDetail | RunRecord): string {
        return run.is_public === false ? '비공개' : '공개';
    }

    public runMediaPrivacyText(run: CalendarRunDetail | RunRecord): string {
        return run.is_public === false ? '피드 비공개' : '피드 공개';
    }

    public toggleCalendarUploadPrivacy(event?: Event): void {
        event?.preventDefault();
        event?.stopPropagation();
        this.calendarUploadIsPublic = !this.calendarUploadIsPublic;
        this.cdr.detectChanges();
    }

    public async toggleRunPrivacy(run: CalendarRunDetail | RunRecord, event?: Event): Promise<void> {
        event?.preventDefault();
        event?.stopPropagation();
        if (!run?.id || this.privacyBusyRunId) return;

        const nextPublic = run.is_public === false;
        this.privacyBusyRunId = run.id;
        this.cdr.detectChanges();

        try {
            const result = await jsonRequest<any>(`/api/runs/${encodeURIComponent(run.id)}`, 'PATCH', { is_public: nextPublic });
            if (!result.success) {
                this.showToast(result.error?.message || '공개 설정을 저장하지 못했어.', 'error');
                return;
            }
            this.applyRunUpdate((result.raw as any)?.data || result.data);
            this.showToast(nextPublic ? '기록을 공개로 바꿨어.' : '기록을 비공개로 바꿨어.', 'success');
            void this.loadFeed(false);
        } finally {
            this.privacyBusyRunId = null;
            this.cdr.detectChanges();
        }
    }

    public setRankingPeriod(period: RankingPeriod): void {
        if (this.activeRankingPeriod === period) return;
        this.activeRankingPeriod = period;
        void this.loadRanking();
        this.cdr.detectChanges();
    }

    public setRankingScope(scope: RankingScope): void {
        if (this.activeRankingScope === scope) return;
        this.activeRankingScope = scope;
        void this.loadRanking();
        this.cdr.detectChanges();
    }

    public async toggleRankingParticipation(): Promise<void> {
        if (this.isRankingSaving) return;

        const nextEnabled = !this.rankingParticipationEnabled;
        this.isRankingSaving = true;
        this.rankingStatus = '참여 설정 저장 중';
        this.cdr.detectChanges();

        try {
            const response = await fetch(`/api/ranking/weekly?period=${encodeURIComponent(this.activeRankingPeriod)}&scope=${encodeURIComponent(this.activeRankingScope)}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ranking_enabled: nextEnabled })
            });
            const payload = await response.json().catch(() => null);
            if (!response.ok || !payload?.success) {
                this.rankingStatus = payload?.message || '참여 설정을 저장하지 못했어.';
                return;
            }

            this.rankingParticipationEnabled = nextEnabled;
            this.applyRankingPayload(payload.ranking || payload.data || payload);
            this.rankingStatus = nextEnabled ? '랭킹 참여 중' : '랭킹에서 숨김';
            this.showToast(nextEnabled ? '랭킹 참여를 켰어.' : '랭킹 참여를 껐어.', 'success');
        } catch {
            this.rankingStatus = '참여 설정 저장 중 오류가 발생했어.';
        } finally {
            this.isRankingSaving = false;
            this.cdr.detectChanges();
        }
    }

    public openBadgeDetail(badge: Badge): void {
        this.selectedBadge = badge;
        this.cdr.detectChanges();
    }

    public closeBadgeDetail(): void {
        this.selectedBadge = null;
        this.cdr.detectChanges();
    }

    public closeBadgeCelebration(): void {
        this.newlyEarnedBadges = [];
        this.cdr.detectChanges();
    }

    public openAiSettings(): void {
        this.activeScreen = 'ai-settings';
        this.loadPacerPersonaLocal();
        this.aiLoginRefreshStatus = '';
        this.cdr.detectChanges();
    }

    public openChatHistory(): void {
        this.isChatHistoryOpen = true;
        void this.loadChatHistory();
    }

    public closeChatHistory(): void {
        this.isChatHistoryOpen = false;
        this.cdr.detectChanges();
    }

    public startNewChat(): void {
        this.activeChatSessionId = null;
        this.chatDayPromptSession = null;
        this.chatText = '';
        this.chatMessages = this.buildChatMessages();
        this.isChatHistoryOpen = false;
        this.cdr.detectChanges();
        this.scrollChatToBottom();
    }

    public selectChatSession(session: ChatSession): void {
        if (!session?.id) return;

        this.activeChatSessionId = session.id;
        this.chatDayPromptSession = null;
        this.chatMessages = session.messages.map((message) => ({
            sender: message.sender,
            text: message.text,
            created_at: message.created_at,
            streaming: false
        }));
        this.isChatHistoryOpen = false;
        this.cdr.detectChanges();
        this.scrollChatToBottom();
    }

    public async deleteChatSession(session: ChatSession, event?: Event): Promise<void> {
        event?.preventDefault();
        event?.stopPropagation();
        if (!session?.id || this.deletingChatSessionId) return;

        const title = session.title || '이 대화';
        if (!(await this.openConfirmDialog(`"${title}" 대화를 삭제할까요?`, {
            title: '대화 삭제',
            confirmLabel: '삭제',
            tone: 'danger',
            iconClass: 'fa-message'
        }))) return;

        this.deletingChatSessionId = session.id;
        this.cdr.detectChanges();

        try {
            const response = await fetch('/api/chat', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    ...authHeaderForUrl('/api/chat')
                },
                body: JSON.stringify({ id: session.id })
            });
            const rawPayload = await response.json().catch(() => null);
            const payload = this.normalizeWizStatusPayload(rawPayload) as { success?: boolean; message?: string; data?: unknown[]; usage?: Partial<AiUsage> } | null;
            this.applyAiUsage(payload?.usage);
            if (!payload?.success) {
                this.showToast(payload?.message || '대화를 삭제하지 못했어.', 'error');
                return;
            }

            const rows = Array.isArray(payload.data) ? payload.data : null;
            this.chatSessions = rows
                ? rows
                    .map((row: unknown) => this.normalizeChatSession(row))
                    .filter((row: ChatSession | null): row is ChatSession => Boolean(row))
                : this.chatSessions.filter((item) => item.id !== session.id);
            if (this.chatDayPromptSession?.id === session.id) {
                this.chatDayPromptSession = null;
            }

            if (this.activeChatSessionId === session.id) {
                this.activeChatSessionId = null;
                this.chatMessages = this.buildChatMessages();
            }

            this.showToast('대화를 삭제했어.', 'success');
            this.scrollChatToBottom();
        } catch {
            this.showToast('대화 삭제 중 오류가 발생했어.', 'error');
        } finally {
            this.deletingChatSessionId = null;
            this.cdr.detectChanges();
        }
    }

    public setTheme(isDark: boolean): void {
        this.setThemeMode(isDark ? 'dark' : 'light');
    }

    public setChartPeriod(period: ChartPeriod): void {
        if (!['this_week', 'last_week', 'monthly'].includes(period)) return;
        if (this.activeChartPeriod === period) return;

        this.activeChartPeriod = period;
        this.chartCards = this.buildChartCards();
        this.hydrationPattern = this.buildHydrationPattern();
        this.miniStats = this.buildMiniStats();
        this.cdr.detectChanges();
    }

    public setWeightPeriod(period: WeightPeriod): void {
        if (!['1m', '3m', 'all'].includes(period)) return;
        if (this.activeWeightPeriod === period) return;

        this.activeWeightPeriod = period;
        this.refreshWeightDerivedState();
        this.cdr.detectChanges();
    }

    public changeWeightCalendarMonth(delta: number): void {
        if (!Number.isFinite(delta) || delta === 0) return;

        const [year, month] = this.activeWeightYearMonth.split('-').map(Number);
        const next = new Date(year, month - 1 + delta, 1);
        this.activeWeightYearMonth = this.yearMonthKey(next);

        const selected = this.parseDate(this.weightDate);
        const selectedDay = selected ? selected.getDate() : 1;
        const daysInMonth = new Date(next.getFullYear(), next.getMonth() + 1, 0).getDate();
        this.weightDate = this.dateKey(new Date(next.getFullYear(), next.getMonth(), Math.min(selectedDay, daysInMonth)));
        this.syncWeightInputForDate();
        this.refreshWeightDerivedState();
        this.cdr.detectChanges();
    }

    public selectWeightDate(cell: WeightCalendarCell): void {
        if (!cell.day) return;

        this.weightDate = cell.key;
        this.activeWeightYearMonth = cell.key.slice(0, 7);
        this.syncWeightInputForDate();
        this.refreshWeightDerivedState();
        this.cdr.detectChanges();
    }

    public onWeightDateChange(): void {
        const date = this.normalizeDateKey(this.weightDate);
        if (date) {
            this.activeWeightYearMonth = date.slice(0, 7);
        }
        this.syncWeightInputForDate();
        this.refreshWeightDerivedState();
        this.cdr.detectChanges();
    }

    public openWeightTargetEditor(): void {
        this.weightTargetInput = this.targetWeightKg ? this.targetWeightKg.toFixed(1) : '';
        this.weightTargetStatus = '';
        this.isWeightTargetEditing = true;
        this.cdr.detectChanges();
    }

    public cancelWeightTargetEdit(): void {
        this.weightTargetInput = this.targetWeightKg ? this.targetWeightKg.toFixed(1) : '';
        this.weightTargetStatus = '';
        this.isWeightTargetEditing = false;
        this.cdr.detectChanges();
    }

    public async saveWeightTarget(): Promise<void> {
        if (this.isWeightTargetSaving) return;

        const target = this.toNumber(this.weightTargetInput);
        if (target === null || target <= 0 || target >= 1000) {
            this.weightTargetStatus = '목표 체중을 0.1kg 단위로 입력해줘.';
            return;
        }

        this.isWeightTargetSaving = true;
        this.weightTargetStatus = '저장 중';
        this.cdr.detectChanges();

        try {
            const roundedTarget = this.round1(target);
            const targetPayload = { target_weight_kg: roundedTarget };
            this.applyWeightSettings(targetPayload);
            this.persistWeightTargetLocal(roundedTarget);
            this.isWeightTargetEditing = false;
            this.weightTargetStatus = '저장 중';
            this.cdr.detectChanges();

            const requestBody = {
                mode: 'target_weight',
                ...targetPayload
            };
            let result = await jsonRequest<any>('/api/weights', 'POST', requestBody);
            if (!result.success && result.error?.status === 401 && await refreshAuthTokens()) {
                result = await jsonRequest<any>('/api/weights', 'POST', requestBody);
            }

            if (!result.success) {
                const message = result.error?.kind === 'parse'
                    ? ''
                    : result.message || apiErrorMessage(result.error);
                this.weightTargetStatus = message || '목표 체중을 저장하지 못했어.';
                this.showToast(this.weightTargetStatus, 'error');
                return;
            }

            const payload = result.raw as any;
            const data = result.data as any;
            this.applyWeightSettings(
                payload?.settings ||
                payload?.data?.settings ||
                data?.settings ||
                payload?.data ||
                data ||
                targetPayload
            );
            this.isWeightTargetEditing = false;
            this.weightTargetStatus = '저장됨';
            this.showToast('목표 체중을 저장했어.', 'success');
        } catch {
            this.weightTargetStatus = '목표 체중 저장 중 오류가 발생했어.';
            this.showToast(this.weightTargetStatus, 'error');
        } finally {
            this.isWeightTargetSaving = false;
            this.cdr.detectChanges();
        }
    }

    public async saveWeightLog(): Promise<void> {
        if (this.isWeightSaving) return;

        const date = this.normalizeDateKey(this.weightDate);
        const weight = this.toNumber(this.weightInput);
        if (!date) {
            this.weightStatus = '날짜를 선택해줘.';
            return;
        }
        if (weight === null || weight <= 0 || weight >= 1000) {
            this.weightStatus = '체중을 0.1kg 단위로 입력해줘.';
            return;
        }
        if (date > this.todayDateKey) {
            this.weightStatus = '오늘 이후 날짜는 저장할 수 없어.';
            return;
        }

        this.isWeightSaving = true;
        this.weightStatus = '저장 중';
        this.cdr.detectChanges();

        try {
            const response = await fetch('/api/weights', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ date, weight_kg: this.round1(weight) })
            });
            const payload = await response.json().catch(() => null);
            if (!payload?.success) {
                this.weightStatus = payload?.message || '체중 기록을 저장하지 못했어.';
                return;
            }

            const rows = Array.isArray(payload.weights)
                ? payload.weights
                : Array.isArray(payload.data?.weights)
                    ? payload.data.weights
                    : payload.data ? [payload.data] : [];
            if (rows.length) {
                this.setWeights(rows);
            } else {
                await this.loadWeights();
            }
            const saved = this.normalizeWeightLog(payload.data);
            if (saved) {
                this.weightDate = saved.date;
                this.activeWeightYearMonth = saved.date.slice(0, 7);
                this.weightInput = saved.weight_kg.toFixed(1);
            }
            this.applyWeightSettings(payload.settings || payload.data?.settings || payload.data);
            this.weightStatus = '저장됨';
            this.showToast('체중 기록을 저장했어.', 'success');
        } catch {
            this.weightStatus = '체중 저장 중 오류가 발생했어.';
        } finally {
            this.isWeightSaving = false;
            this.cdr.detectChanges();
        }
    }

    public async deleteWeightLog(log: WeightLog, event?: Event): Promise<void> {
        event?.preventDefault();
        event?.stopPropagation();
        if (!log?.date || this.deletingWeightDate) return;
        if (!(await this.openConfirmDialog(`${this.displayDate(log.date, true)} 체중 기록을 삭제할까요?`, {
            title: '체중 기록 삭제',
            confirmLabel: '삭제',
            tone: 'danger',
            iconClass: 'fa-weight-scale'
        }))) return;

        this.deletingWeightDate = log.date;
        this.cdr.detectChanges();

        try {
            const response = await fetch(`/api/weights/${encodeURIComponent(log.date)}`, {
                method: 'DELETE'
            });
            const payload = await response.json().catch(() => null);
            if (!payload?.success) {
                this.showToast(payload?.message || '체중 기록을 삭제하지 못했어.', 'error');
                return;
            }

            const rows = Array.isArray(payload.weights)
                ? payload.weights
                : Array.isArray(payload.data?.weights)
                    ? payload.data.weights
                    : [];
            this.setWeights(rows);
            this.syncWeightInputForDate();
            this.applyWeightSettings(payload.settings || payload.data?.settings || payload.data);
            this.showToast('체중 기록을 삭제했어.', 'success');
        } catch {
            this.showToast('체중 삭제 중 오류가 발생했어.', 'error');
        } finally {
            this.deletingWeightDate = null;
            this.cdr.detectChanges();
        }
    }

    public setGalleryTab(tab: GalleryTab): void {
        if (!['capture', 'media', 'journal'].includes(tab)) return;
        if (this.galleryTab === tab) return;

        this.galleryTab = tab;
        this.galleryItems = this.buildGalleryItems();
        this.cdr.detectChanges();
    }

    public selectRunType(runType: RunType): void {
        this.selectedRunType = this.normalizeRunType(runType);
        this.cdr.detectChanges();
    }

    public addWaterAmount(timing: 'before' | 'after', amount: number): void {
        const current = timing === 'before'
            ? this.waterAmountFromInput(this.waterBeforeInput)
            : this.waterAmountFromInput(this.waterAfterInput);
        const next = Math.min(20000, (current || 0) + amount);
        if (timing === 'before') {
            this.waterBeforeInput = String(next);
        } else {
            this.waterAfterInput = String(next);
        }
        this.cdr.detectChanges();
    }

    public clearWaterAmount(timing: 'before' | 'after'): void {
        if (timing === 'before') {
            this.waterBeforeInput = '';
        } else {
            this.waterAfterInput = '';
        }
        this.cdr.detectChanges();
    }

    public async fetchRecentAppleMusicTracks(): Promise<void> {
        if (this.isAppleMusicLoading) return;
        if (!this.appSettings.appleMusicConnected) {
            await this.connectAppleMusic();
            if (!this.appSettings.appleMusicConnected) return;
        }

        this.isAppleMusicLoading = true;
        this.appleMusicStatus = '최근 재생곡 불러오는 중';
        this.cdr.detectChanges();

        try {
            const nativeTracks = await this.nativeRecentAppleMusicTracks();
            if (nativeTracks.length) {
                this.appleMusicRecentTracks = nativeTracks;
                this.appleMusicTracksVisible = true;
                this.appleMusicStatus = `${nativeTracks.length}곡 불러옴`;
                return;
            }

            const userToken = this.appleMusicUserToken();
            if (!userToken) {
                await this.connectAppleMusic();
            }
            const nextToken = this.appleMusicUserToken();
            if (!nextToken) {
                this.appleMusicStatus = 'Apple Music 연결이 필요해.';
                return;
            }

            const response = await fetch('/api/apple-music', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'recent', user_token: nextToken })
            });
            const payload = await response.json().catch(() => null);
            if (!payload?.success) {
                this.appleMusicStatus = payload?.message || '최근 재생곡을 불러오지 못했어.';
                this.showToast(this.appleMusicStatus, 'error');
                return;
            }

            const tracks = Array.isArray(payload.data)
                ? payload.data
                    .map((track: unknown) => this.normalizeMusicTrack(track))
                    .filter((track: MusicTrack | null): track is MusicTrack => Boolean(track))
                : [];
            this.appleMusicRecentTracks = tracks.slice(0, 30);
            this.appleMusicTracksVisible = true;
            this.appleMusicStatus = tracks.length ? `${tracks.length}곡 불러옴` : '최근 재생곡이 없어.';
        } catch {
            this.appleMusicStatus = 'Apple Music 최근곡 조회 중 오류가 발생했어.';
            this.showToast(this.appleMusicStatus, 'error');
        } finally {
            this.isAppleMusicLoading = false;
            this.cdr.detectChanges();
        }
    }

    public toggleMusicTrack(track: MusicTrack): void {
        if (!track?.id) return;

        if (this.selectedMusicTrackIds.includes(track.id)) {
            this.selectedMusicTrackIds = this.selectedMusicTrackIds.filter((id) => id !== track.id);
        } else {
            this.selectedMusicTrackIds = [...this.selectedMusicTrackIds, track.id];
        }
        this.cdr.detectChanges();
    }

    public isMusicTrackSelected(track: MusicTrack): boolean {
        return this.selectedMusicTrackIds.includes(track.id);
    }

    public clearSelectedMusic(): void {
        this.selectedMusicTrackIds = [];
        this.playlistNameInput = '';
        this.musicUrlInput = '';
        this.cdr.detectChanges();
    }

    public hasRunMusic(run?: CalendarRunDetail | RunRecord | null): boolean {
        const source = run ? run as unknown as Record<string, unknown> : {};
        const tracks = Array.isArray(source['topTracks']) ? source['topTracks'] : source['top_tracks'];
        return Boolean(
            source['playlistName']
            || source['playlist_name']
            || source['musicUrl']
            || source['music_url']
            || (Array.isArray(tracks) && tracks.length)
        );
    }

    public openRunMusicUrl(run: CalendarRunDetail | RunRecord, event?: Event): void {
        event?.preventDefault();
        event?.stopPropagation();
        const source = run as unknown as Record<string, unknown>;
        const url = typeof source['musicUrl'] === 'string'
            ? source['musicUrl']
            : typeof source['music_url'] === 'string'
                ? source['music_url']
                : '';
        if (!url) return;
        window.open(url, '_blank', 'noopener,noreferrer');
    }

    public musicTrackArtworkAlt(track?: MusicTrack | null): string {
        return track ? `${track.title} 앨범아트` : '앨범아트';
    }

    public openRunMediaPicker(run: CalendarRunDetail, input: HTMLInputElement): void {
        if (!run?.id || this.uploadingMediaRunId) return;

        this.pendingMediaRunId = run.id;
        input.value = '';
        input.click();
    }

    public openRunRecordImagePicker(run: CalendarRunDetail, input: HTMLInputElement): void {
        if (!run?.id || this.isUploading || this.isManualRunSaving) return;

        this.recordReuploadTargetId = run.id;
        this.parseErrorMessage = '';
        this.uploadProgress = 0;
        this.uploadStatus = '';
        input.value = '';
        input.click();
        this.cdr.detectChanges();
    }

    public async onRunRecordFilesSelected(event: Event, run: CalendarRunDetail): Promise<void> {
        const input = event.target instanceof HTMLInputElement ? event.target : null;
        const files = Array.from(input?.files || []);
        if (!run?.id) {
            if (input) input.value = '';
            return;
        }

        if (files.length) {
            this.markMediaAccessNoticeAccepted();
        }
        this.recordReuploadTargetId = run.id;
        await this.onFilesSelected(event, run.date || this.selectedCalendarDate, run.id, run.is_public !== false);
    }

    public async onRunMediaSelected(event: Event): Promise<void> {
        const input = event.target instanceof HTMLInputElement ? event.target : null;
        const files = Array.from(input?.files || []);
        const runId = this.pendingMediaRunId;
        this.pendingMediaRunId = null;
        if (!runId || !files.length) {
            if (input) input.value = '';
            return;
        }

        this.markMediaAccessNoticeAccepted();
        this.uploadingMediaRunId = runId;
        this.runMediaStatus = `${files.length}개 사진/영상 업로드 중`;
        this.cdr.detectChanges();

        try {
            const form = new FormData();
            files.forEach((file) => form.append('media', file));
            const response = await fetch(`/api/runs/${encodeURIComponent(runId)}/media`, {
                method: 'POST',
                body: form
            });
            const payload = await response.json().catch(() => null);
            if (!payload?.success) {
                this.runMediaStatus = payload?.message || '사진/영상을 업로드하지 못했어.';
                this.showToast(this.runMediaStatus, 'error');
                return;
            }

            const rows = Array.isArray(payload.media) ? payload.media : Array.isArray(payload.data) ? payload.data : [];
            this.applyRunMedia(runId, rows);
            const savedCount = Array.isArray(payload.data) ? payload.data.length : files.length;
            this.runMediaStatus = `${savedCount}개 사진/영상을 추가했어.`;
            this.showToast(this.runMediaStatus, 'success');
        } catch {
            this.runMediaStatus = '사진/영상 업로드 중 오류가 발생했어.';
            this.showToast(this.runMediaStatus, 'error');
        } finally {
            this.uploadingMediaRunId = null;
            if (input) input.value = '';
            this.cdr.detectChanges();
        }
    }

    public async deleteRunMedia(media: RunMedia, event?: Event): Promise<void> {
        event?.preventDefault();
        event?.stopPropagation();
        if (!media?.id || this.deletingMediaId) return;

        this.deletingMediaId = media.id;
        this.cdr.detectChanges();

        try {
            const response = await fetch(`/api/media/${encodeURIComponent(media.id)}`, {
                method: 'DELETE'
            });
            const payload = await response.json().catch(() => null);
            if (!payload?.success) {
                this.showToast(payload?.message || '첨부 미디어를 삭제하지 못했어.', 'error');
                return;
            }

            this.removeRunMedia(media.id);
            if (this.activeMediaViewer?.id === media.id) {
                this.activeMediaViewer = null;
            }
            this.showToast('첨부 미디어를 삭제했어.', 'success');
        } catch {
            this.showToast('첨부 미디어 삭제 중 오류가 발생했어.', 'error');
        } finally {
            this.deletingMediaId = null;
            this.cdr.detectChanges();
        }
    }

    public openMediaViewer(media: RunMedia): void {
        if (!media?.media_url) return;
        this.activeMediaViewer = media;
        this.cdr.detectChanges();
    }

    public closeMediaViewer(): void {
        this.activeMediaViewer = null;
        this.cdr.detectChanges();
    }

    public openTodayUpload(): void {
        const today = this.todayDateKey;
        const targetMonth = today.slice(0, 7);
        const monthChanged = this.activeYearMonth !== targetMonth;

        this.activeYearMonth = targetMonth;
        this.selectedCalendarDate = today;
        this.uploadProgress = 0;
        this.uploadStatus = '';
        this.resetRunRecordEditState();
        this.refreshDerivedState();
        this.setScreen('calendar');
        this.syncSelectedCalendarMemo();
        this.selectedCalendarRuns = this.buildSelectedCalendarRuns();
        this.cdr.detectChanges();
        this.revealSelectedCalendarRecords();

        if (monthChanged) {
            void this.loadGoalsForActiveMonth();
            void this.loadWeatherForActiveMonth();
        }
    }

    public openJournalViewer(run?: RunRecord | null): void {
        if (!run?.journal) return;
        this.activeJournalViewer = run;
        this.cdr.detectChanges();
    }

    public closeJournalViewer(): void {
        this.activeJournalViewer = null;
        this.cdr.detectChanges();
    }

    public isJournalEditing(run: CalendarRunDetail): boolean {
        return Boolean(run?.id && this.editingJournalRunId === run.id);
    }

    public isJournalSaving(run: CalendarRunDetail): boolean {
        return Boolean(run?.id && this.savingJournalRunId === run.id);
    }

    public startJournalEdit(run: CalendarRunDetail): void {
        if (!run?.id || this.savingJournalRunId) return;

        this.editingJournalRunId = run.id;
        this.journalDraftText = run.journal || '';
        this.journalStatusRunId = null;
        this.journalStatusText = '';
        this.cdr.detectChanges();
        this.resizeActiveJournalInput();
    }

    public cancelJournalEdit(): void {
        this.editingJournalRunId = null;
        this.journalDraftText = '';
        this.cdr.detectChanges();
    }

    public resizeJournalInput(event: Event): void {
        const input = event.target instanceof HTMLTextAreaElement ? event.target : null;
        if (!input) return;

        input.style.height = 'auto';
        input.style.height = `${input.scrollHeight}px`;
    }

    public async saveJournal(run: CalendarRunDetail): Promise<void> {
        if (!run?.id || this.savingJournalRunId) return;

        this.savingJournalRunId = run.id;
        this.journalStatusRunId = run.id;
        this.journalStatusText = '저장 중';
        this.cdr.detectChanges();

        try {
            const response = await fetch(`/api/runs/${encodeURIComponent(run.id)}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ journal: this.journalDraftText })
            });
            const payload = await response.json().catch(() => null);
            if (!payload?.success) {
                this.journalStatusText = payload?.message || '일기를 저장하지 못했어.';
                this.showToast(this.journalStatusText, 'error');
                return;
            }

            this.applyRunUpdate(payload.data);
            const savedText = String(payload?.data?.journal || '').trim();
            this.editingJournalRunId = null;
            this.journalDraftText = '';
            this.journalStatusText = savedText ? '저장됨' : '삭제됨';
            this.showToast(savedText ? '일기를 저장했어.' : '일기를 지웠어.', 'success');
        } catch {
            this.journalStatusText = '일기 저장 중 오류가 발생했어.';
            this.showToast(this.journalStatusText, 'error');
        } finally {
            this.savingJournalRunId = null;
            this.cdr.detectChanges();
        }
    }

    public async deleteJournal(run: CalendarRunDetail, event?: Event): Promise<void> {
        event?.preventDefault();
        event?.stopPropagation();
        if (!run?.id || this.savingJournalRunId) return;
        if (!(await this.openConfirmDialog('오늘의 일기를 삭제할까요?', {
            title: '일기 삭제',
            confirmLabel: '삭제',
            tone: 'danger',
            iconClass: 'fa-book'
        }))) return;

        const previousDraft = this.journalDraftText;
        const previousEditingRunId = this.editingJournalRunId;
        this.editingJournalRunId = run.id;
        this.journalDraftText = '';
        await this.saveJournal(run);
        if (this.journalStatusText !== '삭제됨') {
            this.journalDraftText = previousDraft;
            this.editingJournalRunId = previousEditingRunId;
        }
    }

    public selectCalendarDate(cell: CalendarCell): void {
        if (!cell.day) return;

        this.selectCalendarDateKey(cell.key);
    }

    public selectJournalDate(cell: JournalCalendarCell): void {
        if (!cell.day) return;
        if (Date.now() < this.calendarDateClickSuppressUntil) return;

        this.selectedJournalDate = cell.key;
        this.selectedJournalRuns = this.buildSelectedJournalRuns();
        this.cdr.detectChanges();
    }

    public changeCalendarMonth(delta: number): void {
        if (!Number.isFinite(delta) || delta === 0) return;

        const [year, month] = this.activeYearMonth.split('-').map(Number);
        const next = new Date(year, month - 1 + delta, 1);
        this.activeYearMonth = this.yearMonthKey(next);
        this.uploadProgress = 0;
        this.uploadStatus = '';
        this.resetRunRecordEditState();
        this.refreshDerivedState();
        this.cdr.detectChanges();
        void this.loadGoalsForActiveMonth();
        void this.loadWeatherForActiveMonth();
    }

    public startCalendarSwipe(event: TouchEvent): void {
        if (event.touches.length !== 1) {
            this.cancelCalendarSwipe();
            return;
        }

        const touch = event.touches[0];
        this.calendarSwipeStartX = touch.clientX;
        this.calendarSwipeStartY = touch.clientY;
    }

    public endCalendarSwipe(event: TouchEvent): void {
        if (this.calendarSwipeStartX === null || this.calendarSwipeStartY === null) return;
        const touch = event.changedTouches[0];
        if (!touch) {
            this.cancelCalendarSwipe();
            return;
        }

        const deltaX = touch.clientX - this.calendarSwipeStartX;
        const deltaY = touch.clientY - this.calendarSwipeStartY;
        this.cancelCalendarSwipe();

        const absX = Math.abs(deltaX);
        const absY = Math.abs(deltaY);
        if (absX < 48 || absX < absY * 1.35) return;

        event.preventDefault();
        this.calendarDateClickSuppressUntil = Date.now() + 350;
        this.changeCalendarMonth(deltaX < 0 ? 1 : -1);
    }

    public cancelCalendarSwipe(): void {
        this.calendarSwipeStartX = null;
        this.calendarSwipeStartY = null;
    }

    public async toggleRestDay(): Promise<void> {
        const date = this.restActionDate;
        if (!date) {
            this.showToast('휴식일로 지정할 날짜를 선택해줘.', 'error');
            return;
        }
        if (this.hasRunsOnDate(date) && !this.isRestDate(date)) {
            this.showToast('러닝 기록이 있는 날짜는 휴식일로 지정할 수 없어.', 'error');
            return;
        }

        const nextRest = !this.isRestDate(date);
        if (await this.saveRestDay(date, nextRest)) {
            this.showToast(nextRest
                ? `${this.displayDate(date, true)} 휴식일로 표시했어.`
                : `${this.displayDate(date, true)} 휴식일을 해제했어.`, 'success');
        }
    }

    public async markTodayRest(): Promise<void> {
        const date = this.todayDateKey;
        if (this.hasRunsOnDate(date)) {
            this.showToast('오늘 러닝 기록이 있어 휴식일로 표시할 수 없어.', 'error');
            return;
        }

        if (await this.saveRestDay(date, true)) {
            this.dismissRestRecommendation();
            this.showToast('오늘을 휴식일로 표시했어.', 'success');
        }
    }

    public async saveCalendarActivity(runType: RunType): Promise<void> {
        const normalized = this.normalizeRunType(runType);
        if (!SUPPORT_ACTIVITY_TYPES.has(normalized)) return;

        const date = this.selectedCalendarDate;
        if (!date) {
            this.showToast('기록할 날짜를 선택해줘.', 'error');
            return;
        }
        if (date > this.dateKey(new Date())) {
            this.showToast('미래 날짜는 지나간 뒤 기록할 수 있어.', 'error');
            return;
        }
        if (this.isRestDate(date)) {
            this.showToast('휴식일 해제 후 운동 기록을 남길 수 있어.', 'error');
            return;
        }
        if (this.hasRunsOnDate(date)) {
            this.showToast('이미 기록이 있는 날짜야.', 'error');
            return;
        }
        if (this.isManualRunSaving || this.isUploading) return;

        const label = this.runTypeLabel(normalized);
        const payload: RunRecord = {
            date,
            distance_km: 0,
            avg_pace: null,
            duration: null,
            run_type: normalized,
            calories: null,
            avg_heart_rate: null,
            cadence: null,
            is_public: false
        };

        this.isManualRunSaving = true;
        this.uploadStatus = `${label} 저장 중`;
        this.cdr.detectChanges();

        try {
            const saved = await this.saveRunRecord(payload);
            if (!saved.saved) {
                this.uploadStatus = saved.message || `${label} 기록을 저장하지 못했어.`;
                this.showToast(this.uploadStatus, 'error');
                return;
            }

            this.uploadStatus = `${label} 기록을 저장했어.`;
            this.showToast(`${label} 기록을 저장했어.`, 'success');
            await this.loadRuns();
        } finally {
            this.isManualRunSaving = false;
            this.cdr.detectChanges();
        }
    }

    public dismissRestRecommendation(): void {
        this.isRestBannerDismissed = true;
        try {
            window.localStorage.setItem(this.restBannerDismissKey(this.todayDateKey), '1');
        } catch {
            return;
        } finally {
            this.cdr.detectChanges();
        }
    }

    public openFilePicker(input: HTMLInputElement): void {
        input.click();
    }

    public async saveCalendarMemo(): Promise<void> {
        const date = this.selectedCalendarDate;
        if (!date) {
            this.showToast('메모를 남길 날짜를 선택해줘.', 'error');
            return;
        }

        this.isCalendarMemoSaving = true;
        this.calendarMemoStatus = '저장 중';
        this.cdr.detectChanges();

        try {
            const memo = this.calendarMemoText.trim();
            const response = await fetch('/api/day-notes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ date, memo })
            });
            const payload = await response.json();
            if (!payload?.success) {
                this.calendarMemoStatus = payload?.message || '메모를 저장하지 못했어.';
                return;
            }

            const rows = Array.isArray(payload?.notes) ? payload.notes : [];
            this.setDayNotes(rows);
            this.selectedCalendarDate = date;
            this.calendarMemoText = this.memoForDate(date);
            this.calendarMemoStatus = memo ? '저장됨' : '삭제됨';
            this.showToast(memo ? '메모를 저장했어.' : '메모를 지웠어.', 'success');
        } catch {
            this.calendarMemoStatus = '메모 저장 중 오류가 발생했어.';
        } finally {
            this.isCalendarMemoSaving = false;
            this.cdr.detectChanges();
        }
    }

    public async saveUploadJournal(): Promise<void> {
        const date = this.selectedCalendarDate;
        if (!date) {
            this.showToast('일기를 남길 날짜를 선택해줘.', 'error');
            return;
        }
        if (!this.canUploadSelectedCalendarDate) {
            this.showToast('이 날짜에는 일기를 저장할 수 없어.', 'error');
            return;
        }
        if (this.isUploadJournalSaving) return;

        const memo = this.uploadJournalText.trim();
        const savedMemo = this.memoForDate(date).trim();
        if (!memo && !savedMemo) {
            this.uploadJournalStatus = '저장할 일기를 입력해줘.';
            this.cdr.detectChanges();
            return;
        }

        this.isUploadJournalSaving = true;
        this.uploadJournalStatus = '저장 중';
        this.cdr.detectChanges();

        try {
            const response = await fetch('/api/day-notes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ date, memo })
            });
            const payload = await response.json().catch(() => null);
            if (!payload?.success) {
                this.uploadJournalStatus = payload?.message || '일기를 저장하지 못했어.';
                this.showToast(this.uploadJournalStatus, 'error');
                return;
            }

            const rows = Array.isArray(payload?.notes) ? payload.notes : [];
            this.setDayNotes(rows);
            this.selectedCalendarDate = date;
            this.uploadJournalText = memo ? this.memoForDate(date) || memo : '';
            this.uploadJournalStatus = memo ? '저장됨' : '삭제됨';
            this.showToast(memo ? '일기를 저장했어.' : '일기를 지웠어.', 'success');
        } catch {
            this.uploadJournalStatus = '일기 저장 중 오류가 발생했어.';
            this.showToast(this.uploadJournalStatus, 'error');
        } finally {
            this.isUploadJournalSaving = false;
            this.cdr.detectChanges();
        }
    }

    public async toggleCycleFeature(): Promise<void> {
        if (!this.shouldShowCycleFeature || this.isCyclePreferenceSaving) return;

        const previousEnabled = this.isCycleFeatureEnabled;
        const nextEnabled = !this.isCycleFeatureEnabled;
        this.isCycleFeatureEnabled = nextEnabled;
        this.persistCycleLocalSettings();
        this.isCyclePreferenceSaving = true;
        this.cycleStatus = nextEnabled ? '생리주기 설정 저장 중' : '생리주기 연동 끄는 중';
        this.cdr.detectChanges();

        const saved = await this.saveCycleFeaturePreference(nextEnabled);
        this.isCyclePreferenceSaving = false;
        if (!saved) {
            this.isCycleFeatureEnabled = previousEnabled;
            this.persistCycleLocalSettings();
            this.cycleStatus = '생리주기 설정을 저장하지 못했어. 다시 시도해줘.';
            this.showToast(this.cycleStatus, 'error');
            this.cdr.detectChanges();
            return;
        }

        if (!nextEnabled) {
            this.cycleLogs = [];
            this.cycleSummary = { ...EMPTY_CYCLE_SUMMARY };
            this.cycleStatus = '생리주기 연동 꺼짐';
            this.refreshDerivedState();
            this.cdr.detectChanges();
            return;
        }

        this.cycleStatus = '주기 데이터 불러오는 중';
        this.syncCycleDraftWithSelectedDate();
        this.cdr.detectChanges();
        await this.loadCycles();
    }

    public toggleCycleOverlay(): void {
        if (!this.shouldShowCycleFeature || !this.isCycleFeatureEnabled) return;

        this.isCycleOverlayEnabled = !this.isCycleOverlayEnabled;
        this.persistCycleLocalSettings();
        this.refreshDerivedState();
        this.cdr.detectChanges();
    }

    public setCycleStartFromSelected(): void {
        if (!this.selectedCalendarDate) return;
        this.cycleStartDate = this.selectedCalendarDate;
        if (!this.normalizeDateKey(this.cycleEndDate) || this.cycleEndDate < this.cycleStartDate) {
            this.cycleEndDate = this.cycleStartDate;
        }
        this.cycleStatus = '';
        this.cdr.detectChanges();
    }

    public setCycleEndFromSelected(): void {
        if (!this.selectedCalendarDate) return;
        this.cycleEndDate = this.selectedCalendarDate;
        if (!this.normalizeDateKey(this.cycleStartDate) || this.cycleStartDate > this.cycleEndDate) {
            this.cycleStartDate = this.cycleEndDate;
        }
        this.cycleStatus = '';
        this.cdr.detectChanges();
    }

    public onCycleDateChange(): void {
        const start = this.normalizeDateKey(this.cycleStartDate);
        const end = this.normalizeDateKey(this.cycleEndDate);
        if (start && end && end < start) {
            this.cycleEndDate = start;
        }
        this.cycleStatus = '';
        this.cdr.detectChanges();
    }

    public selectCycleFlow(level: CycleFlowLevel): void {
        if (this.isCycleFormReadOnly || this.isCycleSaving) return;
        if (!CYCLE_FLOW_OPTIONS.some((item) => item.id === level)) return;
        this.selectedCycleFlowLevel = level;
        this.cycleStatus = '';
        this.cdr.detectChanges();
    }

    public selectCycleCondition(emoji: string): void {
        if (this.isCycleFormReadOnly || this.isCycleSaving) return;
        if (!this.normalizeCycleConditionEmoji(emoji)) return;
        this.selectedCycleConditionEmoji = emoji;
        this.cycleStatus = '';
        this.cdr.detectChanges();
    }

    public handleCyclePrimaryAction(): void {
        if (this.isCycleSaving) return;
        if (this.selectedCalendarCycleLog && !this.isCycleNoteEditing) {
            this.startCycleNoteEdit();
            return;
        }
        void this.saveCycleLog();
    }

    public startCycleNoteEdit(): void {
        const log = this.selectedCalendarCycleLog;
        if (log) {
            this.selectedCycleFlowLevel = this.normalizeCycleFlowLevel(log.flow_level) || this.selectedCycleFlowLevel;
            this.selectedCycleConditionEmoji = this.normalizeCycleConditionEmoji(log.condition_emoji) || this.selectedCycleConditionEmoji;
            this.cycleNoteText = log.note || '';
        }
        this.isCycleNoteEditing = true;
        this.cycleStatus = '';
        this.cdr.detectChanges();
    }

    public async saveCycleLog(): Promise<void> {
        if (!this.isCycleFeatureEnabled || this.isCycleSaving) return;

        if (!(await ensureAuthenticated())) {
            this.cycleStatus = '로그인이 만료되었습니다. 다시 로그인해주세요.';
            return;
        }

        const logDate = this.normalizeDateKey(this.selectedCalendarDate) || this.todayDateKey;
        if (!logDate) {
            this.cycleStatus = '기록할 날짜를 선택해줘.';
            return;
        }
        if (logDate > this.todayDateKey) {
            this.cycleStatus = '미래 날짜에는 생리 기록을 저장할 수 없어.';
            return;
        }

        this.isCycleSaving = true;
        this.cycleStatus = '저장 중';
        this.cdr.detectChanges();

        try {
            const response = await fetch(resolveApiUrl('/api/cycles'), {
                method: 'POST',
                headers: this.cycleRequestHeaders(),
                body: JSON.stringify({
                    consent: true,
                    start_date: logDate,
                    end_date: logDate,
                    cycle_phase: 'menstrual',
                    flow_level: this.selectedCycleFlowLevel,
                    condition_emoji: this.selectedCycleConditionEmoji,
                    id: this.selectedCalendarCycleLog?.id || undefined,
                    note: this.cycleNoteText.trim()
                })
            });
            const payload = await response.json().catch(() => null);
            if (!payload?.success) {
                this.cycleStatus = payload?.message || '주기 기록을 저장하지 못했어.';
                return;
            }

            const savedNote = this.cycleNoteText.trim();
            this.setCycles(Array.isArray(payload.cycles) ? payload.cycles : payload.data ? [payload.data] : [], payload.summary);
            this.cycleNoteText = savedNote;
            this.isCycleNoteEditing = false;
            this.cycleStartDate = logDate;
            this.cycleEndDate = logDate;
            this.cycleStatus = '저장됨';
            this.showToast('생리 기록을 저장했어.', 'success');
        } catch {
            this.cycleStatus = '생리 기록 저장 중 오류가 발생했어.';
        } finally {
            this.isCycleSaving = false;
            this.cdr.detectChanges();
        }
    }

    public async deleteCycleLog(log: CycleLog, event?: Event): Promise<void> {
        event?.preventDefault();
        event?.stopPropagation();
        if (!this.isCycleFeatureEnabled || !log?.id || this.deletingCycleId) return;
        if (!(await this.openConfirmDialog(`${this.displayDate(log.start_date, true)} 생리 기록을 삭제할까요?`, {
            title: '생리 기록 삭제',
            confirmLabel: '삭제',
            tone: 'danger',
            iconClass: 'fa-heart'
        }))) return;

        this.deletingCycleId = log.id;
        this.cdr.detectChanges();

        try {
            const response = await fetch(resolveApiUrl('/api/cycles'), {
                method: 'DELETE',
                headers: this.cycleRequestHeaders(),
                body: JSON.stringify({ consent: true, id: log.id })
            });
            const payload = await response.json().catch(() => null);
            if (!payload?.success) {
                this.showToast(payload?.message || '주기 기록을 삭제하지 못했어.', 'error');
                return;
            }

            this.setCycles(Array.isArray(payload.data) ? payload.data : [], payload.summary);
            this.showToast('주기 기록을 삭제했어.', 'success');
        } catch {
            this.showToast('주기 삭제 중 오류가 발생했어.', 'error');
        } finally {
            this.deletingCycleId = null;
            this.cdr.detectChanges();
        }
    }

    public async deleteAllCycleData(): Promise<void> {
        if (!this.isCycleFeatureEnabled) return;
        if (!(await this.openConfirmDialog('저장된 생리 기록을 모두 삭제할까요?', {
            title: '생리 기록 전체 삭제',
            confirmLabel: '전체 삭제',
            tone: 'danger',
            iconClass: 'fa-heart-crack'
        }))) return;

        this.deletingCycleId = '__all__';
        this.cycleStatus = '전체 삭제 중';
        this.cdr.detectChanges();

        try {
            const response = await fetch(resolveApiUrl('/api/cycles'), {
                method: 'DELETE',
                headers: this.cycleRequestHeaders(),
                body: JSON.stringify({ consent: true, all: true })
            });
            const payload = await response.json().catch(() => null);
            if (!payload?.success) {
                this.cycleStatus = payload?.message || '주기 데이터를 삭제하지 못했어.';
                return;
            }

            this.setCycles([], payload.summary);
            this.cycleStatus = '전체 삭제됨';
            this.showToast('주기 데이터를 모두 삭제했어.', 'success');
        } catch {
            this.cycleStatus = '주기 데이터 삭제 중 오류가 발생했어.';
        } finally {
            this.deletingCycleId = null;
            this.cdr.detectChanges();
        }
    }

    public async onCalendarFilesSelected(event: Event): Promise<void> {
        const input = event.target instanceof HTMLInputElement ? event.target : null;
        const files = Array.from(input?.files || []);
        const targetDate = this.canUploadSelectedCalendarDate ? this.selectedCalendarDate : null;
        if (!targetDate) {
            if (input) input.value = '';
            return;
        }
        if (files.length) {
            this.markMediaAccessNoticeAccepted();
        }

        await this.onFilesSelected(event, targetDate);
    }

    public onCalendarMediaDraftSelected(event: Event): void {
        const input = event.target instanceof HTMLInputElement ? event.target : null;
        const files = Array.from(input?.files || []);
        if (!this.canUploadSelectedCalendarDate || !files.length) {
            if (input) input.value = '';
            return;
        }

        const mediaFiles = files.filter((file) => this.isImageFile(file) || this.isVideoFile(file));
        if (!mediaFiles.length) {
            this.calendarMediaDraftStatus = '사진이나 영상을 선택해줘.';
            if (input) input.value = '';
            this.cdr.detectChanges();
            return;
        }

        this.markMediaAccessNoticeAccepted();
        this.calendarMediaDraftFiles = [...this.calendarMediaDraftFiles, ...mediaFiles];
        this.calendarMediaDraftStatus = `${this.calendarMediaDraftFiles.length}개 사진/영상 선택됨`;
        if (input) input.value = '';
        this.cdr.detectChanges();
    }

    public async onFilesSelected(
        event: Event,
        targetDate: string | null = null,
        updateRunId: string | null = null,
        updateRunPublic: boolean | null = null
    ): Promise<void> {
        const input = event.target instanceof HTMLInputElement ? event.target : null;
        const files = Array.from(input?.files || []);
        if (!files.length) return;

        this.isUploading = true;
        this.parseErrorMessage = '';
        this.uploadProgress = 0;
        if (updateRunId) {
            this.recordReuploadTargetId = updateRunId;
            this.manualEntryRunId = updateRunId;
        }
        const orderedFiles = targetDate
            ? [
                ...files.filter((file) => this.isImageFile(file)),
                ...files.filter((file) => !this.isImageFile(file))
            ]
            : files;
        this.uploadStatus = updateRunId
            ? `${this.displayDate(targetDate || this.selectedCalendarDate || this.todayDateKey, true)} 기록 다시 업로드 준비 중`
            : targetDate
            ? `${this.displayDate(targetDate, true)} 기록 ${files.length}개 업로드 준비 중`
            : `${files.length}개 이미지 파싱 준비 중`;
        this.cdr.detectChanges();

        const runType = this.selectedRunType;
        const hydration = this.hydrationUploadPayload();
        const music = this.musicUploadPayload(!updateRunId);
        const isPublic = updateRunPublic !== null ? updateRunPublic : targetDate ? this.calendarUploadIsPublic : true;
        let savedCount = 0;
        let lastMessage = '';
        const savedIds: string[] = [];
        let mediaTargetRunId = updateRunId || (targetDate ? this.runIdForCalendarMediaTarget() : '');
        const draftMediaFiles = targetDate && !updateRunId ? [...this.calendarMediaDraftFiles] : [];
        let mediaSavedCount = 0;
        for (let index = 0; index < orderedFiles.length; index++) {
            const result = await this.parseAndSaveFile(orderedFiles[index], index, orderedFiles.length, targetDate, runType, hydration, music, mediaTargetRunId, isPublic, updateRunId);
            if (result.saved) savedCount += 1;
            if (result.message) lastMessage = result.message;
            if (result.run?.id) {
                savedIds.push(result.run.id);
                if (!mediaTargetRunId) mediaTargetRunId = result.run.id;
            }
            if (result.mediaRunId && !mediaTargetRunId) {
                mediaTargetRunId = result.mediaRunId;
            }
        }

        if (savedIds.length && draftMediaFiles.length) {
            const targetRunId = savedIds[0];
            for (let index = 0; index < draftMediaFiles.length; index++) {
                const result = await this.uploadCalendarMediaFile(targetRunId, draftMediaFiles[index], index, draftMediaFiles.length);
                if (result.saved) mediaSavedCount += 1;
                if (result.message) lastMessage = result.message;
            }
        }

        this.isUploading = false;
        this.uploadProgress = 100;
        this.uploadStatus = updateRunId && savedCount
            ? '기록을 다시 저장했어.'
            : savedCount
            ? mediaSavedCount
                ? `${savedCount}개 기록과 사진/영상 ${mediaSavedCount}개를 저장했어.`
                : `${savedCount}개 항목을 저장했어.`
            : lastMessage || '저장된 기록이 없어.';
        if (!savedCount && lastMessage) {
            this.parseErrorMessage = lastMessage;
        }
        if (savedCount) {
            this.resetHydrationInputs();
            this.resetMusicInputs();
            this.calendarMediaDraftFiles = [];
            this.calendarMediaDraftStatus = '';
        }
        if (input) input.value = '';
        await this.loadRuns();
    }

    private emptyManualRunForm(): any {
        return {
            distance_km: '',
            avg_pace: '',
            duration: '',
            calories: '',
            avg_heart_rate: '',
            cadence: ''
        };
    }

    private manualRunFormForRun(runId?: string | null): any {
        const run = runId ? this.runs.find((item) => item.id === runId) : null;
        if (!run) return this.emptyManualRunForm();

        return {
            distance_km: this.formatDistance(run.distance_km),
            avg_pace: run.avg_pace ? this.displayPace(run.avg_pace) : '',
            duration: run.duration || '',
            calories: run.calories ?? '',
            avg_heart_rate: run.avg_heart_rate ?? '',
            cadence: run.cadence ?? ''
        };
    }

    private resetRunRecordEditState(): void {
        this.manualEntryVisible = false;
        this.manualEntryRunId = null;
        this.recordReuploadTargetId = null;
        this.parseErrorMessage = '';
        this.manualRunForm = this.emptyManualRunForm();
    }

    public openManualEntry(run?: CalendarRunDetail | string | null): void {
        const targetRunId = typeof run === 'string'
            ? run
            : run?.id || this.recordReuploadTargetId || null;
        this.manualEntryRunId = targetRunId;
        if (targetRunId) this.recordReuploadTargetId = targetRunId;
        this.manualRunForm = this.manualRunFormForRun(targetRunId);
        this.manualEntryVisible = true;
        this.parseErrorMessage = '';
        this.uploadProgress = 0;
        this.uploadStatus = targetRunId
            ? `${this.selectedCalendarDateText} 기록을 수동으로 수정해줘.`
            : this.selectedCalendarDate
            ? `${this.selectedCalendarDateText} 기록을 수동으로 입력해줘.`
            : '기록을 수동으로 입력해줘.';
        this.cdr.detectChanges();
    }

    public closeManualEntry(): void {
        if (this.isManualRunSaving) return;
        this.manualEntryVisible = false;
        this.manualEntryRunId = null;
        this.cdr.detectChanges();
    }

    public async saveManualRun(): Promise<void> {
        if (this.isManualRunSaving) return;
        const date = this.selectedCalendarDate || this.todayDateKey;
        const distance = this.toNumber(this.manualRunForm.distance_km);
        const distanceKm = distance !== null ? this.displayDistanceToKm(distance) : 0;
        if (!date || !distanceKm || distanceKm <= 0) {
            this.uploadStatus = '거리 값을 입력해줘.';
            this.cdr.detectChanges();
            return;
        }

        this.isManualRunSaving = true;
        this.uploadStatus = '수동 기록 저장 중';
        this.cdr.detectChanges();

        const hydration = this.hydrationUploadPayload();
        const music = this.musicUploadPayload(!this.manualEntryRunId);
        const manualTargetRun = this.manualEntryRunId
            ? this.runs.find((run) => run.id === this.manualEntryRunId)
            : null;
        const payload: RunRecord = {
            date,
            distance_km: distanceKm,
            avg_pace: this.storagePaceTextFromDisplay(String(this.manualRunForm.avg_pace || '')),
            duration: String(this.manualRunForm.duration || '').trim() || null,
            run_type: manualTargetRun?.run_type || this.selectedRunType,
            calories: this.toNumber(this.manualRunForm.calories),
            avg_heart_rate: this.toNumber(this.manualRunForm.avg_heart_rate),
            cadence: this.toNumber(this.manualRunForm.cadence),
            is_public: this.manualEntryRunId ? manualTargetRun?.is_public !== false : this.calendarUploadIsPublic,
            ...hydration,
            ...music
        };

        try {
            const saved = await this.saveRunRecord(payload, this.manualEntryRunId);
            if (!saved.saved) {
                this.uploadStatus = saved.message || '수동 기록을 저장하지 못했어.';
                return;
            }

            this.manualRunForm = this.emptyManualRunForm();
            this.resetHydrationInputs();
            this.resetMusicInputs();
            this.manualEntryVisible = false;
            this.manualEntryRunId = null;
            this.uploadStatus = '수동 기록을 저장했어.';
            this.showToast('러닝 기록을 저장했어.', 'success');
            await this.loadRuns();
        } finally {
            this.isManualRunSaving = false;
            this.cdr.detectChanges();
        }
    }

    public async sendChat(): Promise<void> {
        const text = this.chatText.trim();
        if (!text || this.isChatSending) return;
        if (this.isAiUsageExhausted) {
            this.notifyAiUsageLimit(this.aiUsage);
            return;
        }

        const sessionId = this.prepareChatSessionForSend();
        this.chatDayPromptSession = null;
        this.chatMessages = [
            ...this.chatMessages,
            { sender: 'user', text, created_at: new Date().toISOString() },
            { sender: 'ai', text: '', created_at: new Date().toISOString(), streaming: true }
        ];
        const aiMessageIndex = this.chatMessages.length - 1;
        this.chatText = '';
        this.isChatSending = true;
        this.cdr.detectChanges();
        this.scrollChatToBottom();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    ...authHeaderForUrl('/api/chat')
                },
                body: JSON.stringify({
                    message: text,
                    session_id: sessionId,
                    client_date: this.todayDateKey,
                    pacer_persona: this.appSettings.pacerPersona,
                    stream: false,
                    cycle_enabled: this.isCycleFeatureEnabled
                })
            });
            const rawPayload = await response.json().catch(() => null);
            const payload = this.normalizeWizStatusPayload(rawPayload) as ChatResponse | null;
            this.applyAiUsage(payload?.usage, true);
            const reply = payload?.success
                ? payload?.reply || '답변을 만들지 못했어.'
                : payload?.message || 'AI 채팅 중 오류가 발생했어.';
            this.replaceChatMessage(aiMessageIndex, reply, false);
            this.activeChatSessionId = payload?.session_id || payload?.session?.id || this.activeChatSessionId;
            this.upsertChatSession(payload?.session);
            await this.loadChatHistory();
        } catch {
            this.replaceChatMessage(aiMessageIndex, 'AI 채팅 서버에 연결하지 못했어.', false);
        } finally {
            this.isChatSending = false;
            this.finishChatMessage(aiMessageIndex);
        }
    }

    public async refreshAiConnection(): Promise<void> {
        this.aiLoginRefreshStatus = '연결 상태 확인 중';
        await this.loadAiConnection();
        this.aiLoginRefreshStatus = this.aiConnection?.message || '연결 상태를 확인했어.';
        this.cdr.detectChanges();
    }

    public async refreshCodexLogin(): Promise<void> {
        if (this.aiLoginRefreshPending) return;

        if (this.aiConnection?.mode !== 'codex') {
            await this.refreshAiConnection();
            return;
        }

        this.aiLoginRefreshPending = true;
        this.aiLoginRefreshStatus = 'Codex 로그인 갱신 준비 중';
        this.aiLoginDeviceUrl = '';
        this.aiLoginDeviceCode = '';
        this.aiLoginDeviceExpiresIn = null;
        this.cdr.detectChanges();

        try {
            const response = await fetch('/api/ai-config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...authHeaderForUrl('/api/ai-config')
                },
                body: JSON.stringify({ action: 'refresh_login' })
            });
            const payload = await response.json() as AiLoginRefreshResult;

            if (payload?.config) {
                this.applyAiConnection(payload.config);
            } else {
                await this.loadAiConnection();
            }

            this.aiLoginRefreshStatus = payload?.message || (payload?.success ? '로그인 갱신을 요청했어.' : '로그인 갱신에 실패했어.');
            this.aiLoginDeviceUrl = typeof payload?.auth_url === 'string' ? payload.auth_url : '';
            this.aiLoginDeviceCode = typeof payload?.user_code === 'string' ? payload.user_code : '';
            this.aiLoginDeviceExpiresIn = typeof payload?.expires_in_minutes === 'number' && Number.isFinite(payload.expires_in_minutes)
                ? payload.expires_in_minutes
                : null;
        } catch {
            this.aiLoginRefreshStatus = '로그인 갱신 요청 중 오류가 발생했어.';
        } finally {
            this.aiLoginRefreshPending = false;
            this.cdr.detectChanges();
        }
    }

    public openAiAuthUrl(): void {
        if (!this.aiLoginDeviceUrl) return;
        window.open(this.aiLoginDeviceUrl, '_blank', 'noopener,noreferrer');
    }

    private installAgreementLoadingMessageSync(): void {
        if (typeof window === 'undefined') return;

        this.agreementModalVisibleForLoading = typeof document !== 'undefined'
            ? !!document.body?.classList.contains(this.agreementModalBodyClass)
            : false;

        const handleAgreementModalState = (event: Event): void => {
            const detail = (event as CustomEvent<{ visible?: boolean }>).detail;
            this.agreementModalVisibleForLoading = !!detail?.visible;
            if (this.isInitialLoading) {
                this.refreshInitialLoadingDetail();
            }
        };

        window.addEventListener(this.agreementModalEventName, handleAgreementModalState);
        this.cleanupHandlers.push(() => window.removeEventListener(this.agreementModalEventName, handleAgreementModalState));
    }

    public ngAfterViewInit(): void {
        this.installDashboardViewportSync();
        this.installAgreementLoadingMessageSync();

        this.bindNativeClick('[data-screen]', (target) => {
            const screen = target.dataset.screen as ScreenKey | undefined;
            if (screen) this.setScreen(screen);
        });

        this.bindNativeClick('[data-theme]', (target) => {
            this.setTheme(target.dataset.theme === 'dark');
        });

        this.bindNativeClick('[data-chart-period]', (target) => {
            const period = target.dataset.chartPeriod as ChartPeriod | undefined;
            if (period) this.setChartPeriod(period);
        });

        this.bindNativeClick('[data-weight-period]', (target) => {
            const period = target.dataset.weightPeriod as WeightPeriod | undefined;
            if (period) this.setWeightPeriod(period);
        });

        this.bindNativeClick('[data-calendar-nav]', (target) => {
            this.changeCalendarMonth(target.dataset.calendarNav === 'next' ? 1 : -1);
        });

        this.bindNativeClick('[data-calendar-date]', (target) => {
            const date = target.dataset.calendarDate;
            if (date) this.selectCalendarDateKey(date);
        });

        this.bindNativeClick('[data-rest-toggle]', () => {
            void this.toggleRestDay();
        });

        this.bindNativeClick('[data-ai-settings-open]', () => {
            this.openAiSettings();
        });

        this.bindNativeClick('[data-ai-settings-back]', () => {
            this.setScreen('chat');
        });

        this.bindNativeClick('[data-ai-settings-refresh]', () => {
            void this.refreshAiConnection();
        });

        this.bindNativeClick('[data-chat-history-close]', () => {
            this.closeChatHistory();
        });

        void this.loadInitialDashboardData();
    }

    public async loadInitialDashboardData(): Promise<void> {
        this.isInitialLoading = true;
        this.deferredDashboardDataStarted = false;
        this.initialCoreDataLoaded = false;
        this.initialLoadingSteps.clear();
        this.initialLoadingDetail = this.agreementModalVisibleForLoading ? '이용 약관 동의 중' : '초기 데이터를 불러오는 중';
        this.initialErrorMessage = '';
        this.cdr.detectChanges();
        let shouldStartDeferredData = false;

        try {
            this.loadRestBannerDismissed();
            this.loadCycleLocalSettings();

            const bootstrapStatus = await this.runInitialLoadingStep('runs', '초기 데이터를 불러오는 중', () => this.loadDashboardBootstrap());
            if (bootstrapStatus === 'unauthenticated') {
                this.redirectToAccess();
                return;
            }

            let runLoaded = bootstrapStatus === 'loaded';
            if (!runLoaded) {
                const authenticated = await this.runInitialLoadingStep('auth', '로그인 상태를 확인하는 중', () => ensureAuthenticated());
                if (!authenticated) {
                    this.redirectToAccess();
                    return;
                }

                runLoaded = await this.runInitialLoadingStep('runs', '러닝 기록을 불러오는 중', () => this.loadRuns(true, false, false, this.initialRunsUrl(), false));
                if (runLoaded) {
                    this.initialRunsTruncated = true;
                }
                await this.runInitialLoadingStep('profile', '프로필을 확인하는 중', () => this.loadProfile());
            }

            if (!runLoaded && !this.initialErrorMessage) {
                this.initialErrorMessage = '초기 데이터를 불러오지 못했어. 네트워크를 확인한 뒤 다시 시도해줘';
            }

            if (runLoaded) {
                await this.loadInitialDashboardCoreData();
                shouldStartDeferredData = !this.initialErrorMessage;
            }
        } catch (error) {
            this.initialErrorMessage = error instanceof Error && error.message
                ? error.message
                : '초기 데이터를 불러오지 못했어. 네트워크를 확인한 뒤 다시 시도해줘';
        } finally {
            this.initialLoadingSteps.clear();
            this.initialLoadingDetail = '';
            this.isInitialLoading = false;
            this.cdr.detectChanges();
            if (shouldStartDeferredData) {
                this.startWeatherAutoRefresh();
                this.scheduleDeferredDashboardData();
            }
        }
    }

    private redirectToAccess(): void {
        clearAuthTokens();
        window.location.replace('/access');
    }

    public ngOnDestroy(): void {
        this.uninstallDashboardViewportSync();
        this.cleanupHandlers.forEach((cleanup) => cleanup());
        this.cleanupHandlers.length = 0;
        if (this.weatherRefreshTimer !== null) {
            window.clearInterval(this.weatherRefreshTimer);
            this.weatherRefreshTimer = null;
        }
        if (this.accountDeleteRedirectTimer !== null) {
            window.clearTimeout(this.accountDeleteRedirectTimer);
            this.accountDeleteRedirectTimer = null;
        }
        this.stopSystemThemeListener();
    }

    public navIsActive(screen: ScreenKey): boolean {
        const group = this.navActiveGroups[screen] || [screen];
        return group.includes(this.activeScreen);
    }

    public trackById(index: number, item: TabItem): string {
        return item.id || `${index}`;
    }

    public trackByLabel(index: number, item: StatCard): string {
        return item.label || `${index}`;
    }

    public trackSettingsOption(index: number, item: SettingsOption): string {
        return item.id || `${index}`;
    }

    public trackGoalOption(index: number, item: GoalTypeOption): string {
        return item.id || `${index}`;
    }

    public trackGoalProgress(index: number, item: GoalProgress): string {
        return `${item.year_month}-${item.goal_type}-${index}`;
    }

    public trackGoalHistory(index: number, item: GoalHistory): string {
        return item.year_month || `${index}`;
    }

    public trackChallenge(index: number, item: Challenge): string {
        return item.id || `${index}`;
    }

    public trackChallengeMember(index: number, item: ChallengeMember): string {
        return item.user_id || `${index}`;
    }

    public trackChallengeType(index: number, item: ChallengeTypeOption): string {
        return item.id || `${index}`;
    }

    public trackChallengeTab(index: number, item: ChallengeTabOption): string {
        return item.id || `${index}`;
    }

    public trackFriendTab(index: number, item: FriendTabOption): string {
        return item.id || `${index}`;
    }

    public trackSocialProfile(index: number, item: SocialProfile): string {
        return item.id || `${index}`;
    }

    public trackFeedRun(index: number, item: FeedRun): string {
        return item.id || `${index}`;
    }

    public trackFeedReaction(index: number, item: FeedReactionSummary): string {
        return item.type || `${index}`;
    }

    public trackFeedReactionUser(index: number, item: FeedReactionUser): string {
        return `${item.user_id}-${item.type}-${index}`;
    }

    public trackFeedComment(index: number, item: FeedComment): string {
        return item.id || `${index}`;
    }

    public trackCommunityNotification(index: number, item: CommunityNotification): string {
        return item.id || `${item.type}-${index}`;
    }

    public trackRankingPeriod(index: number, item: RankingPeriodOption): string {
        return item.id || `${index}`;
    }

    public trackRankingScope(index: number, item: RankingScopeOption): string {
        return item.id || `${index}`;
    }

    public trackRankingEntry(index: number, item: RankingEntry): string {
        return item.user_id || `${index}`;
    }

    public trackCalendarCell(index: number, item: CalendarCell): string {
        return item.key || `${index}`;
    }

    public trackCalendarRun(index: number, item: CalendarRunDetail): string {
        return item.id || `${this.selectedCalendarDate || 'date'}-${index}`;
    }

    public trackJournalRun(index: number, item: RunRecord): string {
        return item.id || `${item.date}-${index}`;
    }

    public trackRunMedia(index: number, item: RunMedia): string {
        return item.id || `${item.media_url}-${index}`;
    }

    public trackMusicTrack(index: number, item: MusicTrack): string {
        return item.id || `${item.title}-${item.artist}-${index}`;
    }

    public trackRunRecord(index: number, item: RunRecord): string {
        return item.id || `${item.date}-${index}`;
    }

    public trackBadge(index: number, item: Badge): string {
        return item.code || `${index}`;
    }

    public trackWeatherHour(index: number, item: WeatherHourly): string {
        return `${item.time}-${index}`;
    }

    public trackWeightLog(index: number, item: WeightLog): string {
        return item.date || item.id || `${index}`;
    }

    public trackTrendPoint(index: number, item: TrendPoint): string {
        return item.id || `${index}`;
    }

    public trackTrendSegment(index: number, item: TrendSegment): string {
        return item.id || `${index}`;
    }

    public trackWeightRunBar(index: number, item: WeightRunBar): string {
        return item.id || `${index}`;
    }

    public trackWeightContextStat(index: number, item: WeightContextStat): string {
        return item.id || `${index}`;
    }

    public trackChart(index: number, item: ChartCard): string {
        return item.title || `${index}`;
    }

    public trackTrainingLoadZone(index: number, item: TrainingLoadZone): string {
        return item.id || `${index}`;
    }

    public trackRunType(index: number, item: RunTypeOption): string {
        return item.id || `${index}`;
    }

    public trackRunTypeSummary(index: number, item: RunTypeSummary): string {
        return item.id || `${index}`;
    }

    public trackCyclePhase(index: number, item: CyclePhaseOption): string {
        return item.id || `${index}`;
    }

    public trackCycleCondition(index: number, item: CycleConditionOption): string {
        return item.emoji || `${index}`;
    }

    public trackCycleFlow(index: number, item: CycleFlowOption): string {
        return item.id || `${index}`;
    }

    public trackCycleLog(index: number, item: CycleLog): string {
        return item.id || `${item.start_date}-${index}`;
    }

    public trackConditionItem(index: number, item: ConditionDistributionItem): string {
        return item.emoji || `${index}`;
    }

    public trackCyclePattern(index: number, item: CyclePatternStat): string {
        return item.phase || `${index}`;
    }

    public trackGallery(index: number, item: GalleryItem): string {
        return item.id || `${item.km}-${index}`;
    }

    public trackGalleryStat(index: number, item: GalleryStat): string {
        return item.label || `${index}`;
    }

    public trackChat(index: number, item: ChatMessage): string {
        return `${item.sender}-${index}`;
    }

    public trackChatSession(index: number, item: ChatSession): string {
        return item.id || `${index}`;
    }

    public trackChatHistoryGroup(index: number, item: ChatHistoryGroup): string {
        return item.label || `${index}`;
    }

    public runTypeLabel(runType?: string | null): string {
        const normalized = this.normalizeRunType(runType);
        return [...RUN_TYPE_OPTIONS, ...SUPPORT_ACTIVITY_OPTIONS].find((item) => item.id === normalized)?.label || '조깅';
    }

    public runTypeClass(runType?: string | null): string {
        const normalized = this.normalizeRunType(runType);
        return `run-type-chip run-type-${normalized}`;
    }

    public isSupportActivityRunType(runType?: string | null): boolean {
        return SUPPORT_ACTIVITY_TYPES.has(this.normalizeRunType(runType));
    }

    public badgeIconClass(badge?: Badge | null): string {
        const icon = badge?.icon || 'fa-medal';
        return icon.includes('fa-') ? icon : 'fa-medal';
    }

    public challengeTypeLabel(type?: ChallengeType | string | null): string {
        return CHALLENGE_TYPE_OPTIONS.find((item) => item.id === type)?.label || '챌린지';
    }

    public rankingAvatarText(name?: string | null): string {
        return this.avatarText(name);
    }

    private rankingEntryToSocialProfile(entry: RankingEntry): SocialProfile {
        return {
            id: entry.user_id,
            email: '',
            display_id: entry.display_id || entry.name || entry.user_id,
            name: entry.name || '러너',
            running_start_date: this.todayDateKey,
            profile_image: entry.profile_image || '',
            is_public: entry.privacy !== 'private',
            is_me: Boolean(entry.is_viewer),
            is_following: Boolean(entry.is_following),
            is_follower: Boolean(entry.is_follower),
            is_mutual: Boolean(entry.is_mutual),
            following_count: 0,
            follower_count: 0,
            stats_public: false,
            stats: null,
            badges_public: false,
            badges: [],
            earned_badge_count: 0,
            total_badge_count: 0,
            achievement_rate: 0
        };
    }

    public avatarText(name?: string | null): string {
        const text = String(name || '').trim();
        return text ? text.slice(0, 1) : 'R';
    }

    public rankingRankClass(entry: RankingEntry): string {
        return entry.medal ? `ranking-rank ${entry.medal}` : 'ranking-rank';
    }

    public mediaTypeLabel(mediaType?: string | null): string {
        return mediaType === 'video' ? '영상' : '사진';
    }

    public mediaAltText(media?: RunMedia | null): string {
        return media ? `러닝 첨부 ${this.mediaTypeLabel(media.media_type)}` : '러닝 첨부 미디어';
    }

    public myFeedUser(): FeedUser {
        return {
            id: this.profile?.id || '',
            name: this.profile?.name || '나',
            display_id: this.myProfileDisplayIdText,
            profile_image: this.profile?.profile_image || '',
            is_me: true
        };
    }

    public socialProfileFeedUser(profile: SocialProfile): FeedUser {
        return {
            id: profile.id,
            name: profile.name || '러너',
            display_id: profile.display_id || profile.id,
            profile_image: profile.profile_image || '',
            is_me: Boolean(profile.is_me)
        };
    }

    public formatWaterMl(value?: number | null): string {
        return value ? `${value}ml` : '-';
    }

    public runHydrationText(run?: CalendarRunDetail | RunRecord | null): string {
        const source = run ? run as unknown as Record<string, unknown> : {};
        const before = this.normalizeWaterMl(source['waterBeforeMl'] ?? source['water_before_ml']);
        const after = this.normalizeWaterMl(source['waterAfterMl'] ?? source['water_after_ml']);
        const total = (before || 0) + (after || 0);
        if (!total) return '수분 기록 없음';
        return `전 ${this.formatWaterMl(before)} · 후 ${this.formatWaterMl(after)} · 총 ${total}ml`;
    }

    public journalPreviewText(value?: string | null): string {
        return String(value || '').replace(/\s+/g, ' ').trim();
    }

    public isRunMediaUploading(runId: string): boolean {
        return this.uploadingMediaRunId === runId;
    }

    private applyProfilePayload(source: unknown): boolean {
        const profile = this.normalizeProfile(source as Partial<UserProfile> | null | undefined);
        if (!profile.id) return false;

        this.profile = profile;
        this.syncWeightTargetLocalForProfile();
        this.syncPacerPersonaLocalForProfile();
        this.applyCyclePreferenceFromProfile(profile);
        if (!profile.onboarded) {
            this.openOnboarding(profile);
        }
        return true;
    }

    private async loadProfile(): Promise<void> {
        try {
            const result = await apiFetch<UserProfile>('/api/profile', { retries: 0, timeoutMs: 8000 });
            if (!result.success || !result.data) return;

            this.applyProfilePayload(result.data);
        } catch {
            return;
        } finally {
            this.cdr.detectChanges();
        }
    }

    private normalizeProfile(source: Partial<UserProfile> | null | undefined): UserProfile {
        const raw = (source || {}) as Record<string, unknown>;
        return {
            id: typeof source?.id === 'string' ? source.id : '',
            username: typeof source?.username === 'string' ? source.username : '',
            display_id: typeof source?.display_id === 'string' ? source.display_id : '',
            display_name: typeof source?.display_name === 'string' ? source.display_name : '',
            email: typeof source?.email === 'string' ? source.email : '',
            name: typeof source?.name === 'string' ? source.name : '',
            gender: this.normalizeGender(source?.gender),
            mobile: typeof source?.mobile === 'string' ? source.mobile : '',
            running_start_date: this.normalizeDateKey(source?.running_start_date) || this.dateKey(new Date()),
            profile_image: typeof source?.profile_image === 'string' ? source.profile_image : '',
            onboarded: Boolean(source?.onboarded),
            is_public: source?.is_public !== false,
            cycle_enabled: raw['cycle_enabled'] === true || raw['cycleEnabled'] === true,
            cycle_enabled_configured: raw['cycle_enabled_configured'] === true || raw['cycleEnabledConfigured'] === true
        };
    }

    private profileEditDraftFromProfile(profile: UserProfile | null): ProfileEditDraft {
        return {
            name: profile?.name || '',
            mobile: profile?.mobile || '',
            running_start_date: this.effectiveRunningStartDate(profile),
            profile_image: profile?.profile_image || '',
            is_public: profile?.is_public !== false
        };
    }

    private applyCycleAvailability(): void {
        if (this.shouldShowCycleFeature) return;

        this.isCycleFeatureEnabled = false;
        this.cycleLogs = [];
        this.cycleSummary = { ...EMPTY_CYCLE_SUMMARY };
        this.cycleDayMap.clear();
        this.cyclePatternStats = [];
        this.cycleStatus = '';
        this.persistCycleLocalSettings();
        this.refreshDerivedState();
    }

    private applyCyclePreferenceFromProfile(profile: UserProfile): void {
        if (!this.shouldShowCycleFeature) {
            this.applyCycleAvailability();
            return;
        }

        if (profile.cycle_enabled_configured) {
            this.isCycleFeatureEnabled = profile.cycle_enabled === true;
        } else if (this.isCycleFeatureEnabled) {
            void this.saveCycleFeaturePreference(true, true);
        }

        if (!this.isCycleFeatureEnabled) {
            this.cycleLogs = [];
            this.cycleSummary = { ...EMPTY_CYCLE_SUMMARY };
            this.cycleDayMap.clear();
            this.cyclePatternStats = [];
            this.cycleStatus = '';
        }

        this.persistCycleLocalSettings();
        this.syncCycleDraftWithSelectedDate();
        this.refreshDerivedState();
    }

    private async saveCycleFeaturePreference(enabled: boolean, silent: boolean = false): Promise<boolean> {
        try {
            const result = await jsonRequest<UserProfile>('/api/profile', 'PATCH', {
                cycle_enabled: enabled
            }, { retries: 0, timeoutMs: 8000 });

            if (!result.success) {
                if (!silent) {
                    this.cycleStatus = apiErrorMessage(result.error) || result.message || '생리주기 설정을 저장하지 못했어.';
                }
                return false;
            }

            const profile = this.normalizeProfile(result.data as Partial<UserProfile>);
            if (profile.id) {
                this.profile = profile;
            } else if (this.profile) {
                this.profile = {
                    ...this.profile,
                    cycle_enabled: enabled,
                    cycle_enabled_configured: true
                };
            }
            return true;
        } catch {
            if (!silent) {
                this.cycleStatus = '생리주기 설정을 저장하지 못했어.';
            }
            return false;
        }
    }

    private effectiveRunningStartDate(profile: UserProfile | null): string {
        return this.firstRunDate() || profile?.running_start_date || this.todayDateKey;
    }

    private firstRunDate(): string {
        return this.runs.reduce((firstDate, run) => {
            if (!run.date) return firstDate;
            return !firstDate || run.date < firstDate ? run.date : firstDate;
        }, '');
    }

    private openOnboarding(profile: UserProfile): void {
        this.onboardingProfile = {
            name: profile.name || '',
            running_start_date: profile.running_start_date || this.dateKey(new Date()),
            profile_image: profile.profile_image || '',
            gender: this.normalizeGender(profile.gender)
        };
        this.onboardingGoalKm = 30;
        this.onboardingIndex = 0;
        this.onboardingStatus = '';
        this.isOnboardingSaving = false;
        this.isOnboardingSkipConfirmVisible = false;
        this.notificationPermissionState = this.readNotificationPermission();
        this.applyOnboardingScreen();
        this.isOnboardingVisible = true;
    }

    private readNotificationPermission(): NotificationPermission | 'unsupported' {
        if (typeof window === 'undefined' || !('Notification' in window)) return 'unsupported';
        return Notification.permission;
    }

    private moveOnboardingTo(index: number): void {
        this.onboardingIndex = Math.max(0, Math.min(index, this.onboardingSteps.length - 1));
        this.onboardingStatus = '';
        this.applyOnboardingScreen();
    }

    private applyOnboardingScreen(): void {
        const screen = this.onboardingScreenMap[this.currentOnboardingStep.id];
        if (!screen) return;
        this.activeScreen = screen;
    }

    private validateOnboardingStep(): boolean {
        const stepId = this.currentOnboardingStep.id;
        if (stepId === 'profile') {
            const name = this.onboardingProfile.name.trim();
            const startDate = this.normalizeDateKey(this.onboardingProfile.running_start_date);
            const genderChoice = String(this.onboardingProfile.gender || '').trim();
            const gender = genderChoice === 'unspecified' ? 'unspecified' : this.normalizeGender(genderChoice);
            if (!name) {
                this.onboardingStatus = '닉네임을 입력해줘.';
                return false;
            }
            if (!startDate) {
                this.onboardingStatus = '러닝 시작일을 선택해줘.';
                return false;
            }
            if (startDate > this.todayDateKey) {
                this.onboardingStatus = '러닝 시작일은 오늘 이전 날짜로 선택해줘.';
                return false;
            }
            if (!gender) {
                this.onboardingStatus = '생리주기와 맞춤 기능을 위해 성별을 선택해줘.';
                return false;
            }
            this.onboardingProfile.name = name;
            this.onboardingProfile.running_start_date = startDate;
            this.onboardingProfile.gender = gender;
        }

        if (stepId === 'goal' && (!Number.isFinite(this.onboardingGoalKm) || this.onboardingGoalKm <= 0)) {
            this.onboardingStatus = '첫 월 목표 거리를 선택해줘.';
            return false;
        }

        return true;
    }

    private async finishOnboarding(skipGuide: boolean = false): Promise<void> {
        if (this.isOnboardingSaving) return;
        if (!skipGuide && !this.validateOnboardingStep()) return;

        this.isOnboardingSaving = true;
        this.onboardingStatus = skipGuide ? '온보딩 건너뛰는 중' : '온보딩 저장 중';
        this.cdr.detectChanges();

        try {
            if (!skipGuide) {
                const goalSaved = await this.saveOnboardingGoal();
                if (!goalSaved) return;
            }

            const profileStepIndex = this.onboardingSteps.findIndex((step) => step.id === 'profile');
            const shouldSaveProfile = !skipGuide || (profileStepIndex >= 0 && this.onboardingIndex > profileStepIndex);
            const profilePayload: Record<string, unknown> = { onboarded: true };
            if (shouldSaveProfile) {
                profilePayload['name'] = this.onboardingProfile.name.trim();
                profilePayload['running_start_date'] = this.onboardingProfile.running_start_date;
                profilePayload['profile_image'] = this.onboardingProfile.profile_image;
                if (this.onboardingProfile.gender !== 'unspecified') {
                    profilePayload['gender'] = this.onboardingProfile.gender;
                }
            }

            const result = await jsonRequest<UserProfile>('/api/profile', 'PATCH', profilePayload, { retries: 0, timeoutMs: 10000 });
            if (!result.success || !result.data) {
                this.onboardingStatus = result.error?.message || result.message || (skipGuide ? '온보딩 건너뛰기를 저장하지 못했어.' : '온보딩 완료 정보를 저장하지 못했어.');
                return;
            }

            this.profile = this.normalizeProfile(result.data);
            this.applyCyclePreferenceFromProfile(this.profile);
            this.syncPacerPersonaLocalForProfile();
            this.isOnboardingVisible = false;
            this.isOnboardingSkipConfirmVisible = false;
            this.onboardingStatus = '';
            this.showToast(skipGuide ? '온보딩을 건너뛰었어.' : '온보딩을 완료했어.', 'success');
        } catch {
            this.onboardingStatus = skipGuide ? '온보딩 건너뛰기 중 오류가 발생했어.' : '온보딩 저장 중 오류가 발생했어.';
        } finally {
            this.isOnboardingSaving = false;
            this.cdr.detectChanges();
        }
    }

    private async saveOnboardingGoal(): Promise<boolean> {
        try {
            const targetMonth = this.todayDateKey.slice(0, 7);
            const response = await fetch(`/api/goals/${encodeURIComponent(targetMonth)}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    goal_type: 'distance',
                    target_value: this.onboardingGoalKm
                })
            });
            const payload = await response.json().catch(() => null);
            if (!response.ok || !payload?.success) {
                this.onboardingStatus = payload?.message || '첫 목표를 저장하지 못했어.';
                return false;
            }

            this.activeYearMonth = targetMonth;
            this.applyGoalsPayload(payload);
            return true;
        } catch {
            this.onboardingStatus = '첫 목표 저장 중 오류가 발생했어.';
            return false;
        }
    }

    private runsUrl(options: { limit?: number; fields?: string[]; includeMedia?: boolean } = {}): string {
        const params = new URLSearchParams();
        if (options.limit) params.set('limit', String(options.limit));
        if (options.fields?.length) params.set('fields', options.fields.join(','));
        if (options.includeMedia === false) params.set('include_media', 'false');
        if (options.includeMedia === true) params.set('include_media', 'true');
        const query = params.toString();
        return query ? `/api/runs?${query}` : '/api/runs';
    }

    private initialRunsUrl(): string {
        return this.runsUrl({
            limit: this.initialDashboardRunLimit,
            fields: this.initialRunFields,
            includeMedia: false
        });
    }

    private async loadDashboardBootstrap(): Promise<'loaded' | 'unauthenticated' | 'failed'> {
        const result = await apiFetch<DashboardBootstrapData>(
            `/api/dashboard/bootstrap?limit=${encodeURIComponent(String(this.initialDashboardRunLimit))}`,
            { retries: 0, timeoutMs: 8000 }
        );
        if (!result.success) {
            if (result.error?.status === 401) return 'unauthenticated';
            this.initialErrorMessage = result.error?.message || '초기 데이터를 불러오지 못했어.';
            return 'failed';
        }

        const data = (result.data || {}) as DashboardBootstrapData;
        const rows = Array.isArray(data.runs) ? data.runs : [];
        this.applyProfilePayload(data.profile || null);
        this.initialRunsTruncated = Boolean(data.has_more_runs);
        this.runMediaLoaded = false;
        if (data.has_media_history) {
            this.markMediaAccessNoticeAccepted();
        }
        this.setRuns(rows, { loadRelatedData: false });
        return 'loaded';
    }

    private async loadRuns(
        markInitialError: boolean = false,
        includeTrainingLoad: boolean = true,
        loadRelatedData: boolean = true,
        url: string = '/api/runs',
        includesMedia: boolean = true
    ): Promise<boolean> {
        const result = await apiFetch<any[]>(url);
        if (result.success) {
            const payload = result.raw as any;
            const rows = Array.isArray(payload) ? payload : Array.isArray(result.data) ? result.data : [];
            this.runMediaLoaded = includesMedia;
            this.setRuns(rows, { loadRelatedData });
            if (includeTrainingLoad) {
                await this.loadTrainingLoad();
            }
            return true;
        }

        if (markInitialError) {
            this.setRuns([], { loadRelatedData: false });
            if (result.error?.status === 401) {
                this.redirectToAccess();
                return false;
            }
            this.initialErrorMessage = apiErrorMessage(result.error);
        }
        if (includeTrainingLoad) {
            await this.loadTrainingLoad();
        }
        return false;
    }

    private async loadBadges(): Promise<void> {
        const result = await apiFetch<any[]>('/api/badges');
        if (!result.success) {
            this.setBadges([]);
            return;
        }

        const payload = result.raw as any;
        const rows = Array.isArray(payload) ? payload : Array.isArray(result.data) ? result.data : [];
        this.setBadges(rows);
    }

    private async loadRestDays(): Promise<void> {
        const result = await apiFetch<any[]>('/api/rest-days');
        if (!result.success) {
            this.setRestDays([]);
            return;
        }

        const payload = result.raw as any;
        const rows = Array.isArray(payload) ? payload : Array.isArray(result.data) ? result.data : [];
        this.setRestDays(rows);
    }

    private async loadTrainingLoad(): Promise<void> {
        const result = await apiFetch<any>('/api/training-load');
        if (result.success) {
            this.trainingLoad = this.normalizeTrainingLoad(result.raw);
        } else {
            this.trainingLoad = { ...EMPTY_TRAINING_LOAD };
        }
        this.cdr.detectChanges();
    }

    private async saveRestDay(date: string, rest: boolean): Promise<boolean> {
        const result = await jsonRequest<any[]>('/api/rest-days', 'POST', { date, rest });
        if (!result.success) {
            this.showToast(result.error?.message || '휴식일을 저장하지 못했어.', 'error');
            return false;
        }

        this.selectedCalendarDate = date;
        this.setRestDays(Array.isArray(result.data) ? result.data : []);
        return true;
    }

    private loadRestBannerDismissed(): void {
        try {
            this.isRestBannerDismissed = window.localStorage.getItem(this.restBannerDismissKey(this.todayDateKey)) === '1';
        } catch {
            this.isRestBannerDismissed = false;
        }
    }

    private restBannerDismissKey(date: string): string {
        return `${this.restBannerDismissStorageKey}:${date}`;
    }

    private async loadDayNotes(): Promise<void> {
        const result = await apiFetch<any[]>('/api/day-notes');
        if (!result.success) {
            this.setDayNotes([]);
            return;
        }

        const payload = result.raw as any;
        const rows = Array.isArray(payload) ? payload : Array.isArray(result.data) ? result.data : [];
        this.setDayNotes(rows);
    }

    private async loadWeights(): Promise<void> {
        const result = await apiFetch<any[]>('/api/weights?period=all');
        if (!result.success) {
            this.setWeights([]);
            return;
        }

        const payload = result.raw as any;
        const rows = Array.isArray(payload)
            ? payload
            : Array.isArray(payload?.weights)
                ? payload.weights
                : Array.isArray(payload?.data?.weights)
                    ? payload.data.weights
                    : Array.isArray(result.data) ? result.data : [];
        this.setWeights(rows);
        this.applyWeightSettings(payload?.settings || payload?.data?.settings || payload?.data || result.data);
    }

    private async loadGoalsForActiveMonth(): Promise<void> {
        const targetMonth = this.activeYearMonth;
        const result = await apiFetch<any>(`/api/goals/${encodeURIComponent(targetMonth)}`);
        if (targetMonth !== this.activeYearMonth) return;
        if (result.success) {
            this.applyGoalsPayload(result.raw);
        } else {
            if (targetMonth !== this.activeYearMonth) return;
            this.goals = [];
            this.goalProgressCards = [];
            this.goalHistory = [];
            this.syncGoalDrafts();
            this.refreshDerivedState();
            this.cdr.detectChanges();
        }
    }

    private async loadChallenges(): Promise<void> {
        if (this.isChallengeLoading) return;

        this.isChallengeLoading = true;
        try {
            const result = await apiFetch<any>('/api/challenges');
            if (result.success) {
                this.applyChallengesPayload(result.raw);
            } else {
                this.setChallenges([]);
            }
        } finally {
            this.isChallengeLoading = false;
            this.cdr.detectChanges();
        }
    }

    private async loadFeed(showLoading: boolean = true): Promise<void> {
        if (this.isFeedLoading) return;

        this.isFeedLoading = showLoading;
        if (showLoading && !this.feedItems.length) {
            this.feedStatus = '피드 불러오는 중';
        }
        this.cdr.detectChanges();

        try {
            const result = await apiFetch<any>('/api/feed');
            if (!result.success) {
                this.feedStatus = result.error?.message || '피드를 불러오지 못했어.';
                this.feedItems = [];
                return;
            }

            const payload = result.raw as any;
            const rows = Array.isArray(payload) ? payload : Array.isArray(result.data) ? result.data : [];
            this.setFeedItems(rows);
            this.feedStatus = '';
        } catch {
            this.feedStatus = '인터넷 연결을 확인해줘';
            this.feedItems = [];
        } finally {
            this.isFeedLoading = false;
            this.cdr.detectChanges();
        }
    }

    private async loadProfileFeedSocial(runId: string): Promise<void> {
        if (!runId || this.isProfileFeedSocialLoading) return;

        this.isProfileFeedSocialLoading = true;
        this.profileFeedSocialStatus = '';
        this.cdr.detectChanges();

        try {
            const result = await apiFetch<any>(`/api/runs/${encodeURIComponent(runId)}/reactions`);
            if (!result.success) {
                this.profileFeedSocialStatus = result.error?.message || '좋아요와 댓글을 불러오지 못했어.';
                return;
            }

            const payload = result.raw as any;
            this.applyFeedSocial(runId, payload?.social || payload?.data || result.data || payload);
        } catch {
            this.profileFeedSocialStatus = '인터넷 연결을 확인해줘';
        } finally {
            this.isProfileFeedSocialLoading = false;
            this.cdr.detectChanges();
        }
    }

    private async loadCommunityNotifications(showLoading: boolean = true): Promise<void> {
        if (this.isCommunityNotificationLoading) return;

        this.isCommunityNotificationLoading = showLoading;
        this.cdr.detectChanges();

        try {
            const result = await apiFetch<any[]>('/api/notifications?limit=5');
            if (result.success) {
                this.communityNotifications = this.normalizeCommunityNotifications(result.data);
            }
        } finally {
            this.isCommunityNotificationLoading = false;
            this.cdr.detectChanges();
        }
    }

    private async loadFriendLists(showLoading: boolean = true): Promise<void> {
        if (this.isFriendListLoading) return;

        this.isFriendListLoading = showLoading;
        if (showLoading && !this.activeFriendList.length) {
            this.friendStatus = '친구 목록 불러오는 중';
        }
        this.cdr.detectChanges();

        try {
            const [followingResult, followersResult] = await Promise.all([
                apiFetch<any[]>('/api/follows/following'),
                apiFetch<any[]>('/api/follows/followers')
            ]);

            if (!followingResult.success) {
                this.friendStatus = followingResult.error?.message || '팔로잉 목록을 불러오지 못했어.';
                return;
            }
            if (!followersResult.success) {
                this.friendStatus = followersResult.error?.message || '팔로워 목록을 불러오지 못했어.';
                return;
            }

            this.followingUsers = this.normalizeSocialProfiles(followingResult.data);
            this.followerUsers = this.normalizeSocialProfiles(followersResult.data);
            this.syncSelectedFriendProfile();
            this.friendStatus = '';
        } catch {
            this.friendStatus = '인터넷 연결을 확인해줘';
        } finally {
            this.isFriendListLoading = false;
            this.cdr.detectChanges();
        }
    }

    private async loadViewedProfile(userId: string): Promise<void> {
        if (!userId || this.isViewedProfileLoading) return;

        this.isViewedProfileLoading = true;
        this.viewedProfileStatus = '프로필 불러오는 중';
        this.cdr.detectChanges();

        try {
            const result = await apiFetch<any>(`/api/follows/${encodeURIComponent(userId)}`);
            if (!result.success) {
                this.viewedProfileStatus = this.viewedProfile?.id === userId
                    ? ''
                    : result.error?.message || '프로필을 불러오지 못했어.';
                return;
            }

            const detail = this.normalizeSocialProfileDetail(result.data);
            if (!detail) {
                this.viewedProfileStatus = this.viewedProfile?.id === userId ? '' : '프로필을 불러오지 못했어.';
                return;
            }

            this.viewedProfile = detail.profile;
            this.applySocialProfileUpdate(detail.profile);
            this.viewedProfileFollowingUsers = detail.following;
            this.viewedProfileFollowerUsers = detail.followers;
            this.viewedProfileMediaItems = detail.media;
            this.viewedProfileListsPublic = detail.lists_public;
            this.viewedProfileStatus = '';
        } catch {
            this.viewedProfileStatus = this.viewedProfile?.id === userId ? '' : '인터넷 연결을 확인해줘';
        } finally {
            this.isViewedProfileLoading = false;
            this.cdr.detectChanges();
        }
    }

    private async loadRanking(): Promise<void> {
        if (this.isRankingLoading) return;

        this.isRankingLoading = true;
        this.rankingStatus = this.rankingEntries.length ? '' : '랭킹 불러오는 중';
        this.cdr.detectChanges();

        try {
            const result = await apiFetch<any>(`/api/ranking/weekly?period=${encodeURIComponent(this.activeRankingPeriod)}&scope=${encodeURIComponent(this.activeRankingScope)}`);
            if (!result.success) {
                this.rankingStatus = result.error?.message || '랭킹을 불러오지 못했어.';
                return;
            }

            this.applyRankingPayload(result.data || result.raw);
            this.rankingStatus = '';
        } catch {
            this.rankingStatus = '인터넷 연결을 확인해줘';
        } finally {
            this.isRankingLoading = false;
            this.cdr.detectChanges();
        }
    }

    private async joinChallenge(payload: { invite_code?: string; challenge_id?: string }): Promise<void> {
        if (this.isChallengeJoining) return;

        const inviteCode = (payload.invite_code || '').trim();
        const challengeId = (payload.challenge_id || '').trim();
        if (!inviteCode && !challengeId) {
            this.challengeStatus = '초대코드를 입력해줘.';
            this.cdr.detectChanges();
            return;
        }

        this.isChallengeJoining = true;
        this.challengeStatus = '챌린지 참여 중';
        this.cdr.detectChanges();

        try {
            const response = await fetch('/api/challenges/join', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(inviteCode ? { invite_code: inviteCode } : { challenge_id: challengeId })
            });
            const result = await response.json().catch(() => null);
            if (!result?.success) {
                this.challengeStatus = result?.message || '챌린지에 참여하지 못했어.';
                return;
            }

            this.applyChallengesPayload(result);
            const joined = this.normalizeChallenge(result.data);
            if (joined) {
                this.selectedChallengeId = joined.id;
                this.activeChallengeTab = 'joined';
                this.challengeViewMode = 'detail';
            }
            this.challengeInviteCode = '';
            this.challengeStatus = '';
            this.showToast('챌린지에 참여했어.', 'success');
        } catch {
            this.challengeStatus = '챌린지 참여 중 오류가 발생했어.';
        } finally {
            this.isChallengeJoining = false;
            this.cdr.detectChanges();
        }
    }

    private async loadCycles(): Promise<void> {
        if (!this.shouldShowCycleFeature || !this.isCycleFeatureEnabled) {
            this.setCycles([], EMPTY_CYCLE_SUMMARY);
            return;
        }

        try {
            const response = await fetch(resolveApiUrl('/api/cycles?enabled=1'), {
                headers: this.cycleRequestHeaders()
            });
            const payload = await response.json();
            const rows = Array.isArray(payload) ? payload : Array.isArray(payload?.data) ? payload.data : [];
            this.setCycles(rows, payload?.summary);
            this.cycleStatus = rows.length ? '' : '생리 기록 없음';
        } catch {
            this.setCycles([], EMPTY_CYCLE_SUMMARY);
            this.cycleStatus = '주기 데이터를 불러오지 못했어.';
        }
    }

    private async loadWeatherForActiveMonth(): Promise<void> {
        const targetMonth = this.activeYearMonth;
        const requestSeq = ++this.weatherRequestSeq;
        this.isWeatherLoading = true;
        this.weatherStatus = '';
        this.cdr.detectChanges();

        try {
            await this.refreshWeatherPositionIfAlreadyGranted();
            const params = new URLSearchParams({ year_month: targetMonth });
            if (this.weatherPosition) {
                params.set('lat', String(this.weatherPosition.lat));
                params.set('lon', String(this.weatherPosition.lon));
                params.set('location_source', 'browser');
            }

            const result = await apiFetch<WeatherResponseData>(`/api/weather/monthly?${params.toString()}`, {
                retries: 0,
                timeoutMs: 7000
            });
            if (requestSeq !== this.weatherRequestSeq || targetMonth !== this.activeYearMonth) return;

            if (!result.success || !result.data) {
                this.weatherDays = new Map();
                this.weatherCoverage = null;
                this.weatherStatus = result.error?.message || '날씨 정보 없음';
                this.weatherLocationText = '';
                this.weatherUpdatedText = '';
                this.refreshDerivedState();
                return;
            }

            this.setWeatherDays(result.data);
        } catch {
            if (requestSeq !== this.weatherRequestSeq || targetMonth !== this.activeYearMonth) return;

            this.weatherDays = new Map();
            this.weatherCoverage = null;
            this.weatherStatus = '날씨 정보 없음';
            this.weatherLocationText = '';
            this.weatherUpdatedText = '';
            this.refreshDerivedState();
        } finally {
            if (this.isInitialLoading) {
                this.clearInitialLoadingStep('location');
                this.clearInitialLoadingStep('weather');
            }
            if (requestSeq === this.weatherRequestSeq) {
                this.lastWeatherLoadedAt = Date.now();
                this.isWeatherLoading = false;
                this.cdr.detectChanges();
            }
        }
    }

    private startWeatherAutoRefresh(): void {
        if (typeof window === 'undefined') return;
        if (this.weatherRefreshTimer !== null) return;

        this.weatherRefreshTimer = window.setInterval(() => {
            this.refreshWeatherIfStale();
        }, this.weatherRefreshIntervalMs);

        if (typeof document !== 'undefined') {
            const handleVisibilityChange = (): void => {
                if (document.visibilityState === 'visible') {
                    this.refreshWeatherIfStale();
                }
            };
            document.addEventListener('visibilitychange', handleVisibilityChange);
            this.cleanupHandlers.push(() => document.removeEventListener('visibilitychange', handleVisibilityChange));
        }
    }

    private refreshWeatherIfStale(): void {
        if (this.isWeatherLoading) return;
        if (Date.now() - this.lastWeatherLoadedAt < this.weatherRefreshIntervalMs) return;

        void this.loadWeatherForActiveMonth();
    }

    private async refreshWeatherPositionIfAlreadyGranted(): Promise<void> {
        if (typeof navigator === 'undefined' || !navigator.geolocation) return;

        const permissions = (navigator as any).permissions;
        if (!permissions || typeof permissions.query !== 'function') return;

        try {
            const status = await permissions.query({ name: 'geolocation' });
            if (status?.state !== 'granted') return;
        } catch {
            return;
        }

        try {
            const position = await this.requestCurrentWeatherPosition();
            this.weatherPosition = position;
            this.storeWeatherPosition(position);
        } catch {
            return;
        }
    }

    private requestCurrentWeatherPosition(): Promise<WeatherPosition> {
        return new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = Number(position.coords.latitude);
                    const lon = Number(position.coords.longitude);
                    if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
                        reject(new Error('현재 위치를 확인하지 못했어.'));
                        return;
                    }
                    resolve({
                        lat: Math.round(lat * 100000) / 100000,
                        lon: Math.round(lon * 100000) / 100000
                    });
                },
                (error) => {
                    if (error.code === error.PERMISSION_DENIED) {
                        reject(new Error('위치 권한이 허용되지 않았어.'));
                    } else if (error.code === error.TIMEOUT) {
                        reject(new Error('위치 확인 시간이 초과됐어.'));
                    } else {
                        reject(new Error('현재 위치를 확인하지 못했어.'));
                    }
                },
                {
                    enableHighAccuracy: false,
                    maximumAge: 15 * 60 * 1000,
                    timeout: 8000
                }
            );
        });
    }

    private readStoredWeatherPosition(): WeatherPosition | null {
        if (typeof window === 'undefined' || !window.localStorage) return null;

        try {
            const raw = window.localStorage.getItem(this.weatherPositionStorageKey);
            if (!raw) return null;
            const parsed = JSON.parse(raw);
            const lat = Number(parsed?.lat);
            const lon = Number(parsed?.lon);
            if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
            return { lat, lon };
        } catch {
            return null;
        }
    }

    private storeWeatherPosition(position: WeatherPosition): void {
        if (typeof window === 'undefined' || !window.localStorage) return;

        try {
            window.localStorage.setItem(this.weatherPositionStorageKey, JSON.stringify(position));
        } catch {
            return;
        }
    }

    private hasAcceptedMediaAccessNotice(): boolean {
        if (this.hasUploadedMediaHistory()) return true;
        if (typeof window === 'undefined' || !window.localStorage) return false;

        try {
            return window.localStorage.getItem(this.mediaAccessNoticeAcceptedKey) === '1';
        } catch {
            return false;
        }
    }

    private markMediaAccessNoticeAccepted(): void {
        if (typeof window === 'undefined' || !window.localStorage) return;

        try {
            window.localStorage.setItem(this.mediaAccessNoticeAcceptedKey, '1');
        } catch {
            return;
        }
    }

    private hasUploadedMediaHistory(): boolean {
        return this.runs.some((run) => Boolean(run.image_url) || Boolean(run.media?.length));
    }

    private aiUsagePeriodText(remaining: number | null, limit: number, label: string): string {
        if (!limit) return `${label} 제한 없음`;
        const safeRemaining = Math.max(0, Math.round(remaining ?? limit));
        return `${label} ${safeRemaining}/${limit}회`;
    }

    private applyAiUsage(row: unknown, notify: boolean = false): void {
        const usage = this.normalizeAiUsage(row);
        if (!usage) return;

        this.aiUsage = usage;
        if (notify) {
            this.notifyAiUsageLimit(usage);
        }
    }

    private notifyAiUsageLimit(usage: AiUsage | null): void {
        const message = this.aiUsageLimitNotice(usage);
        if (!message || !usage) return;
        this.showToast(message, usage.allowed ? 'info' : 'error');
    }

    private aiUsageLimitNotice(usage: AiUsage | null): string {
        if (!usage) return '';
        if (!usage.allowed && usage.message) return usage.message;
        if (usage.reason === 'monthly_limit' || usage.monthly_remaining === 0) {
            return '이번 달 페이서 AI 한도를 모두 사용했어. 다음 달에 다시 이용해줘.';
        }
        if (usage.reason === 'daily_limit' || usage.daily_remaining === 0) {
            return '오늘 페이서 AI 한도를 모두 사용했어. 내일 다시 이용해줘.';
        }
        return '';
    }

    private normalizeAiUsage(row: unknown): AiUsage | null {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : null;
        if (!source) return null;

        const dailyLimit = this.usageLimitValue(source['daily_limit'] ?? source['dailyLimit'], DEFAULT_AI_CHAT_DAILY_LIMIT);
        const monthlyLimit = this.usageLimitValue(source['monthly_limit'] ?? source['monthlyLimit'], DEFAULT_AI_CHAT_MONTHLY_LIMIT);
        const dailyCount = this.usageCountValue(source['daily_count'] ?? source['dailyCount']);
        const monthlyCount = this.usageCountValue(source['monthly_count'] ?? source['monthlyCount']);
        const dailyRemaining = this.usageRemainingValue(source['daily_remaining'] ?? source['dailyRemaining'], dailyLimit, dailyCount);
        const monthlyRemaining = this.usageRemainingValue(source['monthly_remaining'] ?? source['monthlyRemaining'], monthlyLimit, monthlyCount);
        const reason = typeof source['reason'] === 'string' ? source['reason'] : '';

        return {
            allowed: source['allowed'] !== false,
            reason,
            message: typeof source['message'] === 'string' ? source['message'] : '',
            action: typeof source['action'] === 'string' ? source['action'] : 'chat',
            day_key: typeof source['day_key'] === 'string' ? source['day_key'] : '',
            month_key: typeof source['month_key'] === 'string' ? source['month_key'] : '',
            daily_count: dailyCount,
            daily_limit: dailyLimit,
            daily_remaining: dailyRemaining,
            monthly_count: monthlyCount,
            monthly_limit: monthlyLimit,
            monthly_remaining: monthlyRemaining,
            updated_at: typeof source['updated_at'] === 'string' ? source['updated_at'] : ''
        };
    }

    private usageLimitValue(value: unknown, fallback: number): number {
        const limit = this.toNumber(value);
        if (limit === null) return fallback;
        return Math.max(0, Math.round(limit));
    }

    private usageCountValue(value: unknown): number {
        const count = this.toNumber(value);
        return Math.max(0, Math.round(count ?? 0));
    }

    private usageRemainingValue(value: unknown, limit: number, count: number): number | null {
        if (!limit) return null;
        const remaining = this.toNumber(value);
        return Math.max(0, Math.round(remaining ?? Math.max(0, limit - count)));
    }

    private async loadChatHistory(selectLatest: boolean = false): Promise<void> {
        this.isChatHistoryLoading = true;
        try {
            const response = await fetch('/api/chat', {
                headers: authHeaderForUrl('/api/chat')
            });
            const rawPayload = await response.json();
            const payload = this.normalizeWizStatusPayload(rawPayload);
            const payloadObject = payload && typeof payload === 'object' && !Array.isArray(payload)
                ? payload as { data?: unknown[]; usage?: Partial<AiUsage> }
                : null;
            const rows = Array.isArray(payload) ? payload : Array.isArray(payloadObject?.data) ? payloadObject.data : [];
            this.applyAiUsage(payloadObject?.usage);
            this.chatSessions = rows
                .map((row: unknown) => this.normalizeChatSession(row))
                .filter((row: ChatSession | null): row is ChatSession => Boolean(row));

            this.syncDailyChatState(selectLatest);
        } catch {
            this.chatSessions = [];
            this.chatDayPromptSession = null;
        } finally {
            this.isChatHistoryLoading = false;
            this.cdr.detectChanges();
        }
    }

    private syncDailyChatState(selectLatest: boolean): void {
        if (this.activeChatSessionId) {
            const active = this.chatSessions.find((item) => item.id === this.activeChatSessionId);
            if (!active) {
                this.activeChatSessionId = null;
            } else if (!this.isChatSessionFromToday(active)) {
                if (selectLatest) {
                    this.chatDayPromptSession = active;
                    this.activeChatSessionId = null;
                    this.chatMessages = [];
                    return;
                }
                this.chatDayPromptSession = null;
                return;
            } else {
                this.chatDayPromptSession = null;
                return;
            }
        }

        if (!this.chatSessions.length) {
            this.chatDayPromptSession = null;
            return;
        }

        if (!selectLatest || this.activeChatSessionId || !this.chatSessions.length) return;

        const latest = this.chatSessions[0];
        if (this.isChatSessionFromToday(latest)) {
            this.selectChatSession(latest);
            return;
        }

        this.chatDayPromptSession = latest;
        this.chatMessages = [];
    }

    private prepareChatSessionForSend(): string | null {
        const active = this.chatSessions.find((item) => item.id === this.activeChatSessionId);
        if (!active) {
            this.activeChatSessionId = null;
            return null;
        }
        if (this.isChatSessionFromToday(active)) {
            return active.id;
        }

        this.activeChatSessionId = null;
        this.chatMessages = this.buildChatMessages();
        return null;
    }

    private isChatSessionFromToday(session: ChatSession): boolean {
        return this.chatSessionDayKey(session) === this.todayDateKey;
    }

    private async loadAiConnection(): Promise<void> {
        try {
            const response = await fetch('/api/ai-config');
            const payload = await response.json();
            this.applyAiConnection(payload);
        } catch {
            this.aiConnection = {
                configured: false,
                provider: 'OpenAI Responses API',
                model: '-',
                message: 'AI 연결 상태를 확인하지 못했습니다.',
                setup_steps: []
            };
        }

        this.cdr.detectChanges();
    }

    private async loadAppleMusicConnection(): Promise<void> {
        try {
            const response = await fetch('/api/apple-music');
            const payload = await response.json().catch(() => null);
            this.applyAppleMusicConnection(payload);
        } catch {
            this.appleMusicConnection = {
                configured: false,
                developer_token: '',
                message: 'Apple Music 연결 상태를 확인하지 못했어.',
                setup_steps: []
            };
        }

        this.appSettings.appleMusicConnected = Boolean(this.appleMusicUserToken()) && this.appleMusicConnection.configured;
        this.persistAppSettings();
        this.cdr.detectChanges();
    }

    private applyAppleMusicConnection(payload: Partial<AppleMusicConnection> | null | undefined): void {
        this.appleMusicConnection = {
            configured: Boolean(payload?.configured),
            developer_token: typeof payload?.developer_token === 'string' ? payload.developer_token : '',
            message: typeof payload?.message === 'string' ? payload.message : '',
            setup_steps: Array.isArray(payload?.setup_steps) ? payload.setup_steps : []
        };
    }

    private async connectAppleMusic(): Promise<void> {
        this.isAppleMusicLoading = true;
        this.appleMusicStatus = 'Apple Music 연결 확인 중';
        this.cdr.detectChanges();

        try {
            if (!this.appleMusicConnection.configured) {
                await this.loadAppleMusicConnection();
            }
            if (!this.appleMusicConnection.configured) {
                this.appleMusicStatus = this.appleMusicConnection.message || 'Apple Music 서버 설정이 필요해.';
                this.showToast(this.appleMusicStatus, 'error');
                return;
            }

            const token = await this.nativeAuthorizeAppleMusic() || await this.musicKitJsAuthorize();
            if (!token) {
                this.appleMusicStatus = 'Apple Music User Token을 받지 못했어.';
                this.showToast(this.appleMusicStatus, 'error');
                return;
            }

            this.storeAppleMusicUserToken(token);
            this.appSettings.appleMusicConnected = true;
            this.persistAppSettings();
            this.appleMusicStatus = 'Apple Music 연결됨';
            this.showToast('Apple Music을 연결했어.', 'success');
        } catch {
            this.appleMusicStatus = 'Apple Music 연결 중 오류가 발생했어.';
            this.showToast(this.appleMusicStatus, 'error');
        } finally {
            this.isAppleMusicLoading = false;
            this.cdr.detectChanges();
        }
    }

    private async disconnectAppleMusic(): Promise<void> {
        this.isAppleMusicLoading = true;
        this.cdr.detectChanges();

        try {
            const bridge = this.appleMusicBridge();
            if (bridge && typeof bridge.deauthorize === 'function') {
                await bridge.deauthorize();
            }
        } catch {
            // Local disconnect still clears the stored token.
        } finally {
            this.removeAppleMusicUserToken();
            this.appSettings.appleMusicConnected = false;
            this.appleMusicRecentTracks = [];
            this.selectedMusicTrackIds = [];
            this.appleMusicTracksVisible = false;
            this.appleMusicStatus = 'Apple Music 연결 해제됨';
            this.persistAppSettings();
            this.showToast('Apple Music 연결을 해제했어.', 'success');
            this.isAppleMusicLoading = false;
            this.cdr.detectChanges();
        }
    }

    private appleMusicUserToken(): string {
        if (typeof window === 'undefined' || !window.localStorage) return '';
        try {
            return window.localStorage.getItem(this.appleMusicUserTokenStorageKey) || '';
        } catch {
            return '';
        }
    }

    private storeAppleMusicUserToken(token: string): void {
        if (typeof window === 'undefined' || !window.localStorage) return;
        try {
            window.localStorage.setItem(this.appleMusicUserTokenStorageKey, token);
        } catch {
            return;
        }
    }

    private removeAppleMusicUserToken(): void {
        if (typeof window === 'undefined' || !window.localStorage) return;
        try {
            window.localStorage.removeItem(this.appleMusicUserTokenStorageKey);
        } catch {
            return;
        }
    }

    private appleMusicBridge(): any {
        if (typeof window === 'undefined') return null;
        return (window as any).RunningMateMusicKit || null;
    }

    private async nativeAuthorizeAppleMusic(): Promise<string> {
        const bridge = this.appleMusicBridge();
        if (!bridge || typeof bridge.authorize !== 'function') return '';

        const result = await bridge.authorize({
            developerToken: this.appleMusicConnection.developer_token
        });
        if (typeof result === 'string') return result;
        if (result && typeof result.userToken === 'string') return result.userToken;
        if (result && typeof result.user_token === 'string') return result.user_token;
        return '';
    }

    private async nativeRecentAppleMusicTracks(): Promise<MusicTrack[]> {
        const bridge = this.appleMusicBridge();
        if (!bridge || typeof bridge.getRecentPlayedTracks !== 'function') return [];

        try {
            const result = await bridge.getRecentPlayedTracks({ limit: 30 });
            const rows = Array.isArray(result) ? result : Array.isArray(result?.data) ? result.data : [];
            return rows
                .map((track: unknown) => this.normalizeMusicTrack(track))
                .filter((track: MusicTrack | null): track is MusicTrack => Boolean(track))
                .slice(0, 30);
        } catch {
            return [];
        }
    }

    private async musicKitJsAuthorize(): Promise<string> {
        if (!this.appleMusicConnection.developer_token) return '';
        await this.loadMusicKitScript();

        const musicKit = (window as any).MusicKit;
        if (!musicKit) return '';

        musicKit.configure({
            developerToken: this.appleMusicConnection.developer_token,
            app: {
                name: 'RunningMate',
                build: this.appVersion
            }
        });
        const instance = musicKit.getInstance();
        const token = await instance.authorize();
        return typeof token === 'string' ? token : typeof instance.musicUserToken === 'string' ? instance.musicUserToken : '';
    }

    private async loadMusicKitScript(): Promise<void> {
        if (typeof window === 'undefined' || typeof document === 'undefined') return;
        if ((window as any).MusicKit) return;

        await new Promise<void>((resolve, reject) => {
            const existing = document.querySelector('script[data-runningmate-musickit="true"]') as HTMLScriptElement | null;
            if (existing) {
                existing.addEventListener('load', () => resolve(), { once: true });
                existing.addEventListener('error', () => reject(new Error('MusicKit script failed')), { once: true });
                return;
            }

            const script = document.createElement('script');
            script.src = 'https://js-cdn.music.apple.com/musickit/v3/musickit.js';
            script.async = true;
            script.dataset.runningmateMusickit = 'true';
            script.addEventListener('load', () => resolve(), { once: true });
            script.addEventListener('error', () => reject(new Error('MusicKit script failed')), { once: true });
            document.head.appendChild(script);
        });
    }

    private applyAiConnection(payload: Partial<AiConnection> | null | undefined): void {
        this.aiConnection = {
            configured: Boolean(payload?.configured),
            provider: typeof payload?.provider === 'string' ? payload.provider : 'OpenAI Responses API',
            model: typeof payload?.model === 'string' ? payload.model : '-',
            message: typeof payload?.message === 'string' ? payload.message : '',
            setup_steps: Array.isArray(payload?.setup_steps) ? payload.setup_steps : [],
            mode: typeof payload?.mode === 'string' ? payload.mode : '',
            codex_supported: Boolean(payload?.codex_supported),
            codex_authenticated: Boolean(payload?.codex_authenticated),
            codex_status: typeof payload?.codex_status === 'string' ? payload.codex_status : '',
            codex_status_message: typeof payload?.codex_status_message === 'string' ? payload.codex_status_message : '',
            login_refresh_supported: Boolean(payload?.login_refresh_supported)
        };
    }

    private async parseAndSaveFile(
        file: File,
        fileIndex: number,
        totalFiles: number,
        targetDate: string | null = null,
        runType: RunType = 'jogging',
        hydration: Partial<RunRecord> = {},
        music: Partial<RunRecord> = {},
        mediaRunId: string = '',
        isPublic: boolean = true,
        updateRunId: string | null = null
    ): Promise<SaveRunResult> {
        try {
            if (this.isVideoFile(file)) {
                if (!targetDate) {
                    return { saved: false, message: '영상은 달력에서 날짜를 선택한 뒤 추가할 수 있어.' };
                }
                const targetRunId = mediaRunId || this.runIdForCalendarMediaTarget();
                if (!targetRunId) {
                    return { saved: false, message: '영상은 먼저 러닝 기록을 저장한 뒤 추가할 수 있어.' };
                }
                return await this.uploadCalendarMediaFile(targetRunId, file, fileIndex, totalFiles);
            }
            if (!this.isImageFile(file)) {
                return { saved: false, message: '지원하지 않는 파일 형식이야. 사진이나 영상을 선택해줘.' };
            }
            const parsePayload = await this.parseImageFile(file, targetDate, (stage) => {
                this.updateUploadProgress(fileIndex, totalFiles, stage, `${fileIndex + 1}/${totalFiles} 이미지 파싱 중`);
            });
            if (!parsePayload?.success || !parsePayload?.data) {
                return { saved: false, message: this.parseImageFailureMessage(parsePayload) };
            }

            const data = parsePayload.data as RunRecord;
            if (targetDate) data.date = targetDate;
            data.run_type = this.normalizeRunType(runType);
            data.is_public = isPublic;
            if (hydration.water_before_ml !== undefined) {
                data.water_before_ml = hydration.water_before_ml;
            }
            if (hydration.water_after_ml !== undefined) {
                data.water_after_ml = hydration.water_after_ml;
            }
            if (music.playlist_name) {
                data.playlist_name = music.playlist_name;
            }
            if (music.music_url) {
                data.music_url = music.music_url;
            }
            if (music.top_tracks?.length) {
                data.top_tracks = music.top_tracks;
            }
            if (music.journal) {
                data.journal = music.journal;
            }
            if (!data.date || !this.toNumber(data.distance_km)) {
                return { saved: false, message: this.parseImageFailureMessage(parsePayload, '이미지에서 날짜와 거리 값을 확인하지 못했어. 수동으로 입력해줘.') };
            }

            this.updateUploadProgress(fileIndex, totalFiles, 94, `${fileIndex + 1}/${totalFiles} 기록 저장 중`);
            const savePayload = await this.saveRunRecord(data, updateRunId);
            this.updateUploadProgress(fileIndex, totalFiles, 100, `${fileIndex + 1}/${totalFiles} 처리 완료`);
            return savePayload;
        } catch (error) {
            const payload = error as { message?: unknown; error?: { message?: unknown } } | null;
            const message = typeof payload?.message === 'string'
                ? payload.message
                : typeof payload?.error?.message === 'string'
                    ? payload.error.message
                    : '';
            return { saved: false, message: this.parseImageFailureMessage(payload, message || '이미지를 읽지 못했어. 수동으로 입력할래?') };
        }
    }

    private parseImageFailureMessage(payload: unknown, fallback: string = '이미지를 읽지 못했어. 수동으로 입력할래?'): string {
        const normalizedPayload = this.normalizeWizStatusPayload(payload);
        if (normalizedPayload !== payload) {
            return this.parseImageFailureMessage(normalizedPayload, fallback);
        }

        if (payload && typeof payload === 'object') {
            const source = payload as Record<string, unknown>;
            const message = typeof source['message'] === 'string' ? source['message'].trim() : '';
            if (message) return message;

            const errorCode = typeof source['error_code'] === 'string' ? source['error_code'] : '';
            if (AI_PARSE_CONFIGURATION_ERROR_CODES.has(errorCode)) {
                return this.aiConnection?.message || 'AI 이미지 파싱 설정을 확인해야 해. OpenAI API 키, 결제 상태, 모델 설정을 확인해줘.';
            }
        }

        return fallback;
    }

    private async uploadCalendarMediaFile(runId: string, file: File, fileIndex: number, totalFiles: number): Promise<SaveRunResult> {
        this.updateUploadProgress(fileIndex, totalFiles, 25, `${fileIndex + 1}/${totalFiles} 사진/영상 업로드 중`);
        const form = new FormData();
        form.append('media', file);
        const response = await fetch(`/api/runs/${encodeURIComponent(runId)}/media`, {
            method: 'POST',
            body: form
        });
        const payload = await response.json().catch(() => null);
        if (!payload?.success) {
            return { saved: false, message: payload?.message || '사진/영상을 업로드하지 못했어.' };
        }

        const rows = Array.isArray(payload.media) ? payload.media : Array.isArray(payload.data) ? payload.data : [];
        this.applyRunMedia(runId, rows);
        this.updateUploadProgress(fileIndex, totalFiles, 100, `${fileIndex + 1}/${totalFiles} 처리 완료`);
        return {
            saved: true,
            mediaRunId: runId,
            message: '사진/영상을 추가했어.'
        };
    }

    private async saveRunRecord(data: RunRecord & { raw_parsed_json?: Record<string, unknown> }, updateRunId: string | null = null): Promise<SaveRunResult> {
        const endpoint = updateRunId ? `/api/runs/${encodeURIComponent(updateRunId)}` : '/api/runs';
        const result = await jsonRequest<any>(endpoint, updateRunId ? 'PATCH' : 'POST', data);
        const payload = result.raw as any;
        if (!result.success) {
            return {
                saved: false,
                message: result.error?.message || '러닝 기록을 저장하지 못했어.'
            };
        }
        if (payload?.success && payload?.data?.date) {
            this.restDays = this.restDays.filter((date) => date !== payload.data.date);
        }
        const newlyEarnedBadges = !updateRunId && Array.isArray(payload?.newly_earned_badges)
            ? payload.newly_earned_badges
                .map((row: unknown) => this.normalizeBadge(row))
                .filter((row: Badge | null): row is Badge => Boolean(row))
            : [];
        if (newlyEarnedBadges.length) {
            this.handleNewlyEarnedBadges(newlyEarnedBadges);
        }
        void this.loadChallenges();
        return {
            saved: true,
            message: payload?.message,
            run: payload?.data as RunRecord | undefined,
            newlyEarnedBadges
        };
    }

    private handleNewlyEarnedBadges(badges: Badge[]): void {
        const existingCodes = new Set(this.newlyEarnedBadges.map((badge) => badge.code));
        const nextBadges = [
            ...this.newlyEarnedBadges,
            ...badges.filter((badge) => !existingCodes.has(badge.code))
        ];
        this.newlyEarnedBadges = nextBadges;

        this.badges = this.badges.map((badge) => {
            const earned = badges.find((item) => item.code === badge.code);
            return earned ? { ...badge, ...earned, achieved: true } : badge;
        });
        for (const badge of badges) {
            if (!this.badges.some((item) => item.code === badge.code)) {
                this.badges.push(badge);
            }
        }

        const names = badges.map((badge) => badge.title).join(', ');
        const message = badges.length === 1
            ? `새 뱃지 '${names}' 획득을 축하해. 오늘 기록이 제대로 쌓였어.`
            : `새 뱃지 ${badges.length}개(${names})를 획득했어. 흐름이 좋아.`;
        this.chatMessages = [
            ...this.chatMessages,
            { sender: 'ai', text: message, created_at: new Date().toISOString() }
        ];

        this.showToast(`새 뱃지 ${badges.length}개 획득`, 'success');
        this.cdr.detectChanges();
        void this.loadBadges();
    }

    private updateUploadProgress(fileIndex: number, totalFiles: number, stage: number, status: string): void {
        const total = Math.max(1, totalFiles);
        const completed = Math.max(0, fileIndex);
        const currentShare = Math.max(0, Math.min(100, stage)) / total;
        const progress = Math.round((completed / total) * 100 + currentShare);

        this.uploadProgress = Math.max(this.uploadProgress, Math.min(99, progress));
        this.uploadStatus = status;
        this.cdr.detectChanges();
    }

    private async parseImageFile(file: File, targetDate: string | null, onProgress: (stage: number) => void): Promise<any> {
        if (!(await ensureAuthenticated())) {
            throw { message: '로그인이 만료되었습니다. 다시 로그인해주세요.' };
        }

        return new Promise((resolve, reject) => {
            const form = new FormData();
            form.append('image', file);
            if (targetDate) {
                form.append('target_date', targetDate);
            }

            const xhr = new XMLHttpRequest();
            let stage = 3;
            let timer: number | null = null;
            const setStage = (value: number) => {
                stage = Math.max(stage, Math.min(90, Math.round(value)));
                onProgress(stage);
            };
            const clearTimer = () => {
                if (timer !== null) {
                    window.clearInterval(timer);
                    timer = null;
                }
            };

            xhr.open('POST', resolveApiUrl('/api/parse-image'));
            xhr.timeout = 20000;
            xhr.responseType = 'json';
            Object.entries(authHeaderForUrl('/api/parse-image')).forEach(([key, value]) => {
                xhr.setRequestHeader(key, value);
            });
            xhr.upload.addEventListener('progress', (event) => {
                if (event.lengthComputable && event.total > 0) {
                    setStage(5 + (event.loaded / event.total) * 35);
                }
            });
            xhr.addEventListener('loadstart', () => {
                setStage(5);
                timer = window.setInterval(() => setStage(stage + 2), 700);
            });
            xhr.addEventListener('load', () => {
                clearTimer();
                setStage(90);
                const payload = this.normalizeWizStatusPayload(xhr.response || this.parseJson(xhr.responseText));
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve(payload);
                } else {
                    reject(payload);
                }
            });
            xhr.addEventListener('error', () => {
                clearTimer();
                reject(standardApiError('network'));
            });
            xhr.addEventListener('timeout', () => {
                clearTimer();
                reject(standardApiError('timeout'));
            });
            xhr.addEventListener('abort', () => {
                clearTimer();
                reject(standardApiError('timeout'));
            });
            xhr.send(form);
        });
    }

    private parseJson(text: string): unknown {
        try {
            return JSON.parse(text);
        } catch {
            return null;
        }
    }

    private normalizeWizStatusPayload(payload: unknown): unknown {
        if (!payload || typeof payload !== 'object') return payload;

        const source = payload as Record<string, unknown>;
        const code = source['code'];
        const data = source['data'];
        if (
            (typeof code === 'number' || typeof code === 'string') &&
            data &&
            typeof data === 'object' &&
            !('success' in source)
        ) {
            return data;
        }

        return payload;
    }

    private async readChatResponse(response: Response, aiMessageIndex: number): Promise<void> {
        const contentType = response.headers.get('Content-Type') || '';
        if (!response.ok || !response.body || contentType.includes('application/json')) {
            const payload = await response.json().catch(() => null);
            this.applyAiUsage(payload?.usage, true);
            const reply = payload?.success
                ? payload?.reply || '답변을 만들지 못했어.'
                : payload?.message || 'AI 채팅 중 오류가 발생했어.';
            this.replaceChatMessage(aiMessageIndex, reply, false);
            return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let hasReply = false;

        while (true) {
            const { value, done } = await reader.read();
            buffer += decoder.decode(value || new Uint8Array(), { stream: !done });

            const lines = buffer.split(/\r?\n/);
            buffer = lines.pop() || '';

            for (const line of lines) {
                hasReply = this.handleChatStreamLine(line, aiMessageIndex) || hasReply;
            }

            if (done) break;
        }

        if (buffer.trim()) {
            hasReply = this.handleChatStreamLine(buffer, aiMessageIndex) || hasReply;
        }

        if (!hasReply) {
            this.replaceChatMessage(aiMessageIndex, '답변을 만들지 못했어.', false);
        }
    }

    private handleChatStreamLine(line: string, aiMessageIndex: number): boolean {
        const payload = this.parseJson(line.trim());
        if (!payload || typeof payload !== 'object') return false;

        const event = String((payload as Record<string, unknown>).event || (payload as Record<string, unknown>).type || '');
        const text = (payload as Record<string, unknown>).text;
        const message = (payload as Record<string, unknown>).message;
        this.applyAiUsage((payload as Record<string, unknown>).usage, event === 'error' || event === 'done');

        if (event === 'delta' && typeof text === 'string' && text) {
            this.appendChatMessage(aiMessageIndex, text);
            return true;
        }

        if (event === 'message' && typeof text === 'string') {
            this.replaceChatMessage(aiMessageIndex, text, true);
            return Boolean(text.trim());
        }

        if (event === 'error') {
            this.replaceChatMessage(
                aiMessageIndex,
                typeof message === 'string' && message ? message : 'AI 채팅 중 오류가 발생했어.',
                false
            );
            return true;
        }

        if (event === 'done') {
            this.finishChatMessage(aiMessageIndex);
        }

        return false;
    }

    private appendChatMessage(index: number, text: string): void {
        this.updateChatMessage(index, (message) => ({
            ...message,
            text: `${message.text}${text}`,
            streaming: true
        }));
    }

    private replaceChatMessage(index: number, text: string, streaming: boolean): void {
        this.updateChatMessage(index, (message) => ({
            ...message,
            text,
            streaming
        }));
    }

    private finishChatMessage(index: number): void {
        this.updateChatMessage(index, (message) => ({
            ...message,
            text: message.text.trim() ? message.text : '답변을 만들지 못했어.',
            streaming: false
        }));
    }

    private updateChatMessage(index: number, updater: (message: ChatMessage) => ChatMessage): void {
        if (!this.chatMessages[index]) return;

        const next = [...this.chatMessages];
        next[index] = updater(next[index]);
        this.chatMessages = next;
        this.cdr.detectChanges();
        this.scrollChatToBottom();
    }

    private scrollChatToBottom(): void {
        window.setTimeout(() => {
            const messages = this.elementRef.nativeElement.querySelector('.chat-messages');
            if (messages) {
                messages.scrollTop = messages.scrollHeight;
            }
        }, 0);
    }

    private setRuns(rows: unknown[], options: { loadRelatedData?: boolean } = {}): void {
        this.runs = rows
            .map((row) => this.normalizeRun(row))
            .filter((row): row is RunRecord => Boolean(row))
            .sort((a, b) => b.date.localeCompare(a.date));

        const nextYearMonth = this.runs[0]?.date.slice(0, 7) || this.yearMonthKey(new Date());
        const monthChanged = this.activeYearMonth !== nextYearMonth;
        this.activeYearMonth = nextYearMonth;
        this.refreshDerivedState();
        this.cdr.detectChanges();
        if (options.loadRelatedData !== false) {
            void this.loadGoalsForActiveMonth();
            if (monthChanged) {
                void this.loadWeatherForActiveMonth();
            }
        }
    }

    private setBadges(rows: unknown[]): void {
        this.badges = rows
            .map((row) => this.normalizeBadge(row))
            .filter((row): row is Badge => Boolean(row));

        if (this.selectedBadge) {
            this.selectedBadge = this.badges.find((badge) => badge.code === this.selectedBadge?.code) || null;
        }

        this.cdr.detectChanges();
    }

    private applyRunMedia(runId: string, rows: unknown[]): void {
        const media = rows
            .map((row) => this.normalizeRunMedia(row))
            .filter((row): row is RunMedia => Boolean(row));

        this.runs = this.runs.map((run) => run.id === runId ? { ...run, media } : run);
        this.refreshDerivedState();
        this.cdr.detectChanges();
    }

    private runIdForCalendarMediaTarget(): string {
        const selectedRun = this.selectedCalendarRuns.find((run) => Boolean(run.id));
        if (selectedRun?.id) return selectedRun.id;

        const selectedDate = this.selectedCalendarDate;
        const existingRun = selectedDate
            ? this.runs.find((run) => run.date === selectedDate && Boolean(run.id))
            : null;
        return existingRun?.id || '';
    }

    private isImageFile(file: File): boolean {
        const type = String(file.type || '').toLowerCase();
        if (type.startsWith('image/')) return true;
        return /\.(jpe?g|png|webp|gif|heic|heif)$/i.test(file.name || '');
    }

    private isVideoFile(file: File): boolean {
        const type = String(file.type || '').toLowerCase();
        if (type.startsWith('video/')) return true;
        return /\.(mp4|mov|m4v|webm)$/i.test(file.name || '');
    }

    private applyRunUpdate(row: unknown): void {
        const updated = this.normalizeRun(row);
        if (!updated?.id) return;

        this.runs = this.runs.map((run) => run.id === updated.id ? updated : run);
        this.feedItems = this.feedItems.map((run) => run.id === updated.id ? {
            ...run,
            ...updated,
            id: run.id,
            user: run.user,
            reaction_summary: run.reaction_summary,
            reaction_count: run.reaction_count,
            comment_count: run.comment_count,
            comments: run.comments
        } : run);
        if (this.activeJournalViewer?.id === updated.id) {
            this.activeJournalViewer = updated.journal ? updated : null;
        }
        this.refreshDerivedState();
        this.cdr.detectChanges();
        void this.loadTrainingLoad();
    }

    private removeRunMedia(mediaId: string): void {
        this.runs = this.runs.map((run) => ({
            ...run,
            media: (run.media || []).filter((media) => media.id !== mediaId)
        }));
        this.refreshDerivedState();
        this.cdr.detectChanges();
    }

    private setRestDays(rows: unknown[]): void {
        this.restDays = Array.from(new Set(
            rows
                .map((row) => this.normalizeDateKey(row))
                .filter((date): date is string => Boolean(date))
        )).sort();

        this.refreshDerivedState();
        this.cdr.detectChanges();
    }

    private setDayNotes(rows: unknown[]): void {
        this.calendarNotes = new Map(
            rows
                .map((row) => this.normalizeDayNote(row))
                .filter((note): note is CalendarNote => Boolean(note))
                .map((note) => [note.date, note])
        );
        this.syncSelectedCalendarMemo();
        this.syncUploadJournalWithSelectedDate();
        this.refreshDerivedState();
        this.cdr.detectChanges();
    }

    private setWeights(rows: unknown[]): void {
        this.weightLogs = rows
            .map((row) => this.normalizeWeightLog(row))
            .filter((row): row is WeightLog => Boolean(row))
            .sort((a, b) => b.date.localeCompare(a.date));

        this.refreshWeightDerivedState();
        if (!this.weightInput) {
            this.syncWeightInputForDate();
        }
        this.cdr.detectChanges();
    }

    private applyWeightSettings(row: unknown): void {
        const settings = this.normalizeWeightSettings(row);
        if (!settings) return;

        this.targetWeightKg = settings.target_weight_kg;
        this.weightTargetInput = settings.target_weight_kg !== null ? settings.target_weight_kg.toFixed(1) : '';
        this.persistWeightTargetLocal(settings.target_weight_kg);
        this.weightTargetStatus = '';
        this.refreshWeightDerivedState();
        this.cdr.detectChanges();
    }

    private applyGoalsPayload(payload: unknown): void {
        const source = payload && typeof payload === 'object' ? payload as Record<string, unknown> : {};
        const rows = Array.isArray(source.data) ? source.data : Array.isArray(payload) ? payload : [];
        this.goals = rows
            .map((row) => this.normalizeGoal(row))
            .filter((goal): goal is Goal => Boolean(goal))
            .filter((goal) => goal.year_month === this.activeYearMonth)
            .sort((a, b) => this.goalTypeIndex(a.goal_type) - this.goalTypeIndex(b.goal_type));

        const progressRows = Array.isArray(source.progress) ? source.progress : [];
        this.goalProgressCards = progressRows
            .map((row) => this.normalizeGoalProgress(row))
            .filter((goal): goal is GoalProgress => Boolean(goal))
            .filter((goal) => goal.year_month === this.activeYearMonth)
            .sort((a, b) => this.goalTypeIndex(a.goal_type) - this.goalTypeIndex(b.goal_type));

        const historyRows = Array.isArray(source.history) ? source.history : [];
        this.goalHistory = historyRows
            .map((row) => this.normalizeGoalHistory(row))
            .filter((row): row is GoalHistory => Boolean(row));

        this.syncGoalDrafts();
        this.refreshDerivedState();
        this.cdr.detectChanges();
    }

    private applyChallengesPayload(payload: unknown): void {
        const source = payload && typeof payload === 'object' ? payload as Record<string, unknown> : {};
        const rows = Array.isArray(source.challenges)
            ? source.challenges
            : Array.isArray(source.data)
                ? source.data
                : Array.isArray(payload)
                    ? payload
                    : [];
        this.setChallenges(rows);
    }

    private applyRankingPayload(payload: unknown): void {
        const source = payload && typeof payload === 'object' ? payload as Record<string, unknown> : {};
        const data = source.data && typeof source.data === 'object'
            ? source.data as Record<string, unknown>
            : source;
        const period = this.normalizeRankingPeriod(data['period']) || this.activeRankingPeriod;
        if (period !== this.activeRankingPeriod) {
            this.activeRankingPeriod = period;
        }

        const scope = this.normalizeRankingScope(data['scope']) || this.activeRankingScope;
        if (scope !== this.activeRankingScope) {
            this.activeRankingScope = scope;
        }

        const rows = Array.isArray(data['entries']) ? data['entries'] : [];
        this.rankingEntries = rows
            .map((row) => this.normalizeRankingEntry(row))
            .filter((entry): entry is RankingEntry => Boolean(entry));

        this.rankingMe = this.normalizeRankingEntry(data['me']) || this.rankingEntries.find((entry) => entry.is_viewer) || null;
        this.rankingPeriodLabel = typeof data['period_label'] === 'string' ? data['period_label'] : '';
        this.rankingScopeLabel = typeof data['scope_label'] === 'string' ? data['scope_label'] : this.rankingTitleText;
        this.rankingTargetCount = Math.max(0, Math.round(this.toNumber(data['target_count'] ?? data['targetCount']) || 0));
        this.rankingMotivationText = typeof data['motivation_text'] === 'string' ? data['motivation_text'] : '';
        this.rankingFinalized = Boolean(data['finalized']);

        const viewer = data['viewer'] && typeof data['viewer'] === 'object' ? data['viewer'] as Record<string, unknown> : {};
        if ('ranking_enabled' in viewer) {
            this.rankingParticipationEnabled = Boolean(viewer['ranking_enabled']);
        }
        if (!this.shouldShowChatDayPrompt && (!this.chatMessages.length || (this.chatMessages.length === 1 && this.chatMessages[0].sender === 'ai'))) {
            this.chatMessages = this.buildChatMessages();
        }
        this.cdr.detectChanges();
    }

    private setChallenges(rows: unknown[]): void {
        this.challenges = rows
            .map((row) => this.normalizeChallenge(row))
            .filter((challenge): challenge is Challenge => Boolean(challenge))
            .sort((a, b) => {
                const statusOrder = (challenge: Challenge): number => challenge.status === 'ended' ? 2 : challenge.viewer_joined ? 0 : 1;
                const statusDiff = statusOrder(a) - statusOrder(b);
                return statusDiff || b.created_at.localeCompare(a.created_at);
            });

        if (this.selectedChallengeId && !this.challenges.some((challenge) => challenge.id === this.selectedChallengeId)) {
            this.selectedChallengeId = null;
            if (this.challengeViewMode === 'detail') {
                this.challengeViewMode = 'list';
            }
        }
        if (!this.selectedChallengeId && this.activeChallengeList.length) {
            this.selectedChallengeId = this.activeChallengeList[0].id;
        }
        this.cdr.detectChanges();
    }

    private setFeedItems(rows: unknown[]): void {
        this.feedItems = rows
            .map((row) => this.normalizeFeedRun(row))
            .filter((row): row is FeedRun => Boolean(row));

        const validIds = new Set(this.feedItems.map((item) => item.id));
        this.feedCommentDrafts = Object.fromEntries(
            Object.entries(this.feedCommentDrafts).filter(([runId]) => validIds.has(runId))
        );
        if (this.expandedReactionRunId && !validIds.has(this.expandedReactionRunId)) {
            this.expandedReactionRunId = null;
        }
        if (this.expandedCommentsRunId && !validIds.has(this.expandedCommentsRunId)) {
            this.expandedCommentsRunId = null;
        }
        this.cdr.detectChanges();
    }

    private profileFeedRunFromItem(item: GalleryItem): FeedRun | null {
        const sourceRun = item.run;
        const runId = typeof sourceRun?.id === 'string' && sourceRun.id
            ? sourceRun.id
            : item.media?.run_id || '';
        if (!sourceRun || !runId) return null;

        const current = this.activeProfileFeedRun?.id === runId ? this.activeProfileFeedRun : null;
        const existing = this.feedItems.find((run) => run.id === runId) || current;
        if (existing) return existing;

        const owner = item.owner || this.myFeedUser();
        const ownerId = sourceRun.user_id || owner.id || this.profile?.id || '';
        return {
            ...sourceRun,
            id: runId,
            user: {
                id: ownerId || runId,
                name: owner.name || '러너',
                display_id: owner.display_id || ownerId || runId,
                profile_image: owner.profile_image || '',
                is_me: owner.is_me
            },
            reaction_summary: this.emptyFeedReactions(),
            reaction_count: 0,
            comment_count: 0,
            comments: []
        };
    }

    private applyFeedSocial(runId: string, row: unknown): void {
        const social = this.normalizeFeedSocial(row);
        if (!social) return;

        const applySocial = (run: FeedRun): FeedRun => ({
            ...run,
            reaction_summary: social.reaction_summary,
            reaction_count: social.reaction_count,
            comment_count: social.comment_count,
            comments: social.comments
        });

        this.feedItems = this.feedItems.map((run) => run.id === runId ? applySocial(run) : run);
        if (this.activeProfileFeedRun?.id === runId) {
            this.activeProfileFeedRun = applySocial(this.activeProfileFeedRun);
        }
        this.cdr.detectChanges();
    }

    private setCycles(rows: unknown[], summary?: unknown): void {
        this.cycleLogs = rows
            .map((row) => this.normalizeCycleLog(row))
            .filter((row): row is CycleLog => Boolean(row))
            .sort((a, b) => b.start_date.localeCompare(a.start_date));
        this.cycleSummary = this.normalizeCycleSummary(summary);
        this.refreshDerivedState();
        this.cdr.detectChanges();
    }

    private setWeatherDays(data: WeatherResponseData): void {
        const days = data.days && typeof data.days === 'object' ? data.days : {};
        this.weatherDays = new Map(
            Object.entries(days)
                .map(([date, row]) => this.normalizeWeatherDay(date, row))
                .filter((day): day is WeatherDay => Boolean(day))
                .map((day) => [day.date, day])
        );
        this.weatherCoverage = this.normalizeWeatherCoverage(data.coverage);

        const locationName = typeof data.location?.name === 'string' ? data.location.name.trim() : '';
        this.weatherLocationText = locationName;
        this.weatherUpdatedText = this.formatWeatherBase(data.base);
        this.weatherStatus = this.weatherDays.size ? '' : this.weatherCoverage?.message || '예보 범위 밖';
        this.refreshDerivedState();
        this.cdr.detectChanges();
    }

    private normalizeWeatherCoverage(row: unknown): WeatherCoverage | null {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const startDate = this.normalizeDateKey(source.startDate);
        const endDate = this.normalizeDateKey(source.endDate);
        if (!startDate || !endDate) return null;

        const message = typeof source.message === 'string' && source.message.trim()
            ? source.message.trim()
            : '날씨 예보 범위 밖';

        return { startDate, endDate, message };
    }

    private selectedWeatherCoverageText(date: string): string {
        const coverage = this.weatherCoverage;
        if (!coverage) return '';
        if (date < coverage.startDate) {
            return `${this.displayDate(coverage.startDate, false)}부터 날씨 예보가 제공돼.`;
        }
        if (date > coverage.endDate) {
            return `${this.displayDate(coverage.endDate, false)}까지만 날씨 예보가 제공돼.`;
        }
        return '';
    }

    private normalizeRun(row: unknown): RunRecord | null {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const date = typeof source.date === 'string' ? source.date : '';
        const distance = this.toNumber(source.distance_km);

        if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || distance === null) {
            return null;
        }

        return {
            id: typeof source.id === 'string' ? source.id : null,
            date,
            distance_km: distance,
            avg_pace: typeof source.avg_pace === 'string' ? source.avg_pace : null,
            duration: typeof source.duration === 'string' ? source.duration : null,
            run_type: this.normalizeRunType(source.run_type || source.runType),
            calories: this.toNumber(source.calories),
            avg_heart_rate: this.toNumber(source.avg_heart_rate),
            cadence: this.toNumber(source.cadence),
            elevation_gain: this.toNumber(source.elevation_gain),
            water_before_ml: this.normalizeWaterMl(source.water_before_ml ?? source.waterBeforeMl),
            water_after_ml: this.normalizeWaterMl(source.water_after_ml ?? source.waterAfterMl),
            image_url: this.resolveMediaUrl(source.image_url) || null,
            journal: typeof source['journal'] === 'string' && source['journal'].trim() ? source['journal'].trim() : null,
            playlist_name: typeof source['playlist_name'] === 'string' && source['playlist_name'].trim()
                ? source['playlist_name'].trim()
                : typeof source['playlistName'] === 'string' && source['playlistName'].trim()
                    ? source['playlistName'].trim()
                    : null,
            music_url: typeof source['music_url'] === 'string' && source['music_url'].trim()
                ? source['music_url'].trim()
                : typeof source['musicUrl'] === 'string' && source['musicUrl'].trim()
                    ? source['musicUrl'].trim()
                    : null,
            top_tracks: Array.isArray(source['top_tracks'])
                ? source['top_tracks']
                    .map((track) => this.normalizeMusicTrack(track))
                    .filter((track): track is MusicTrack => Boolean(track))
                : Array.isArray(source['topTracks'])
                    ? source['topTracks']
                        .map((track) => this.normalizeMusicTrack(track))
                        .filter((track): track is MusicTrack => Boolean(track))
                    : [],
            is_public: source['is_public'] !== false && source['isPublic'] !== false,
            user_id: typeof source['user_id'] === 'string' ? source['user_id'] : typeof source['userId'] === 'string' ? source['userId'] : null,
            created_at: typeof source['created_at'] === 'string' ? source['created_at'] : null,
            media: Array.isArray(source['media'])
                ? source['media']
                    .map((item) => this.normalizeRunMedia(item))
                    .filter((item): item is RunMedia => Boolean(item))
                : []
        };
    }

    private normalizeFeedRun(row: unknown): FeedRun | null {
        const run = this.normalizeRun(row);
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const id = typeof source['id'] === 'string' ? source['id'] : '';
        const userSource = source['user'] && typeof source['user'] === 'object'
            ? source['user'] as Record<string, unknown>
            : {};
        const userId = typeof userSource['id'] === 'string' ? userSource['id'] : run?.user_id || '';
        if (!run || !id || !userId) return null;

        const social = this.normalizeFeedSocial(source) || {
            reaction_summary: this.emptyFeedReactions(),
            reaction_count: 0,
            comment_count: 0,
            comments: []
        };
        return {
            ...run,
            id,
            user: {
                id: userId,
                name: typeof userSource['name'] === 'string' && userSource['name'].trim() ? userSource['name'].trim() : '러너',
                display_id: typeof userSource['display_id'] === 'string' && userSource['display_id'].trim() ? userSource['display_id'].trim() : userId,
                profile_image: typeof userSource['profile_image'] === 'string' ? userSource['profile_image'] : '',
                is_me: Boolean(userSource['is_me'])
            },
            reaction_summary: social.reaction_summary,
            reaction_count: social.reaction_count,
            comment_count: social.comment_count,
            comments: social.comments
        };
    }

    private normalizeFeedSocial(row: unknown): Pick<FeedRun, 'reaction_summary' | 'reaction_count' | 'comment_count' | 'comments'> | null {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const summarySource = Array.isArray(source['reaction_summary'] ?? source['reactionSummary'])
            ? source['reaction_summary'] ?? source['reactionSummary']
            : [];
        const reactions = this.mergeFeedReactions(summarySource as unknown[]);
        const comments = Array.isArray(source['comments'])
            ? source['comments']
                .map((item) => this.normalizeFeedComment(item))
                .filter((item): item is FeedComment => Boolean(item))
            : [];
        return {
            reaction_summary: reactions,
            reaction_count: Math.max(0, Math.round(this.toNumber(source['reaction_count'] ?? source['reactionCount']) ?? reactions.reduce((sum, item) => sum + item.count, 0))),
            comment_count: Math.max(0, Math.round(this.toNumber(source['comment_count'] ?? source['commentCount']) ?? comments.length)),
            comments
        };
    }

    private mergeFeedReactions(rows: unknown[]): FeedReactionSummary[] {
        const byType = new Map<ReactionType, FeedReactionSummary>(
            this.emptyFeedReactions().map((item) => [item.type, item])
        );
        for (const row of rows) {
            const item = this.normalizeFeedReaction(row);
            if (item) byType.set(item.type, item);
        }
        return FEED_REACTION_SUMMARY.map((item) => byType.get(item.type) || { ...item, users: [] });
    }

    private emptyFeedReactions(): FeedReactionSummary[] {
        return FEED_REACTION_SUMMARY.map((item) => ({ ...item, users: [] }));
    }

    private normalizeFeedReaction(row: unknown): FeedReactionSummary | null {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const type = this.normalizeReactionType(source['type']);
        if (!type) return null;
        const fallback = FEED_REACTION_SUMMARY.find((item) => item.type === type);
        const users = Array.isArray(source['users'])
            ? source['users']
                .map((item) => this.normalizeFeedReactionUser(item, type))
                .filter((item): item is FeedReactionUser => Boolean(item))
            : [];
        return {
            type,
            emoji: typeof source['emoji'] === 'string' && source['emoji'] ? source['emoji'] : fallback?.emoji || '',
            label: typeof source['label'] === 'string' && source['label'] ? source['label'] : fallback?.label || '',
            count: Math.max(0, Math.round(this.toNumber(source['count']) ?? users.length)),
            reacted: Boolean(source['reacted']),
            users
        };
    }

    private normalizeFeedReactionUser(row: unknown, fallbackType: ReactionType): FeedReactionUser | null {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const userId = typeof source['user_id'] === 'string' ? source['user_id'] : typeof source['userId'] === 'string' ? source['userId'] : '';
        if (!userId) return null;
        return {
            user_id: userId,
            name: typeof source['name'] === 'string' && source['name'].trim() ? source['name'].trim() : '러너',
            profile_image: typeof source['profile_image'] === 'string' ? source['profile_image'] : '',
            type: this.normalizeReactionType(source['type']) || fallbackType,
            created_at: typeof source['created_at'] === 'string' ? source['created_at'] : '',
            is_me: Boolean(source['is_me'])
        };
    }

    private normalizeFeedComment(row: unknown): FeedComment | null {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const id = typeof source['id'] === 'string' ? source['id'] : '';
        const runId = typeof source['run_id'] === 'string' ? source['run_id'] : typeof source['runId'] === 'string' ? source['runId'] : '';
        const userId = typeof source['user_id'] === 'string' ? source['user_id'] : typeof source['userId'] === 'string' ? source['userId'] : '';
        const content = typeof source['content'] === 'string' ? source['content'].trim() : '';
        if (!id || !runId || !userId || !content) return null;
        return {
            id,
            run_id: runId,
            user_id: userId,
            user_name: typeof source['user_name'] === 'string' && source['user_name'].trim() ? source['user_name'].trim() : '러너',
            profile_image: typeof source['profile_image'] === 'string' ? source['profile_image'] : '',
            content,
            created_at: typeof source['created_at'] === 'string' ? source['created_at'] : '',
            is_mine: Boolean(source['is_mine'])
        };
    }

    private normalizeReactionType(value: unknown): ReactionType | null {
        const text = String(value || '').trim();
        return text === 'like' || text === 'fire' || text === 'clap' || text === 'strong' ? text : null;
    }

    private normalizeTrainingLoad(row: unknown): TrainingLoad {
        let source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        if (!('streak' in source) && source['data'] && typeof source['data'] === 'object') {
            source = source['data'] as Record<string, unknown>;
        }

        const statusRaw = String(source['status'] || EMPTY_TRAINING_LOAD.status);
        const status: TrainingLoadStatus = statusRaw === 'danger' || statusRaw === 'caution' || statusRaw === 'safe'
            ? statusRaw
            : 'safe';
        const weeklyIncrease = this.toNumber(source['weekly_increase_pct'] ?? source['weeklyIncreasePct']);
        const reasons = Array.isArray(source['reasons'])
            ? source['reasons'].filter((item): item is string => typeof item === 'string' && item.trim().length > 0)
            : [];
        const recommendRaw = source['recommend_rest'] ?? source['recommendRest'];
        const recommendRest = typeof recommendRaw === 'boolean'
            ? recommendRaw
            : String(recommendRaw || '').toLowerCase() === 'true';

        return {
            streak: Math.max(0, Math.round(this.toNumber(source['streak']) || 0)),
            weekly_increase_pct: weeklyIncrease,
            recommend_rest: recommendRest,
            reason: typeof source['reason'] === 'string' && source['reason'].trim()
                ? source['reason'].trim()
                : EMPTY_TRAINING_LOAD.reason,
            reasons,
            current_week_distance_km: this.round2(this.toNumber(source['current_week_distance_km'] ?? source['currentWeekDistanceKm']) || 0),
            previous_week_distance_km: this.round2(this.toNumber(source['previous_week_distance_km'] ?? source['previousWeekDistanceKm']) || 0),
            recent_avg_heart_rate: this.toNumber(source['recent_avg_heart_rate'] ?? source['recentAvgHeartRate']),
            baseline_avg_heart_rate: this.toNumber(source['baseline_avg_heart_rate'] ?? source['baselineAvgHeartRate']),
            heart_rate_delta_bpm: this.toNumber(source['heart_rate_delta_bpm'] ?? source['heartRateDeltaBpm']),
            negative_condition_streak: Math.max(0, Math.round(this.toNumber(source['negative_condition_streak'] ?? source['negativeConditionStreak']) || 0)),
            status,
            status_label: typeof source['status_label'] === 'string' && source['status_label'].trim()
                ? source['status_label'].trim()
                : status === 'danger' ? '위험' : status === 'caution' ? '주의' : '안전'
        };
    }

    private normalizeBadge(row: unknown): Badge | null {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const code = typeof source.code === 'string' ? source.code.trim() : '';
        const title = typeof source.title === 'string' ? source.title.trim() : '';
        const threshold = this.toNumber(source.threshold);
        if (!code || !title || threshold === null) return null;

        const progressSource = source.progress && typeof source.progress === 'object'
            ? source.progress as Record<string, unknown>
            : {};
        const progressThreshold = this.toNumber(progressSource.threshold);
        const current = this.toNumber(progressSource.current);
        const percent = this.toNumber(progressSource.percent);
        const progress: BadgeProgress = {
            current: current ?? 0,
            threshold: progressThreshold ?? threshold,
            percent: Math.max(0, Math.min(100, Math.round(percent ?? 0))),
            label: typeof progressSource.label === 'string' ? progressSource.label : ''
        };

        return {
            id: typeof source.id === 'string' || typeof source.id === 'number' ? source.id : code,
            code,
            title,
            description: typeof source.description === 'string' ? source.description : '',
            icon: typeof source.icon === 'string' && source.icon.trim() ? source.icon.trim() : 'fa-medal',
            condition_type: typeof source.condition_type === 'string' ? source.condition_type : '',
            threshold,
            achieved: Boolean(source.achieved),
            achieved_at: typeof source.achieved_at === 'string' ? source.achieved_at : null,
            progress
        };
    }

    private normalizeWeightLog(row: unknown): WeightLog | null {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const date = typeof source.date === 'string' ? source.date : '';
        const weight = this.toNumber(source.weight_kg ?? source.weightKg ?? source.weight);

        if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || weight === null || weight <= 0 || weight >= 1000) {
            return null;
        }

        return {
            id: typeof source.id === 'string' ? source.id : null,
            date,
            weight_kg: this.round1(weight),
            created_at: typeof source.created_at === 'string' ? source.created_at : ''
        };
    }

    private normalizeWeightSettings(row: unknown): WeightSettings | null {
        if (typeof row === 'number' || typeof row === 'string') {
            const targetValue = this.normalizedWeightTarget(row);
            if (targetValue === null) return null;
            return {
                target_weight_kg: targetValue,
                updated_at: ''
            };
        }

        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        if (!Object.keys(source).length) return null;

        const hasDirectTarget = (
            'target_weight_kg' in source ||
            'targetWeightKg' in source ||
            'target_weight' in source
        );
        if (!hasDirectTarget) {
            const nested = source['settings'] || source['data'];
            if (nested && nested !== row) {
                return this.normalizeWeightSettings(nested);
            }
            return null;
        }

        const target = this.normalizedWeightTarget(source.target_weight_kg ?? source.targetWeightKg ?? source.target_weight);
        if (target === null) return null;

        return {
            target_weight_kg: target,
            updated_at: typeof source.updated_at === 'string' ? source.updated_at : ''
        };
    }

    private normalizedWeightTarget(value: unknown): number | null {
        const target = this.toNumber(value);
        return target !== null && target > 0 && target < 1000 ? this.round1(target) : null;
    }

    private currentUserStorageIdentity(): string {
        const profile = this.profile;
        if (!profile) return '';

        return [
            profile.id,
            profile.username,
            profile.display_id,
            profile.email
        ]
            .map((value) => typeof value === 'string' ? value.trim() : '')
            .find(Boolean) || '';
    }

    private weightTargetStorageKeyForCurrentUser(): string | null {
        const identity = this.currentUserStorageIdentity();
        return identity ? `${this.weightTargetStorageKey}:${encodeURIComponent(identity)}` : null;
    }

    private pacerPersonaStorageKeyForCurrentUser(): string | null {
        const identity = this.currentUserStorageIdentity();
        return identity ? `${this.pacerPersonaStorageKey}:${encodeURIComponent(identity)}` : null;
    }

    private syncPacerPersonaLocalForProfile(): void {
        this.loadPacerPersonaLocal();
        this.pacerPersonaDraft = this.appSettings.pacerPersona;
    }

    private loadPacerPersonaLocal(): void {
        if (typeof window === 'undefined' || !window.localStorage) {
            this.pacerPersonaDraft = this.appSettings.pacerPersona;
            return;
        }

        try {
            const storageKey = this.pacerPersonaStorageKeyForCurrentUser();
            if (!storageKey) {
                this.pacerPersonaDraft = this.appSettings.pacerPersona;
                return;
            }

            const persona = this.normalizePacerPersona(window.localStorage.getItem(storageKey));
            this.appSettings.pacerPersona = persona || DEFAULT_APP_SETTINGS.pacerPersona;
            this.pacerPersonaDraft = this.appSettings.pacerPersona;
        } catch {
            this.pacerPersonaDraft = this.appSettings.pacerPersona;
        }
    }

    private persistPacerPersonaLocal(): void {
        if (typeof window === 'undefined' || !window.localStorage) return;

        try {
            const storageKey = this.pacerPersonaStorageKeyForCurrentUser();
            if (!storageKey) return;
            window.localStorage.setItem(storageKey, this.appSettings.pacerPersona);
        } catch {
            return;
        }
    }

    private syncWeightTargetLocalForProfile(): void {
        this.targetWeightKg = null;
        this.weightTargetInput = '';
        this.weightTargetStatus = '';
        this.removeLegacyWeightTargetLocal();
        this.loadWeightTargetLocal();
        this.refreshWeightDerivedState();
    }

    private loadWeightTargetLocal(): void {
        if (typeof window === 'undefined' || !window.localStorage) return;

        try {
            const storageKey = this.weightTargetStorageKeyForCurrentUser();
            if (!storageKey) return;

            const target = this.normalizedWeightTarget(window.localStorage.getItem(storageKey));
            if (target === null) return;

            this.targetWeightKg = target;
            this.weightTargetInput = target.toFixed(1);
        } catch {
            return;
        }
    }

    private persistWeightTargetLocal(target: number | null): void {
        if (typeof window === 'undefined' || !window.localStorage) return;

        try {
            const storageKey = this.weightTargetStorageKeyForCurrentUser();
            if (!storageKey) return;

            if (target === null) {
                window.localStorage.removeItem(storageKey);
                return;
            }
            window.localStorage.setItem(storageKey, target.toFixed(1));
        } catch {
            return;
        }
    }

    private removeLegacyWeightTargetLocal(): void {
        if (typeof window === 'undefined' || !window.localStorage) return;

        try {
            window.localStorage.removeItem(this.weightTargetStorageKey);
        } catch {
            return;
        }
    }

    private normalizeGoal(row: unknown): Goal | null {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const yearMonth = this.normalizeYearMonth(source['year_month'] ?? source['yearMonth']);
        const goalType = this.normalizeGoalType(source['goal_type'] ?? source['goalType'] ?? source['type']);
        const targetValue = this.toNumber(source['target_value'] ?? source['targetValue'] ?? source['value']);
        if (!yearMonth || !goalType || targetValue === null || targetValue <= 0) return null;

        return {
            id: typeof source['id'] === 'string' ? source['id'] : null,
            year_month: yearMonth,
            goal_type: goalType,
            target_value: goalType === 'count' || goalType === 'pace' ? Math.round(targetValue) : this.round2(targetValue),
            created_at: typeof source['created_at'] === 'string' ? source['created_at'] : ''
        };
    }

    private normalizeGoalProgress(row: unknown): GoalProgress | null {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const goal = this.normalizeGoal(source);
        if (!goal) return null;

        const currentValue = this.toNumber(source['current_value'] ?? source['currentValue']);
        const remainingValue = this.toNumber(source['remaining_value'] ?? source['remainingValue']) || 0;
        const percent = this.toNumber(source['percent']) || 0;
        const label = typeof source['label'] === 'string' && source['label'].trim()
            ? source['label'].trim()
            : this.goalTypeLabel(goal.goal_type);

        return {
            ...goal,
            label,
            current_value: currentValue,
            remaining_value: remainingValue,
            percent: Math.max(0, Math.min(100, Math.round(percent))),
            achieved: Boolean(source['achieved']),
            unit: typeof source['unit'] === 'string' ? source['unit'] : this.goalTypeUnit(goal.goal_type),
            target_text: typeof source['target_text'] === 'string' ? source['target_text'] : this.goalValueText(goal.goal_type, goal.target_value),
            current_text: typeof source['current_text'] === 'string' ? source['current_text'] : this.goalValueText(goal.goal_type, currentValue),
            message: typeof source['message'] === 'string' ? source['message'] : ''
        };
    }

    private normalizeGoalHistory(row: unknown): GoalHistory | null {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const yearMonth = this.normalizeYearMonth(source['year_month'] ?? source['yearMonth']);
        if (!yearMonth) return null;

        const items = Array.isArray(source['items'])
            ? source['items']
                .map((item) => this.normalizeGoalProgress(item))
                .filter((item): item is GoalProgress => Boolean(item))
            : [];
        const goalCount = this.toNumber(source['goal_count'] ?? source['goalCount']) ?? items.length;
        const achievedCount = this.toNumber(source['achieved_count'] ?? source['achievedCount']) ?? items.filter((item) => item.achieved).length;

        return {
            year_month: yearMonth,
            label: typeof source['label'] === 'string' && source['label'].trim()
                ? source['label'].trim()
                : yearMonth.replace('-', '.'),
            goal_count: Math.round(goalCount),
            achieved_count: Math.round(achievedCount),
            achieved: Boolean(source['achieved']),
            items
        };
    }

    private normalizeRankingEntry(row: unknown): RankingEntry | null {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const userId = typeof source['user_id'] === 'string' ? source['user_id'] : '';
        const name = typeof source['name'] === 'string' && source['name'].trim() ? source['name'].trim() : '러너';
        if (!userId) return null;

        const distance = this.round2(this.toNumber(source['distance_km'] ?? source['distanceKm']) || 0);
        const rank = Math.max(1, Math.round(this.toNumber(source['rank']) || 1));
        const rawMedal = source['medal'];
        const medal: RankingEntry['medal'] = rawMedal === 'gold' || rawMedal === 'silver' || rawMedal === 'bronze'
            ? rawMedal
            : '';

        return {
            rank,
            user_id: userId,
            display_id: typeof source['display_id'] === 'string' && source['display_id'].trim()
                ? source['display_id'].trim()
                : userId,
            name,
            profile_image: typeof source['profile_image'] === 'string' ? source['profile_image'] : '',
            distance_km: distance,
            distance_text: this.distanceText(distance),
            run_count: Math.max(0, Math.round(this.toNumber(source['run_count'] ?? source['runCount']) || 0)),
            bar_percent: Math.max(0, Math.min(100, Math.round(this.toNumber(source['bar_percent'] ?? source['barPercent']) || 0))),
            is_viewer: Boolean(source['is_viewer'] ?? source['isViewer']),
            is_following: Boolean(source['is_following'] ?? source['isFollowing']),
            is_follower: Boolean(source['is_follower'] ?? source['isFollower']),
            is_mutual: Boolean(source['is_mutual'] ?? source['isMutual']),
            highlight: Boolean(source['highlight']),
            medal,
            privacy: source['privacy'] === 'private' ? 'private' : 'public'
        };
    }

    private normalizeCommunityNotifications(rows: unknown): CommunityNotification[] {
        const source = Array.isArray(rows) ? rows : [];
        return source
            .map((row) => this.normalizeCommunityNotification(row))
            .filter((item): item is CommunityNotification => Boolean(item));
    }

    private normalizeCommunityNotification(row: unknown): CommunityNotification | null {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const id = typeof source['id'] === 'string' ? source['id'] : '';
        const typeSource = String(source['type'] || '');
        let type: CommunityNotification['type'] | null = null;
        if (typeSource === 'follow' || typeSource === 'reaction' || typeSource === 'comment') {
            type = typeSource;
        }
        if (!id || !type) return null;

        const actorName = typeof source['actor_name'] === 'string' && source['actor_name'].trim()
            ? source['actor_name'].trim()
            : '러너';
        const fallbackMessage = type === 'follow'
            ? `${actorName}님이 팔로우하기 시작했어.`
            : type === 'comment'
                ? `${actorName}님이 내 러닝에 댓글을 남겼어.`
                : `${actorName}님이 내 러닝을 응원했어.`;

        return {
            id,
            user_id: typeof source['user_id'] === 'string' ? source['user_id'] : '',
            actor_id: typeof source['actor_id'] === 'string' ? source['actor_id'] : '',
            actor_name: actorName,
            type,
            message: typeof source['message'] === 'string' && source['message'].trim() ? source['message'].trim() : fallbackMessage,
            created_at: typeof source['created_at'] === 'string' ? source['created_at'] : '',
            read_at: typeof source['read_at'] === 'string' ? source['read_at'] : '',
            run_id: typeof source['run_id'] === 'string' ? source['run_id'] : ''
        };
    }

    private normalizeSocialProfiles(rows: unknown): SocialProfile[] {
        const source = Array.isArray(rows) ? rows : [];
        return source
            .map((row) => this.normalizeSocialProfile(row))
            .filter((profile): profile is SocialProfile => Boolean(profile));
    }

    private normalizeSocialProfileDetail(row: unknown): SocialProfileDetail | null {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const profile = this.normalizeSocialProfile(source['profile']);
        if (!profile) return null;

        return {
            profile,
            lists_public: Boolean(source['lists_public'] ?? true),
            following: this.normalizeSocialProfiles(source['following']),
            followers: this.normalizeSocialProfiles(source['followers']),
            media: this.normalizeProfileMediaItems(source['media'], profile)
        };
    }

    private normalizeProfileMediaItems(rows: unknown, owner: SocialProfile | null): GalleryItem[] {
        const source = Array.isArray(rows) ? rows : [];
        const feedUser = owner ? this.socialProfileFeedUser(owner) : null;
        return source
            .map((row) => {
                const item = row && typeof row === 'object' ? row as Record<string, unknown> : {};
                const media = this.normalizeRunMedia(item['media'] || item);
                const run = this.normalizeRun(item['run']);
                if (!media || !run) return null;

                const km = this.distanceText(run.distance_km, true);
                const date = this.displayDate(run.date, false);
                return {
                    id: media.id,
                    km,
                    date,
                    stats: [],
                    runType: run.run_type,
                    altText: `${owner?.name || '러너'} ${date} ${km} 러닝 첨부 ${this.mediaTypeLabel(media.media_type)}`,
                    imageUrl: media.media_url,
                    media,
                    run,
                    owner: feedUser || undefined,
                    mediaType: media.media_type
                } as GalleryItem;
            })
            .filter((item): item is GalleryItem => Boolean(item));
    }

    private normalizeSocialProfile(row: unknown): SocialProfile | null {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const id = typeof source['id'] === 'string' ? source['id'] : '';
        if (!id) return null;

        const displayId = typeof source['display_id'] === 'string' && source['display_id'].trim()
            ? source['display_id'].trim()
            : typeof source['email'] === 'string'
                ? source['email']
                : id;
        const name = typeof source['name'] === 'string' && source['name'].trim()
            ? source['name'].trim()
            : '러너';
        const badges = Array.isArray(source['badges'])
            ? source['badges']
                .map((item) => this.normalizeBadge(item))
                .filter((badge): badge is Badge => Boolean(badge))
            : [];
        const earnedBadgeCount = Math.max(0, Math.round(this.toNumber(source['earned_badge_count'] ?? source['earnedBadgeCount']) ?? badges.length));
        const totalBadgeCount = Math.max(0, Math.round(this.toNumber(source['total_badge_count'] ?? source['totalBadgeCount']) ?? badges.length));

        return {
            id,
            email: typeof source['email'] === 'string' ? source['email'] : '',
            display_id: displayId,
            name,
            running_start_date: this.normalizeDateKey(source['running_start_date'] ?? source['runningStartDate']) || this.todayDateKey,
            profile_image: typeof source['profile_image'] === 'string' ? source['profile_image'] : '',
            is_public: Boolean(source['is_public']),
            is_me: Boolean(source['is_me']),
            is_following: Boolean(source['is_following']),
            is_follower: Boolean(source['is_follower']),
            is_mutual: Boolean(source['is_mutual']),
            following_count: Math.max(0, Math.round(this.toNumber(source['following_count'] ?? source['followingCount']) || 0)),
            follower_count: Math.max(0, Math.round(this.toNumber(source['follower_count'] ?? source['followerCount']) || 0)),
            stats_public: Boolean(source['stats_public']),
            stats: this.normalizePublicUserStats(source['stats']),
            badges_public: Boolean(source['badges_public']),
            badges,
            earned_badge_count: earnedBadgeCount,
            total_badge_count: totalBadgeCount,
            achievement_rate: Math.max(0, Math.min(100, Math.round(this.toNumber(source['achievement_rate'] ?? source['achievementRate']) ?? 0)))
        };
    }

    private normalizePublicUserStats(row: unknown): PublicUserStats | null {
        if (!row || typeof row !== 'object') return null;
        const source = row as Record<string, unknown>;
        const totalDistance = this.toNumber(source['total_distance_km'] ?? source['totalDistanceKm'])
            ?? this.distanceKmFromText(source['total_distance_text']);
        const monthDistance = this.toNumber(source['this_month_distance_km'] ?? source['thisMonthDistanceKm'])
            ?? this.distanceKmFromText(source['this_month_distance_text']);
        const longestDistance = this.toNumber(source['longest_distance_km'] ?? source['longestDistanceKm'])
            ?? this.distanceKmFromText(source['longest_distance_text']);
        return {
            total_distance_km: totalDistance || 0,
            total_distance_text: typeof source['total_distance_text'] === 'string' ? source['total_distance_text'] : '0.00km',
            run_count: Math.max(0, Math.round(this.toNumber(source['run_count'] ?? source['runCount']) || 0)),
            this_month_distance_km: monthDistance || 0,
            this_month_distance_text: typeof source['this_month_distance_text'] === 'string' ? source['this_month_distance_text'] : '0.00km',
            this_month_run_count: Math.max(0, Math.round(this.toNumber(source['this_month_run_count'] ?? source['thisMonthRunCount']) || 0)),
            longest_distance_km: longestDistance || 0,
            longest_distance_text: typeof source['longest_distance_text'] === 'string' ? source['longest_distance_text'] : '0.00km',
            best_pace: typeof source['best_pace'] === 'string' ? source['best_pace'] : '-',
            latest_run_date_text: typeof source['latest_run_date_text'] === 'string' ? source['latest_run_date_text'] : '-'
        };
    }

    private applySocialProfileUpdate(profile: SocialProfile): void {
        const replace = (rows: SocialProfile[]) => rows.map((row) => row.id === profile.id ? profile : row);
        this.friendSearchResults = replace(this.friendSearchResults);
        this.followingUsers = replace(this.followingUsers);
        this.followerUsers = replace(this.followerUsers);
        if (this.selectedFriendProfile?.id === profile.id) {
            this.selectedFriendProfile = profile;
        }
        if (this.viewedProfile?.id === profile.id) {
            this.viewedProfile = profile;
        }
        this.viewedProfileFollowingUsers = replace(this.viewedProfileFollowingUsers);
        this.viewedProfileFollowerUsers = replace(this.viewedProfileFollowerUsers);
    }

    private syncSelectedFriendProfile(): void {
        const currentId = this.selectedFriendProfile?.id || '';
        const allProfiles = [
            ...this.friendSearchResults,
            ...this.activeFriendList,
            ...this.followingUsers,
            ...this.followerUsers
        ];
        if (currentId) {
            const current = allProfiles.find((profile) => profile.id === currentId);
            if (current) {
                this.selectedFriendProfile = current;
                return;
            }
        }
        this.selectedFriendProfile = null;
    }

    private normalizeChallenge(row: unknown): Challenge | null {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const id = typeof source['id'] === 'string' ? source['id'] : '';
        const title = typeof source['title'] === 'string' ? source['title'].trim() : '';
        const type = this.normalizeChallengeType(source['type']);
        const startDate = this.normalizeDateKey(source['start_date'] ?? source['startDate']);
        const endDate = this.normalizeDateKey(source['end_date'] ?? source['endDate']);
        if (!id || !title || !type || !startDate || !endDate) return null;

        const members = Array.isArray(source['members'])
            ? source['members']
                .map((member) => this.normalizeChallengeMember(member))
                .filter((member): member is ChallengeMember => Boolean(member))
            : [];
        const goalValue = this.toNumber(source['goal_value'] ?? source['goalValue']) || 0;
        const progressPercent = Math.max(0, Math.min(100, Math.round(this.toNumber(source['progress_percent'] ?? source['progressPercent']) || 0)));
        const resultStatus = source['result_status'] === 'achieved' || source['result_status'] === 'missed'
            ? source['result_status']
            : 'in_progress';
        const creatorId = typeof source['creator_id'] === 'string' ? source['creator_id'] : '';
        const creatorName = typeof source['creator_name'] === 'string' ? source['creator_name'] : '';
        const viewerOwned = Boolean(source['viewer_owned'] ?? source['viewerOwned'])
            || this.isCurrentUserChallengeOwner(creatorId, creatorName, members);

        return {
            id,
            title,
            type,
            type_label: this.textValue(source['type_label'], this.challengeTypeLabel(type)),
            goal_value: goalValue,
            start_date: startDate,
            end_date: endDate,
            creator_id: creatorId,
            creator_name: creatorName,
            invite_code: typeof source['invite_code'] === 'string' ? source['invite_code'] : '',
            created_at: typeof source['created_at'] === 'string' ? source['created_at'] : '',
            members,
            status: typeof source['status'] === 'string' ? source['status'] : 'active',
            status_label: this.textValue(source['status_label'], '참여중'),
            member_count: Math.round(this.toNumber(source['member_count'] ?? source['memberCount']) || members.length),
            viewer_joined: Boolean(source['viewer_joined']),
            viewer_owned: viewerOwned,
            current_value: this.toNumber(source['current_value'] ?? source['currentValue']) || 0,
            target_value: this.toNumber(source['target_value'] ?? source['targetValue']) || goalValue,
            remaining_value: this.toNumber(source['remaining_value'] ?? source['remainingValue']) || 0,
            progress_percent: progressPercent,
            achieved: Boolean(source['achieved']),
            goal_text: this.challengeValueText(type, goalValue),
            current_text: this.challengeValueText(type, source['current_value']),
            target_text: this.challengeValueText(type, source['target_value'] ?? goalValue),
            remaining_text: this.challengeValueText(type, source['remaining_value']),
            d_day: this.textValue(source['d_day'], '-'),
            period_text: this.textValue(source['period_text'], `${this.displayDate(startDate, false)} - ${this.displayDate(endDate, false)}`),
            result_status: resultStatus,
            result_text: this.textValue(source['result_text'], `${progressPercent}%`)
        };
    }

    private isCurrentUserChallengeOwner(creatorId: string, creatorName: string, members: ChallengeMember[]): boolean {
        const profile = this.profile;
        if (!profile) return false;

        const ids = new Set([
            profile.id,
            profile.username,
            profile.display_id,
            profile.email
        ].map((value) => typeof value === 'string' ? value.trim() : '').filter(Boolean));
        const names = new Set([
            profile.name,
            profile.display_name
        ].map((value) => typeof value === 'string' ? value.trim() : '').filter(Boolean));

        if (creatorId && ids.has(creatorId)) return true;
        if (creatorName && names.has(creatorName)) return true;

        return members.some((member) => {
            const memberId = member.user_id.trim();
            const memberName = member.user_name.trim();
            return Boolean(
                creatorId && memberId === creatorId && ids.has(memberId)
                || creatorName && memberName === creatorName && names.has(memberName)
            );
        });
    }

    private normalizeChallengeMember(row: unknown): ChallengeMember | null {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const userId = typeof source['user_id'] === 'string' ? source['user_id'] : '';
        if (!userId) return null;

        return {
            challenge_id: typeof source['challenge_id'] === 'string' ? source['challenge_id'] : '',
            user_id: userId,
            user_name: this.textValue(source['user_name'], '러너'),
            joined_at: typeof source['joined_at'] === 'string' ? source['joined_at'] : '',
            contributed_value: this.toNumber(source['contributed_value'] ?? source['contributedValue']) || 0,
            contributed_text: typeof source['contributed_text'] === 'string' ? source['contributed_text'] : '',
            progress_percent: Math.max(0, Math.min(100, Math.round(this.toNumber(source['progress_percent'] ?? source['progressPercent']) || 0))),
            rank: Math.round(this.toNumber(source['rank']) || 0)
        };
    }

    private normalizeCycleLog(row: unknown): CycleLog | null {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const startDate = this.normalizeDateKey(source['start_date'] ?? source['startDate']);
        const endDate = this.normalizeDateKey(source['end_date'] ?? source['endDate']) || startDate;
        const phase = this.normalizeCyclePhase(source['cycle_phase'] ?? source['cyclePhase']);
        const flowLevel = this.normalizeCycleFlowLevel(source['flow_level'] ?? source['flowLevel'] ?? source['flow']);
        const conditionEmoji = this.normalizeCycleConditionEmoji(source['condition_emoji'] ?? source['conditionEmoji'] ?? source['condition']);
        if (!startDate || !endDate) return null;

        return {
            id: typeof source['id'] === 'string' ? source['id'] : null,
            start_date: startDate <= endDate ? startDate : endDate,
            end_date: endDate >= startDate ? endDate : startDate,
            cycle_phase: phase,
            flow_level: flowLevel,
            condition_emoji: conditionEmoji,
            note: typeof source['note'] === 'string' ? source['note'].trim() : ''
        };
    }

    private normalizeCycleSummary(row: unknown): CycleSummary {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const averageCycleDays = this.toNumber(source['average_cycle_days'] ?? source['averageCycleDays']);
        const averagePeriodDays = this.toNumber(source['average_period_days'] ?? source['averagePeriodDays']);
        const currentPhase = this.normalizeCyclePhaseOrNull(source['current_phase'] ?? source['currentPhase']);
        const currentPhaseLabel = typeof source['current_phase_label'] === 'string' && source['current_phase_label'].trim()
            ? source['current_phase_label'].trim()
            : currentPhase ? this.cyclePhaseLabel(currentPhase) : null;

        return {
            average_cycle_days: averageCycleDays && averageCycleDays > 0 ? Math.round(averageCycleDays) : EMPTY_CYCLE_SUMMARY.average_cycle_days,
            average_period_days: averagePeriodDays && averagePeriodDays > 0 ? Math.max(7, Math.round(averagePeriodDays)) : EMPTY_CYCLE_SUMMARY.average_period_days,
            next_start_date: this.normalizeDateKey(source['next_start_date'] ?? source['nextStartDate']),
            current_phase: currentPhase,
            current_phase_label: currentPhaseLabel,
            log_count: this.toNumber(source['log_count'] ?? source['logCount']) || 0,
            menstrual_log_count: this.toNumber(source['menstrual_log_count'] ?? source['menstrualLogCount']) || 0
        };
    }

    private normalizeRunMedia(row: unknown): RunMedia | null {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const id = typeof source['id'] === 'string' ? source['id'] : '';
        const runId = typeof source['run_id'] === 'string' ? source['run_id'] : '';
        const mediaUrl = this.resolveMediaUrl(source['media_url']);
        const mediaType = source['media_type'] === 'video' ? 'video' : source['media_type'] === 'photo' ? 'photo' : null;
        if (!id || !runId || !mediaUrl || !mediaType) return null;

        return {
            id,
            run_id: runId,
            media_url: mediaUrl,
            media_type: mediaType,
            created_at: typeof source['created_at'] === 'string' ? source['created_at'] : ''
        };
    }

    private resolveMediaUrl(value: unknown): string {
        const raw = typeof value === 'string' ? value.trim() : '';
        if (!raw) return '';
        if (/^(data|blob):/i.test(raw)) return raw;
        if (raw.startsWith('//')) return `https:${raw}`;

        const nativeLocal = isNativeLocalOrigin();
        try {
            const base = typeof window !== 'undefined' && window.location?.href
                ? window.location.href
                : `${RUNNINGMATE_API_ORIGIN}/`;
            const parsed = new URL(raw, base);
            const localHost = parsed.hostname === 'localhost' || parsed.hostname === '127.0.0.1' || parsed.hostname === '0.0.0.0';
            const localNative = parsed.protocol === 'capacitor:' || parsed.protocol === 'ionic:' || parsed.protocol === 'file:';
            if (localHost || (nativeLocal && localNative)) {
                return `${RUNNINGMATE_API_ORIGIN}${parsed.pathname}${parsed.search}${parsed.hash}`;
            }
            if (nativeLocal && raw.startsWith('/')) {
                return `${RUNNINGMATE_API_ORIGIN}${parsed.pathname}${parsed.search}${parsed.hash}`;
            }
            return raw;
        } catch {
            if (nativeLocal) {
                return `${RUNNINGMATE_API_ORIGIN}/${raw.replace(/^\/+/, '')}`;
            }
            return raw;
        }
    }

    private normalizeMusicTrack(row: unknown): MusicTrack | null {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const attributes = source['attributes'] && typeof source['attributes'] === 'object'
            ? source['attributes'] as Record<string, unknown>
            : {};
        const artwork = attributes['artwork'] && typeof attributes['artwork'] === 'object'
            ? attributes['artwork'] as Record<string, unknown>
            : {};
        const title = this.textValue(source['title'] ?? source['name'] ?? attributes['name'], '').trim();
        const artist = this.textValue(source['artist'] ?? source['artistName'] ?? attributes['artistName'], '').trim();
        if (!title || !artist) return null;

        let artworkUrl = this.textValue(source['album_art_url'] ?? source['albumArtUrl'] ?? source['artworkUrl'] ?? artwork['url'], '');
        artworkUrl = artworkUrl.replace('{w}', '160').replace('{h}', '160');
        const url = this.textValue(source['url'] ?? source['music_url'] ?? source['musicUrl'] ?? attributes['url'], '');
        const id = this.textValue(source['id'], '') || `${title}:${artist}:${url}`;

        return {
            id,
            title,
            artist,
            album: this.textValue(source['album'] ?? source['albumName'] ?? attributes['albumName'], ''),
            album_art_url: artworkUrl,
            url
        };
    }

    private normalizeDayNote(row: unknown): CalendarNote | null {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const date = typeof source.date === 'string' ? source.date : '';
        const memo = typeof source.memo === 'string' ? source.memo.trim() : '';
        if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || !memo) return null;

        return {
            date,
            memo,
            updated_at: typeof source.updated_at === 'string' ? source.updated_at : ''
        };
    }

    private normalizeWeatherDay(dateKey: string, row: unknown): WeatherDay | null {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const date = typeof source.date === 'string' ? source.date : dateKey;
        if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) return null;

        const tone = this.normalizeWeatherTone(source.tone);
        const icon = typeof source.icon === 'string' && source.icon.trim() ? source.icon.trim() : this.weatherIconForTone(tone);
        const hourly = Array.isArray(source.hourly)
            ? source.hourly
                .map((item) => this.normalizeWeatherHourly(item))
                .filter((item): item is WeatherHourly => Boolean(item))
            : [];

        return {
            date,
            icon,
            tone,
            summary: this.textValue(source.summary, '날씨 정보'),
            tempText: this.textValue(source.tempText, '-'),
            popText: this.textValue(source.popText, '-'),
            rainText: this.textValue(source.rainText, '-'),
            snowText: this.textValue(source.snowText, '-'),
            humidityText: this.textValue(source.humidityText, '-'),
            windText: this.textValue(source.windText, '-'),
            hourly,
            locationName: this.textValue(source.locationName || source.location_name, ''),
            locationSource: this.textValue(source.locationSource || source.location_source, ''),
            stored: Boolean(source.stored),
            capturedAt: this.textValue(source.capturedAt || source.captured_at, '')
        };
    }

    private normalizeWeatherHourly(row: unknown): WeatherHourly | null {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const time = typeof source.time === 'string' ? source.time.trim() : '';
        if (!time) return null;

        const tone = this.normalizeWeatherTone(source.tone);
        const icon = typeof source.icon === 'string' && source.icon.trim() ? source.icon.trim() : this.weatherIconForTone(tone);
        return {
            time,
            icon,
            tone,
            summary: this.textValue(source.summary, '날씨'),
            tempText: this.textValue(source.tempText, '-'),
            popText: this.textValue(source.popText, '-'),
            humidityText: this.textValue(source.humidityText, '-'),
            windText: this.textValue(source.windText, '-')
        };
    }

    private normalizeChatSession(row: unknown): ChatSession | null {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const id = typeof source.id === 'string' ? source.id : '';
        if (!id) return null;

        const messages = Array.isArray(source.messages)
            ? source.messages
                .map((message) => this.normalizeChatMessage(message))
                .filter((message): message is ChatMessage => Boolean(message))
            : [];
        if (!messages.length) return null;

        const firstUser = messages.find((message) => message.sender === 'user')?.text || messages[0].text;
        const title = typeof source.title === 'string' && source.title.trim() ? source.title.trim() : this.compactChatText(firstUser, 32);
        const previewSource = typeof source.preview === 'string' && source.preview.trim()
            ? source.preview
            : messages[messages.length - 1].text;
        const dayKey = this.normalizeDateKey(source.day_key ?? source.dayKey)
            || this.chatDateKey(source.updated_at)
            || this.chatDateKey(source.created_at)
            || this.chatDateKey(messages[0].created_at)
            || '';

        return {
            id,
            title,
            created_at: typeof source.created_at === 'string' ? source.created_at : '',
            updated_at: typeof source.updated_at === 'string' ? source.updated_at : '',
            day_key: dayKey,
            preview: this.compactChatText(previewSource, 54),
            message_count: this.toNumber(source.message_count) || messages.length,
            messages
        };
    }

    private normalizeChatMessage(row: unknown): ChatMessage | null {
        const source = row && typeof row === 'object' ? row as Record<string, unknown> : {};
        const sender = source.sender === 'user' ? 'user' : source.sender === 'ai' ? 'ai' : null;
        const text = typeof source.text === 'string' ? source.text.trim() : '';
        if (!sender || !text) return null;

        return {
            sender,
            text,
            created_at: typeof source.created_at === 'string' ? source.created_at : '',
            streaming: false
        };
    }

    private upsertChatSession(row: unknown): void {
        const session = this.normalizeChatSession(row);
        if (!session) return;

        this.chatSessions = [
            session,
            ...this.chatSessions.filter((item) => item.id !== session.id)
        ];
    }

    private refreshDerivedState(): void {
        const monthRecords = this.runs.filter((run) => run.date.startsWith(this.activeYearMonth));
        const monthRuns = monthRecords.filter((run) => this.isRunningRecord(run));
        if (this.selectedCalendarDate && !this.selectedCalendarDate.startsWith(this.activeYearMonth)) {
            this.selectedCalendarDate = null;
            this.calendarMemoText = '';
            this.calendarMemoStatus = '';
        }

        this.homeData = this.buildHomeData(monthRuns);
        this.goalProgressCards = this.buildGoalProgressCards(monthRuns);
        this.statCards = this.buildStatCards();
        this.summaryCards = this.buildSummaryCards();
        this.homeRecentRuns = monthRuns.slice(0, 4);
        this.cycleDayMap = this.buildCycleDayMap();
        this.calendarCells = this.buildCalendarCells();
        this.calendarStats = this.buildCalendarStats();
        this.selectedCalendarRuns = this.buildSelectedCalendarRuns();
        this.refreshWeightDerivedState();
        this.chartCards = this.buildChartCards();
        this.hydrationPattern = this.buildHydrationPattern();
        this.runTypeStats = this.buildRunTypeStats(monthRecords);
        this.cyclePatternStats = this.buildCyclePatternStats();
        this.miniStats = this.buildMiniStats();
        this.galleryItems = this.buildGalleryItems();
        this.syncSelectedJournalDate();
        this.journalCalendarCells = this.buildJournalCalendarCells();
        if (!this.shouldShowChatDayPrompt && !this.activeChatSessionId && (!this.chatMessages.length || (this.chatMessages.length === 1 && this.chatMessages[0].sender === 'ai'))) {
            this.chatMessages = this.buildChatMessages();
        }
    }

    private refreshWeightDerivedState(): void {
        this.visibleWeightLogs = this.periodWeightLogs().slice().reverse().slice(0, 8);
        this.weightCalendarCells = this.buildWeightCalendarCells();
        this.weightContextStats = this.buildWeightContextStats();
        this.weightChartPoints = this.buildWeightTrendPoints();
        this.weightChartSegments = this.buildTrendSegments(this.weightChartPoints);
        this.weightRunBars = this.buildWeightRunBars();
    }

    private periodWeightLogs(): WeightLog[] {
        const range = this.weightPeriodRange();
        return [...this.weightLogs]
            .filter((log) => !range.start || log.date >= range.start)
            .filter((log) => !range.end || log.date <= range.end)
            .sort((a, b) => a.date.localeCompare(b.date));
    }

    private periodRunsForWeight(): RunRecord[] {
        const range = this.weightPeriodRange();
        return this.runs
            .filter((run) => !range.start || run.date >= range.start)
            .filter((run) => !range.end || run.date <= range.end)
            .sort((a, b) => b.date.localeCompare(a.date));
    }

    private weightPeriodRange(): { start: string | null; end: string | null } {
        if (this.activeWeightPeriod === 'all') {
            const dates = [
                ...this.weightLogs.map((log) => log.date),
                ...this.runs.map((run) => run.date)
            ].sort();
            return {
                start: dates[0] || null,
                end: dates[dates.length - 1] || null
            };
        }

        const days = this.activeWeightPeriod === '1m' ? 31 : 93;
        const end = new Date();
        const start = this.addDays(end, -days);
        return {
            start: this.dateKey(start),
            end: this.dateKey(end)
        };
    }

    private buildWeightCalendarCells(): WeightCalendarCell[] {
        const [year, month] = this.activeWeightYearMonth.split('-').map(Number);
        const first = new Date(year, month - 1, 1);
        const daysInMonth = new Date(year, month, 0).getDate();
        const todayKey = this.todayDateKey;
        const weightByDate = new Map(this.weightLogs.map((log) => [log.date, log]));

        const cells: WeightCalendarCell[] = Array.from({ length: first.getDay() }, (_, index) => ({
            key: `weight-empty-${index}`,
            day: null,
            className: 'cal-empty',
            runCount: 0
        }));

        for (let day = 1; day <= daysInMonth; day++) {
            const key = this.dateKey(new Date(year, month - 1, day));
            const log = weightByDate.get(key) || null;
            const classList = ['cal-day', 'weight-cal-day'];
            if (key === todayKey) classList.push('today-marker');
            if (key > todayKey) classList.push('future');
            if (log) classList.push('has-weight');

            cells.push({
                key,
                day,
                className: classList.join(' '),
                dotClass: '',
                ariaLabel: `${this.displayDate(key, true)}${log ? `, 체중 ${log.weight_kg.toFixed(1)}kg` : ', 체중 기록 없음'}`,
                runCount: 0,
                weightText: log ? `${log.weight_kg.toFixed(1)}kg` : ''
            });
        }

        return cells;
    }

    private buildWeightTrendPoints(): TrendPoint[] {
        const logs = this.periodWeightLogs();
        if (!logs.length) return [];

        const bounds = this.weightChartAxisBounds();
        if (!bounds) return [];

        const weights = logs.map((log) => log.weight_kg);
        const min = Math.min(...weights);
        const max = Math.max(...weights);
        const spread = Math.max(0.8, max - min);

        return logs.map((log) => {
            const x = this.dateX(log.date, bounds.start, bounds.end);
            const y = logs.length === 1 ? 48 : 18 + ((max - log.weight_kg) / spread) * 64;
            const valueText = `${log.weight_kg.toFixed(1)}kg`;
            return {
                id: `weight-${log.date}`,
                x,
                y,
                label: this.displayDate(log.date, false),
                valueText,
                title: `${this.displayDate(log.date, true)} 체중 ${valueText}`
            };
        });
    }

    private buildWeightRunBars(): WeightRunBar[] {
        const weeklyRuns = this.weightWeeklyRunTotals();
        if (!weeklyRuns.length) return [];

        const bounds = this.weightChartAxisBounds();
        if (!bounds) return [];

        const max = Math.max(...weeklyRuns.map((point) => point.distance), 1);
        return weeklyRuns.map((point) => {
            const x = this.dateX(point.date, bounds.start, bounds.end);
            const height = Math.max(12, Math.min(100, (point.distance / max) * 100));
            const valueText = this.distanceText(point.distance);
            return {
                id: `run-${point.date}`,
                x,
                height,
                valueText,
                title: `${this.displayDate(point.date, true)} 주간 러닝 ${valueText}`
            };
        });
    }

    private buildWeightContextStats(): WeightContextStat[] {
        const logs = this.periodWeightLogs();
        const runs = this.periodRunsForWeight();
        const weeklyRuns = this.weightWeeklyRunTotals(runs);
        const totalDistance = this.round2(runs.reduce((sum, run) => sum + run.distance_km, 0));
        const weeklyAverage = weeklyRuns.length ? this.round2(totalDistance / weeklyRuns.length) : 0;
        let changeValue = '기록 대기';
        let changeTone = 'same';

        if (logs.length >= 2) {
            const diff = this.round1(logs[logs.length - 1].weight_kg - logs[0].weight_kg);
            const sign = diff > 0 ? '+' : '';
            changeValue = `${sign}${diff.toFixed(1)}kg`;
            changeTone = diff < 0 ? 'down' : diff > 0 ? 'up' : 'same';
        }

        return [
            { id: 'weight-change', label: '체중 변화', value: changeValue, tone: changeTone },
            { id: 'run-total', label: '러닝 합계', value: this.distanceText(totalDistance) },
            { id: 'run-weekly', label: '주당 평균', value: weeklyRuns.length ? this.distanceText(weeklyAverage) : '-' }
        ];
    }

    private weightWeeklyRunTotals(runs: RunRecord[] = this.periodRunsForWeight()): { date: string; distance: number }[] {
        const weekly = new Map<string, number>();
        for (const run of runs) {
            const date = this.parseDate(run.date);
            if (!date) continue;
            const key = this.dateKey(this.weekStart(date));
            weekly.set(key, this.round2((weekly.get(key) || 0) + run.distance_km));
        }

        return Array.from(weekly.entries())
            .map(([date, distance]) => ({ date, distance }))
            .sort((a, b) => a.date.localeCompare(b.date));
    }

    private weightChartAxisDates(): string[] {
        return [
            ...this.periodWeightLogs().map((log) => log.date),
            ...this.weightWeeklyRunTotals().map((point) => point.date)
        ];
    }

    private weightChartAxisBounds(): { start: Date; end: Date } | null {
        const dates = this.weightChartAxisDates();
        if (!dates.length) return null;

        const range = this.weightPeriodRange();
        return this.dateBounds(range.start, range.end, dates);
    }

    private buildTrendSegments(points: TrendPoint[]): TrendSegment[] {
        const segments: TrendSegment[] = [];
        for (let index = 1; index < points.length; index++) {
            const prev = points[index - 1];
            const current = points[index];
            const dx = current.x - prev.x;
            const dy = current.y - prev.y;
            const width = Math.sqrt(dx * dx + dy * dy);
            const angle = Math.atan2(dy, dx) * (180 / Math.PI);
            segments.push({
                id: `${prev.id}-${current.id}`,
                left: prev.x,
                top: prev.y,
                width,
                transform: `rotate(${angle}deg)`
            });
        }
        return segments;
    }

    private dateBounds(start: string | null, end: string | null, fallbackDates: string[]): { start: Date; end: Date } {
        const dates = fallbackDates
            .map((date) => this.parseDate(date))
            .filter((date): date is Date => Boolean(date))
            .sort((a, b) => a.getTime() - b.getTime());
        const fallbackStart = dates.length ? dates[0] : new Date();
        const fallbackEnd = dates.length ? dates[dates.length - 1] : fallbackStart;
        const startDate = this.parseDate(start) || fallbackStart;
        const endDate = this.parseDate(end) || fallbackEnd;
        if (endDate.getTime() <= startDate.getTime()) {
            return { start: this.addDays(startDate, -1), end: this.addDays(endDate, 1) };
        }
        return { start: startDate, end: endDate };
    }

    private dateX(value: string, start: Date, end: Date): number {
        const date = this.parseDate(value) || start;
        const range = Math.max(1, end.getTime() - start.getTime());
        const ratio = (date.getTime() - start.getTime()) / range;
        return Math.max(10, Math.min(90, 10 + ratio * 80));
    }

    private buildHomeData(monthRuns: RunRecord[]): HomeData {
        if (!monthRuns.length) {
            return { ...EMPTY_HOME_DATA };
        }

        const totalKm = this.round2(monthRuns.reduce((sum, run) => sum + run.distance_km, 0));
        const durationSeconds = monthRuns.reduce((sum, run) => sum + (this.durationSeconds(run) || 0), 0);
        const durationParts = this.durationParts(durationSeconds);
        const heartRates = monthRuns.map((run) => run.avg_heart_rate).filter(this.isNumber);
        const cadences = monthRuns.map((run) => run.cadence).filter(this.isNumber);
        const calories = monthRuns.reduce((sum, run) => sum + (run.calories || 0), 0);
        const paceSeconds = totalKm && durationSeconds ? durationSeconds / totalKm : null;
        const bestPaceSeconds = Math.min(...monthRuns.map((run) => this.paceSeconds(run.avg_pace)).filter(this.isNumber));

        return {
            totalKm,
            goalKm: EMPTY_HOME_DATA.goalKm,
            avgPace: this.formatPace(paceSeconds),
            avgHeartRate: heartRates.length ? Math.round(this.average(heartRates)) : '-',
            totalDurationValue: durationParts.value,
            totalDurationUnit: durationParts.unit,
            avgCadence: cadences.length ? Math.round(this.average(cadences)) : '-',
            avgKm: this.round2(totalKm / monthRuns.length),
            totalCalories: Math.round(calories),
            runCount: monthRuns.length,
            maxKm: this.round2(Math.max(...monthRuns.map((run) => run.distance_km))),
            bestPace: Number.isFinite(bestPaceSeconds) ? this.formatPace(bestPaceSeconds) : '-',
            streak: this.computeStreak(monthRuns)
        };
    }

    private buildGoalProgressCards(monthRuns: RunRecord[]): GoalProgress[] {
        if (!this.goals.length) return [];

        const distance = this.round2(monthRuns.reduce((sum, run) => sum + run.distance_km, 0));
        const durationSeconds = monthRuns.reduce((sum, run) => sum + (this.durationSeconds(run) || 0), 0);
        const stats: Record<GoalType, number | null> = {
            distance,
            count: monthRuns.length,
            duration: this.round1(durationSeconds / 60),
            pace: distance && durationSeconds ? Math.round(durationSeconds / distance) : null
        };

        return this.goals
            .filter((goal) => goal.year_month === this.activeYearMonth)
            .map((goal) => {
                const currentValue = stats[goal.goal_type];
                const targetValue = goal.target_value;
                const achieved = goal.goal_type === 'pace'
                    ? currentValue !== null && currentValue > 0 && currentValue <= targetValue
                    : (currentValue || 0) >= targetValue;
                const percent = this.goalPercent(goal.goal_type, currentValue, targetValue);
                const remainingValue = this.goalRemaining(goal.goal_type, currentValue, targetValue, achieved);
                const item: GoalProgress = {
                    id: goal.id || null,
                    year_month: goal.year_month,
                    goal_type: goal.goal_type,
                    label: this.goalTypeLabel(goal.goal_type),
                    target_value: targetValue,
                    current_value: currentValue,
                    remaining_value: remainingValue,
                    percent,
                    achieved,
                    unit: this.goalTypeUnit(goal.goal_type),
                    target_text: this.goalValueText(goal.goal_type, targetValue),
                    current_text: this.goalValueText(goal.goal_type, currentValue),
                    message: ''
                };
                item.message = this.goalProgressMessage(item);
                return item;
            })
            .sort((a, b) => this.goalTypeIndex(a.goal_type) - this.goalTypeIndex(b.goal_type));
    }

    private goalTypeIndex(goalType: GoalType): number {
        return GOAL_TYPE_OPTIONS.findIndex((option) => option.id === goalType);
    }

    private goalTypeLabel(goalType: GoalType): string {
        if (goalType === 'pace') return this.paceMetricLabel;
        return GOAL_TYPE_OPTIONS.find((option) => option.id === goalType)?.label || '목표';
    }

    private goalTypeUnit(goalType: GoalType): string {
        if (goalType === 'distance') return this.distanceUnitLabel;
        if (goalType === 'pace') return this.paceUnitLabel;
        return GOAL_TYPE_OPTIONS.find((option) => option.id === goalType)?.unit || '';
    }

    private goalPercent(goalType: GoalType, currentValue: number | null, targetValue: number): number {
        if (!targetValue) return 0;
        if (goalType === 'pace') {
            if (!currentValue) return 0;
            return Math.max(0, Math.min(100, Math.round((targetValue / currentValue) * 100)));
        }
        return Math.max(0, Math.min(100, Math.round(((currentValue || 0) / targetValue) * 100)));
    }

    private goalRemaining(goalType: GoalType, currentValue: number | null, targetValue: number, achieved: boolean): number {
        if (achieved) return 0;
        if (goalType === 'pace') {
            return currentValue ? Math.max(0, Math.round(currentValue - targetValue)) : targetValue;
        }
        return Math.max(0, this.round2(targetValue - (currentValue || 0)));
    }

    private goalValueText(goalType: GoalType, value: number | null): string {
        if (value === null || value === undefined) return '-';
        if (goalType === 'pace') return value ? `${this.formatPace(value)}${this.paceUnitLabel}` : '-';
        if (goalType === 'distance') return this.distanceText(value);
        if (goalType === 'duration') return `${Math.round(value)}분`;
        return `${Math.round(value)}회`;
    }

    private goalProgressMessage(goal: GoalProgress): string {
        if (goal.achieved) return `${goal.label} 목표를 달성했어.`;
        if (goal.goal_type === 'distance') return `이번달 거리 목표까지 ${this.distanceText(goal.remaining_value)} 남았어.`;
        if (goal.goal_type === 'count') return `이번달 횟수 목표까지 ${Math.round(goal.remaining_value)}번 남았어.`;
        if (goal.goal_type === 'duration') return `이번달 시간 목표까지 ${Math.round(goal.remaining_value)}분 남았어.`;
        if (!goal.current_value) return `${this.paceMetricLabel} 목표는 ${goal.target_text}야.`;
        if (this.appSettings.paceDisplay === 'speed') return `${this.paceMetricLabel} 목표까지 조금만 더 올리면 돼.`;
        return `평균 페이스 목표까지 ${Math.round(goal.remaining_value)}초 줄이면 돼.`;
    }

    private syncGoalDrafts(): void {
        const drafts: Record<GoalType, string> = { ...EMPTY_GOAL_DRAFTS };
        for (const option of GOAL_TYPE_OPTIONS) {
            const goal = this.goalByType(option.id);
            drafts[option.id] = goal ? this.goalInputText(option.id, goal.target_value) : '';
        }
        this.goalDrafts = drafts;
    }

    private goalInputText(goalType: GoalType, value: number): string {
        if (goalType === 'pace') return this.formatPace(value).replace('"', '');
        if (goalType === 'count') return String(Math.round(value));
        return goalType === 'distance' ? this.formatDistance(value) : String(value);
    }

    private goalTargetFromInput(goalType: GoalType, value: string): number | null {
        if (goalType === 'pace') {
            return this.paceInputSeconds(value);
        }

        const numeric = this.toNumber(value);
        if (numeric === null || numeric <= 0) return null;
        if (goalType === 'count') return Math.round(numeric);
        if (goalType === 'distance') return this.displayDistanceToKm(numeric);
        return this.round2(numeric);
    }

    private paceInputSeconds(value: string): number | null {
        const text = String(value || '').trim();
        if (!text) return null;

        if (this.appSettings.paceDisplay === 'speed') {
            const speed = this.toNumber(text);
            if (speed === null || speed <= 0) return null;
            const kmPerHour = this.appSettings.unit === 'mile' ? speed * KM_PER_MILE : speed;
            if (!Number.isFinite(kmPerHour) || kmPerHour <= 0) return null;
            return Math.round(3600 / kmPerHour);
        }

        const pace = this.paceSeconds(text);
        if (pace !== null) return this.appSettings.unit === 'mile' ? Math.round(pace / KM_PER_MILE) : pace;

        const numeric = this.toNumber(text);
        if (numeric === null || numeric <= 0) return null;
        const seconds = numeric < 30 ? numeric * 60 : numeric;
        if (seconds < 120 || seconds > 1800) return null;
        return Math.round(this.appSettings.unit === 'mile' ? seconds / KM_PER_MILE : seconds);
    }

    private storagePaceTextFromDisplay(value: string): string | null {
        const text = String(value || '').trim();
        if (!text) return null;
        const seconds = this.paceInputSeconds(text);
        if (!seconds) return text;
        return this.storagePaceText(seconds);
    }

    private buildStatCards(): StatCard[] {
        return [
            { icon: 'fa-arrow-trend-up', label: this.paceMetricLabel, value: this.homeData.avgPace, unit: this.valueUnit(this.homeData.avgPace, this.paceUnitLabel) },
            { icon: 'fa-heart-pulse', label: '평균 심박수', value: this.homeData.avgHeartRate, unit: this.valueUnit(this.homeData.avgHeartRate, 'bpm') },
            { icon: 'fa-clock', label: '총 시간', value: this.homeData.totalDurationValue, unit: this.homeData.totalDurationUnit },
            { icon: 'fa-person-running', label: '평균 케이던스', value: this.homeData.avgCadence, unit: this.valueUnit(this.homeData.avgCadence, 'spm') }
        ];
    }

    private buildSummaryCards(): StatCard[] {
        return [
            { label: '최장 거리', value: this.formatDistance(this.homeData.maxKm), unit: this.distanceUnitLabel },
            { label: this.bestPaceMetricLabel, value: this.homeData.bestPace, unit: this.valueUnit(this.homeData.bestPace, this.paceUnitLabel) },
            { label: '연속 일수', value: this.homeData.streak, unit: '일' }
        ];
    }

    private buildCalendarCells(): CalendarCell[] {
        const [year, month] = this.activeYearMonth.split('-').map(Number);
        const first = new Date(year, month - 1, 1);
        const daysInMonth = new Date(year, month, 0).getDate();
        const runsByDate = this.runs.reduce((map, run) => {
            map.set(run.date, [...(map.get(run.date) || []), run]);
            return map;
        }, new Map<string, RunRecord[]>());
        const restDates = new Set(this.restDays);
        const noteDates = new Set(this.calendarNotes.keys());
        const todayKey = this.dateKey(new Date());

        const cells: CalendarCell[] = Array.from({ length: first.getDay() }, (_, index) => ({
            key: `empty-${index}`,
            day: null,
            className: 'cal-empty',
            runCount: 0
        }));

        for (let day = 1; day <= daysInMonth; day++) {
            const date = new Date(year, month - 1, day);
            const key = this.dateKey(date);
            const isFuture = key > todayKey;
            const dayRuns = runsByDate.get(key) || [];
            const runCount = dayRuns.length;
            const hasRun = runCount > 0;
            const isRest = restDates.has(key) && !hasRun;
            const weather = this.weatherDays.get(key);
            const cycle = this.isCycleFeatureEnabled && this.isCycleOverlayEnabled ? this.cycleDayMap.get(key) : null;
            const status: CalendarStatus = hasRun ? 'run' : isRest ? 'rest' : isFuture ? 'future' : key === todayKey ? 'today' : 'no-run';
            const supportActivityType = this.primarySupportActivityType(dayRuns);
            const classList = ['cal-day'];

            if (key === todayKey) classList.push('today-marker');
            if (status === 'future') classList.push('future');
            if (status === 'rest') classList.push('rest-day');
            if (supportActivityType) classList.push(`${supportActivityType.replace('_', '-')}-day`);
            if (noteDates.has(key)) classList.push('has-note');
            if (cycle) classList.push('has-cycle', `cycle-phase-${cycle.phase}`, `cycle-source-${cycle.source}`);
            if (weather) {
                classList.push('has-weather', `weather-${weather.tone}`);
            }

            cells.push({
                key,
                day,
                className: classList.join(' '),
                dotClass: this.dotClass(status, supportActivityType),
                ariaLabel: `${this.displayDate(key, true)}${this.calendarDayRecordLabel(dayRuns, isRest)}${cycle ? `, 주기 ${cycle.label}` : ''}${weather ? `, 날씨 ${weather.summary}` : ''}${noteDates.has(key) ? ', 메모 있음' : ''}`,
                runCount,
                weatherIcon: weather?.icon,
                weatherTone: weather?.tone,
                weatherSummary: weather?.summary,
                cyclePhase: cycle?.phase,
                cyclePhaseLabel: cycle?.label,
                cycleSource: cycle?.source,
                cycleMarkerClass: cycle ? this.cycleMarkerClass(cycle.phase, cycle.source) : undefined
            });
        }

        return cells;
    }

    private buildCalendarStats(): StatCard[] {
        const [year, month] = this.activeYearMonth.split('-').map(Number);
        const daysInMonth = new Date(year, month, 0).getDate();
        const runDates = new Set(this.runs.map((run) => run.date));
        const restDates = new Set(this.restDays);
        const todayKey = this.dateKey(new Date());
        let runCount = 0;
        let restCount = 0;
        let noRunCount = 0;
        let futureCount = 0;

        for (let day = 1; day <= daysInMonth; day++) {
            const key = this.dateKey(new Date(year, month - 1, day));
            if (runDates.has(key)) {
                runCount += 1;
            } else if (restDates.has(key)) {
                restCount += 1;
            } else if (key > todayKey) {
                futureCount += 1;
            } else {
                noRunCount += 1;
            }
        }

        return [
            { label: '기록일', value: runCount, unit: '일' },
            { label: '휴식일', value: restCount, unit: '일' },
            { label: '미기록', value: noRunCount, unit: '일' },
            { label: '남은 날', value: futureCount, unit: '일' }
        ];
    }

    private buildJournalCalendarCells(): JournalCalendarCell[] {
        const [year, month] = this.activeYearMonth.split('-').map(Number);
        const first = new Date(year, month - 1, 1);
        const daysInMonth = new Date(year, month, 0).getDate();
        const todayKey = this.dateKey(new Date());
        const journalRunsByDate = this.buildJournalRuns().reduce((map, run) => {
            if (run.date.startsWith(this.activeYearMonth)) {
                map.set(run.date, [...(map.get(run.date) || []), run]);
            }
            return map;
        }, new Map<string, RunRecord[]>());

        const cells: JournalCalendarCell[] = Array.from({ length: first.getDay() }, (_, index) => ({
            key: `journal-empty-${index}`,
            day: null,
            className: 'cal-empty journal-cal-empty',
            runCount: 0,
            journalCount: 0,
            journalRuns: []
        }));

        for (let day = 1; day <= daysInMonth; day++) {
            const key = this.dateKey(new Date(year, month - 1, day));
            const journalRuns = journalRunsByDate.get(key) || [];
            const journalCount = journalRuns.length;
            const classList = ['cal-day', 'journal-cal-day'];

            if (key === todayKey) classList.push('today-marker');
            if (key > todayKey) classList.push('future');
            if (journalCount) classList.push('has-journal');

            cells.push({
                key,
                day,
                className: classList.join(' '),
                dotClass: journalCount ? 'journal-date-ring' : undefined,
                ariaLabel: `${this.displayDate(key, true)}${journalCount ? `, 일기 ${journalCount}개` : ', 일기 없음'}`,
                runCount: journalCount,
                journalCount,
                journalRuns
            });
        }

        return cells;
    }

    private syncSelectedJournalDate(): void {
        const journalRuns = this.buildJournalRuns();
        const selectedStillValid = Boolean(
            this.selectedJournalDate &&
            this.selectedJournalDate.startsWith(this.activeYearMonth) &&
            journalRuns.some((run) => run.date === this.selectedJournalDate)
        );

        if (!selectedStillValid) {
            this.selectedJournalDate = journalRuns.find((run) => run.date.startsWith(this.activeYearMonth))?.date || null;
        }

        this.selectedJournalRuns = this.buildSelectedJournalRuns();
    }

    private buildSelectedJournalRuns(): RunRecord[] {
        if (!this.selectedJournalDate) return [];

        return this.buildJournalRuns().filter((run) => run.date === this.selectedJournalDate);
    }

    private buildCycleDayMap(): Map<string, CycleDayInfo> {
        const map = new Map<string, CycleDayInfo>();
        if (!this.isCycleFeatureEnabled || !this.cycleLogs.length) return map;

        const sortedLogs = [...this.cycleLogs].sort((a, b) => a.start_date.localeCompare(b.start_date));
        const menstrualWindows = this.menstrualCycleWindows(sortedLogs);
        for (const period of menstrualWindows) {
            this.fillCycleRange(map, period.start_date, period.end_date, 'menstrual', 'manual', true);
        }

        const predictionHistory = this.cyclePredictionHistory(menstrualWindows);
        const averageCycleDays = this.cycliaAverageCycleDays(
            predictionHistory,
            Math.max(15, Math.min(60, this.cycleSummary.average_cycle_days || 28))
        );
        const averagePeriodDays = Math.max(1, Math.min(12, this.cycleSummary.average_period_days || 7));
        const predictedCycleCount = 6;
        const predictedStarts = this.predictedCycleStarts(predictionHistory, averageCycleDays, predictedCycleCount);
        const projectionWindows: CycleWindow[] = [
            ...menstrualWindows,
            ...predictedStarts.map((date) => ({ start_date: date, end_date: date }))
        ].sort((a, b) => a.start_date.localeCompare(b.start_date));

        for (let index = 0; index < projectionWindows.length; index++) {
            const start = this.parseDate(projectionWindows[index].start_date);
            if (!start) continue;

            const explicitNext = this.parseDate(projectionWindows[index + 1]?.start_date || null);
            const totalDays = explicitNext
                ? Math.max(0, Math.round((this.addDays(explicitNext, -1).getTime() - start.getTime()) / 86400000))
                : averageCycleDays - 1;

            for (let offset = 0; offset <= totalDays; offset++) {
                const date = this.addDays(start, offset);
                const key = this.dateKey(date);
                if (map.has(key)) continue;

                const phaseOffset = explicitNext ? Math.min(offset, averageCycleDays - 1) : offset % averageCycleDays;
                const windowPeriodDays = projectionWindows[index].ended_by_none
                    ? this.cycleWindowLength(projectionWindows[index], averagePeriodDays)
                    : averagePeriodDays;
                const phase = this.cyclePhaseForOffset(phaseOffset, averageCycleDays, windowPeriodDays);
                map.set(key, {
                    phase,
                    label: this.cyclePhaseLabel(phase),
                    source: 'predicted'
                });
            }
        }

        return map;
    }

    private cyclePredictionHistory(windows: CycleWindow[]): HistoryInput {
        return {
            periodStarts: windows
                .map((window) => this.normalizeDateKey(window.start_date))
                .filter((date): date is string => Boolean(date))
                .map((date) => ({ date }))
        };
    }

    private cycliaAverageCycleDays(history: HistoryInput, fallback: number): number {
        try {
            const averageCycle = this.cyclePredictionEngine.analyze(history).averageCycle;
            if (averageCycle && Number.isFinite(averageCycle)) {
                return Math.max(15, Math.min(60, Math.round(averageCycle)));
            }
        } catch {
            return fallback;
        }
        return fallback;
    }

    private predictedCycleStarts(history: HistoryInput, averageCycleDays: number, count: number): string[] {
        let periodStarts = [...history.periodStarts].sort((a, b) => a.date.localeCompare(b.date));
        const predictions: string[] = [];
        if (!periodStarts.length) return predictions;

        for (let index = 0; index < count; index++) {
            const lastStart = periodStarts[periodStarts.length - 1]?.date;
            if (!lastStart) break;

            let nextStart = this.cycliaNextPeriod({ periodStarts });
            if (!nextStart || nextStart <= lastStart) {
                const lastDate = this.parseDate(lastStart);
                if (!lastDate) break;
                nextStart = this.dateKey(this.addDays(lastDate, averageCycleDays));
            }
            if (!nextStart || predictions.includes(nextStart) || periodStarts.some((item) => item.date === nextStart)) break;

            predictions.push(nextStart);
            periodStarts = [...periodStarts, { date: nextStart }];
        }

        return predictions;
    }

    private cycliaNextPeriod(history: HistoryInput): string | null {
        try {
            return this.normalizeDateKey(this.cyclePredictionEngine.predictNextPeriod(history).likely);
        } catch {
            return null;
        }
    }

    private menstrualCycleWindows(logs: CycleLog[]): CycleWindow[] {
        const ranges = logs
            .filter((log) => log.cycle_phase === 'menstrual')
            .map((log) => ({
                start_date: log.start_date <= log.end_date ? log.start_date : log.end_date,
                end_date: log.end_date >= log.start_date ? log.end_date : log.start_date,
                is_none: log.flow_level === 'none'
            }))
            .sort((a, b) => {
                const dateOrder = a.start_date.localeCompare(b.start_date);
                if (dateOrder) return dateOrder;
                return Number(a.is_none) - Number(b.is_none);
            });
        const windows: CycleWindow[] = [];

        for (const range of ranges) {
            if (range.is_none) {
                const current = windows[windows.length - 1];
                const noneStart = this.parseDate(range.start_date);
                if (!current || !noneStart) continue;

                const cutoff = this.dateKey(this.addDays(noneStart, -1));
                if (cutoff < current.start_date) {
                    windows.pop();
                } else if (cutoff < current.end_date) {
                    current.end_date = cutoff;
                    current.ended_by_none = true;
                } else if (cutoff === current.end_date) {
                    current.ended_by_none = true;
                }
                continue;
            }

            const current = windows[windows.length - 1];
            if (!current) {
                windows.push({ start_date: range.start_date, end_date: range.end_date });
                continue;
            }

            const currentEnd = this.parseDate(current.end_date);
            const rangeStart = this.parseDate(range.start_date);
            if (!currentEnd || !rangeStart || rangeStart.getTime() > this.addDays(currentEnd, 1).getTime()) {
                windows.push({ start_date: range.start_date, end_date: range.end_date });
                continue;
            }

            if (range.end_date > current.end_date) {
                current.end_date = range.end_date;
            }
        }

        return windows;
    }

    private cycleWindowLength(window: CycleWindow, fallback: number): number {
        const start = this.parseDate(window.start_date);
        const end = this.parseDate(window.end_date);
        if (!start || !end) return fallback;
        return Math.max(1, Math.min(12, Math.round((end.getTime() - start.getTime()) / 86400000) + 1));
    }

    private fillCycleRange(map: Map<string, CycleDayInfo>, startDate: string, endDate: string, phase: CyclePhase, source: CycleSource, overwrite: boolean): void {
        const start = this.parseDate(startDate);
        const end = this.parseDate(endDate);
        if (!start || !end) return;

        const days = Math.min(90, Math.max(0, Math.round((end.getTime() - start.getTime()) / 86400000)));
        for (let offset = 0; offset <= days; offset++) {
            const key = this.dateKey(this.addDays(start, offset));
            if (!overwrite && map.has(key)) continue;
            map.set(key, {
                phase,
                label: this.cyclePhaseLabel(phase),
                source
            });
        }
    }

    private cyclePhaseForOffset(offset: number, averageCycleDays: number, averagePeriodDays: number): CyclePhase {
        if (offset < averagePeriodDays) return 'menstrual';

        const ovulationDay = Math.max(averagePeriodDays, averageCycleDays - 14);
        if (offset === ovulationDay) return 'ovulation';
        if (offset < ovulationDay) return 'follicular';
        return 'luteal';
    }

    private buildSelectedCalendarRuns(): CalendarRunDetail[] {
        if (!this.selectedCalendarDate) return [];

        const dayRuns = this.runs.filter((run) => run.date === this.selectedCalendarDate);

        return dayRuns.map((run, index) => {
            const isSupportActivity = SUPPORT_ACTIVITY_TYPES.has(this.normalizeRunType(run.run_type));
            return {
                id: run.id || `${run.date}-${index}`,
                date: run.date,
                title: isSupportActivity
                    ? `${this.runTypeLabel(run.run_type)} 기록`
                    : dayRuns.length > 1 ? `러닝 기록 ${index + 1}` : '러닝 기록',
                badge: isSupportActivity ? '운동 기록' : '저장됨',
                runType: run.run_type,
                stats: this.buildRunStatCards(run),
                media: run.media || [],
                waterBeforeMl: run.water_before_ml || null,
                waterAfterMl: run.water_after_ml || null,
                journal: run.journal || null,
                playlistName: run.playlist_name || null,
                musicUrl: run.music_url || null,
                topTracks: run.top_tracks || [],
                is_public: run.is_public !== false
            };
        });
    }

    private buildRunStatCards(run: RunRecord): StatCard[] {
        if (run.journal_only) {
            return [
                { label: '종류', value: '일기', unit: '' },
                { label: '날짜', value: this.displayDate(run.date, true), unit: '' }
            ];
        }
        if (SUPPORT_ACTIVITY_TYPES.has(this.normalizeRunType(run.run_type))) {
            return [
                { label: '운동', value: this.runTypeLabel(run.run_type), unit: '' },
                { label: '날짜', value: this.displayDate(run.date, true), unit: '' },
                { label: '상태', value: '기록됨', unit: '' }
            ];
        }

        return [
            { label: '거리', value: this.distanceText(run.distance_km), unit: '' },
            { label: this.paceMetricLabel, value: this.paceText(run.avg_pace), unit: '' },
            { label: '시간', value: this.shortDuration(run), unit: '' },
            { label: '칼로리', value: run.calories ?? '-', unit: '' },
            { label: '심박수', value: run.avg_heart_rate ?? '-', unit: '' },
            { label: '케이던스', value: run.cadence ?? '-', unit: '' }
        ];
    }

    private buildChartCards(): ChartCard[] {
        const series = this.buildChartPeriodSeries();
        const distances = series.groups.map((group) => this.round2(group.reduce((sum, run) => sum + run.distance_km, 0)));
        const paceValues = series.groups.map((group) => {
            const distance = group.reduce((sum, run) => sum + run.distance_km, 0);
            const duration = group.reduce((sum, run) => sum + (this.durationSeconds(run) || 0), 0);
            return distance && duration ? duration / distance : null;
        });
        const periodRuns = this.chartPeriodRuns();
        const comparisonRuns = this.chartPeriodComparisonRuns();
        const currentDistance = this.round2(periodRuns.reduce((sum, run) => sum + run.distance_km, 0));
        const previousDistance = this.round2(comparisonRuns.reduce((sum, run) => sum + run.distance_km, 0));
        const currentPace = this.averagePaceForRuns(periodRuns);
        const previousPace = this.averagePaceForRuns(comparisonRuns);

        return [
            {
                title: `${series.title} 거리 (${this.distanceUnitLabel})`,
                bars: this.scaleBars(distances, series.labels),
                footerLeft: currentDistance ? `${series.currentLabel} ${this.distanceText(currentDistance)}` : `${series.currentLabel} 기록 없음`,
                footerRight: this.distanceChangeText(currentDistance, previousDistance, series.previousLabel)
            },
            {
                title: `${this.paceMetricLabel} 추이`,
                bars: this.scalePaceBars(paceValues, series.labels),
                footerLeft: currentPace ? `${series.currentLabel} 평균 ${this.formatPace(currentPace)}${this.paceUnitLabel}` : `${series.currentLabel} ${this.paceDisplaySettingsText} 기록 없음`,
                footerRight: this.paceChangeText(currentPace, previousPace)
            }
        ];
    }

    private buildMiniStats(): StatCard[] {
        const runs = this.chartPeriodRuns();
        const labelPrefix = this.activeChartPeriod === 'monthly'
            ? '이번달'
            : this.activeChartPeriod === 'last_week'
                ? '저번주'
                : '이번주';
        const heartRates = runs.map((run) => run.avg_heart_rate).filter(this.isNumber);
        const cadences = runs.map((run) => run.cadence).filter(this.isNumber);

        return [
            this.metricCard(`${labelPrefix} 평균 심박`, heartRates.length ? Math.round(this.average(heartRates)) : '-', 'bpm'),
            this.metricCard(`${labelPrefix} 평균 케이던스`, cadences.length ? Math.round(this.average(cadences)) : '-', 'spm'),
            this.metricCard('최저 심박 기록', heartRates.length ? Math.min(...heartRates) : '-', 'bpm'),
            this.metricCard('최고 케이던스', cadences.length ? Math.max(...cadences) : '-', 'spm')
        ];
    }

    private buildRunTypeStats(runs: RunRecord[]): RunTypeSummary[] {
        const totalCount = runs.length;
        const totalDistance = runs.reduce((sum, run) => sum + run.distance_km, 0);

        return RUN_TYPE_OPTIONS.map((option) => {
            const group = runs.filter((run) => run.run_type === option.id);
            const distanceKm = this.round2(group.reduce((sum, run) => sum + run.distance_km, 0));
            const duration = group.reduce((sum, run) => sum + (this.durationSeconds(run) || 0), 0);
            const paceSeconds = distanceKm && duration ? duration / distanceKm : null;
            return {
                id: option.id,
                label: option.label,
                count: group.length,
                distanceKm,
                distanceText: this.distanceText(distanceKm),
                averagePace: this.formatPace(paceSeconds),
                paceSeconds,
                countPercent: totalCount ? Math.round((group.length / totalCount) * 100) : 0,
                distancePercent: totalDistance ? Math.max(3, Math.round((distanceKm / totalDistance) * 100)) : 0
            };
        });
    }

    private buildHydrationPattern(): HydrationPattern {
        const runs = this.chartPeriodRuns();
        if (!runs.length) {
            return { ...EMPTY_HYDRATION_PATTERN };
        }

        const loggedRuns = runs.filter((run) => this.waterTotalMl(run) > 0);
        const totalMl = loggedRuns.reduce((sum, run) => sum + this.waterTotalMl(run), 0);
        const totalDistance = loggedRuns.reduce((sum, run) => sum + run.distance_km, 0);
        const longRuns = runs.filter((run) => run.distance_km >= 8);
        const lowLongRuns = longRuns.filter((run) => this.waterTotalMl(run) < this.hydrationTargetMl(run.distance_km));
        const averageMlPerRun = loggedRuns.length ? Math.round(totalMl / loggedRuns.length) : 0;
        const mlPerKm = totalDistance ? Math.round(totalMl / totalDistance) : 0;
        const coverageText = `${loggedRuns.length}/${runs.length}회 기록`;
        let guidance = '수분 기록을 더 남기면 거리별 패턴이 또렷해져.';

        if (!loggedRuns.length) {
            guidance = '러닝 전후 물 섭취량을 저장하면 장거리 때 충분히 마셨는지 볼 수 있어.';
        } else if (lowLongRuns.length) {
            guidance = `${this.distanceText(8)} 이상 ${longRuns.length}회 중 ${lowLongRuns.length}회는 수분이 적거나 미기록이야. 긴 러닝 전후로 나눠 마시는 패턴을 남겨보자.`;
        } else if (longRuns.length) {
            guidance = '긴 러닝 수분 기록은 안정적인 편이야. 더운 날에는 전후 기록을 계속 남겨두자.';
        }

        return {
            runCount: runs.length,
            loggedRunCount: loggedRuns.length,
            averageMlPerRun,
            mlPerKm,
            longRunCount: longRuns.length,
            lowLongRunCount: lowLongRuns.length,
            coverageText,
            guidance
        };
    }

    private buildCyclePatternStats(): CyclePatternStat[] {
        if (!this.isCycleFeatureEnabled || !this.cycleLogs.length) {
            return [];
        }

        return CYCLE_PHASE_OPTIONS.map((option) => {
            const group = this.runs.filter((run) => this.cycleDayMap.get(run.date)?.phase === option.id);
            const totalDistance = this.round2(group.reduce((sum, run) => sum + run.distance_km, 0));
            const totalDuration = group.reduce((sum, run) => sum + (this.durationSeconds(run) || 0), 0);
            const avgPaceSeconds = totalDistance && totalDuration ? totalDuration / totalDistance : null;
            const avgDistance = group.length ? this.round2(totalDistance / group.length) : 0;
            const conditionItems = this.conditionDistributionForPhase(option.id);

            return {
                phase: option.id,
                label: option.label,
                runCount: group.length,
                avgPace: this.formatPace(avgPaceSeconds),
                avgDistanceText: this.distanceText(avgDistance),
                conditionItems
            };
        });
    }

    private conditionDistributionForPhase(phase: CyclePhase): ConditionDistributionItem[] {
        const counts = new Map<string, number>();
        for (const log of this.cycleLogs) {
            if (log.cycle_phase !== phase) continue;
            if (log.flow_level === 'none') continue;
            const emoji = this.normalizeCycleConditionEmoji(log.condition_emoji);
            if (!emoji) continue;
            counts.set(emoji, (counts.get(emoji) || 0) + 1);
        }

        const total = Array.from(counts.values()).reduce((sum, count) => sum + count, 0) || 1;
        return CYCLE_CONDITION_OPTIONS
            .map((item) => ({
                emoji: item.emoji,
                count: counts.get(item.emoji) || 0,
                percent: Math.round(((counts.get(item.emoji) || 0) / total) * 100)
            }))
            .filter((item) => item.count > 0);
    }

    private normalizeCycleConditionEmoji(value: unknown): string {
        const text = typeof value === 'string' ? value.trim() : '';
        return CYCLE_CONDITION_OPTIONS.some((item) => item.emoji === text) ? text : '';
    }

    private normalizeCycleFlowLevel(value: unknown): CycleFlowLevel | '' {
        const text = typeof value === 'string' ? value.trim().toLowerCase() : '';
        if (text === 'none' || text === 'no' || text === '없음' || text === '안함' || text === '안 함') return 'none';
        if (text === 'light' || text === 'normal' || text === 'heavy') return text;
        return '';
    }

    public cycleFlowLabel(level?: CycleFlowLevel | '' | null): string {
        return CYCLE_FLOW_OPTIONS.find((item) => item.id === level)?.label || '';
    }

    public cycleLegendMarkerClass(phase: CyclePhase): string {
        return `${this.cycleMarkerClass(phase, 'predicted')} cycle-legend-icon`;
    }

    private cycleMarkerClass(phase: CyclePhase, source: CycleSource): string {
        const iconClass = phase === 'menstrual' && source === 'predicted'
            ? 'fa-regular fa-heart'
            : phase === 'menstrual'
                ? 'fa-solid fa-heart'
            : phase === 'ovulation'
                ? 'fa-solid fa-star'
            : phase === 'luteal'
                ? 'fa-solid fa-moon'
                    : 'fa-solid fa-seedling';
        return `cycle-day-marker cycle-marker-${phase} ${iconClass}`;
    }

    private buildChartPeriodSeries(): ChartPeriodSeries {
        if (this.activeChartPeriod === 'monthly') {
            return this.buildMonthlyChartSeries();
        }

        return this.buildWeekChartSeries(this.activeChartPeriod === 'last_week' ? -1 : 0);
    }

    private buildWeekChartSeries(offsetWeeks: number): ChartPeriodSeries {
        const range = this.chartWeekRange(offsetWeeks);
        const days = Array.from({ length: 7 }, (_, index) => this.addDays(range.start, index));
        const title = offsetWeeks === -1 ? '저번주' : '이번주';

        return {
            title,
            labels: days.map((date) => `${date.getMonth() + 1}/${date.getDate()}`),
            groups: days.map((day) => this.runsInRange(day, this.addDays(day, 1))),
            currentLabel: title,
            previousLabel: offsetWeeks === -1 ? '전주' : '저번주'
        };
    }

    private buildMonthlyChartSeries(): ChartPeriodSeries {
        const latestDate = this.parseDate(this.runs[0]?.date) || new Date();
        const starts = Array.from({ length: 6 }, (_, index) => (
            new Date(latestDate.getFullYear(), latestDate.getMonth() - (5 - index), 1)
        ));
        const monthKeys = starts.map((date) => this.yearMonthKey(date));

        return {
            title: '월간',
            labels: starts.map((date) => `${date.getMonth() + 1}월`),
            groups: monthKeys.map((key) => this.runs.filter((run) => run.date.startsWith(key))),
            currentLabel: '이번달',
            previousLabel: '지난달'
        };
    }

    private chartPeriodRuns(): RunRecord[] {
        if (this.activeChartPeriod === 'monthly') {
            const latestMonth = this.runs[0]?.date.slice(0, 7) || this.activeYearMonth;
            return this.runs.filter((run) => run.date.startsWith(latestMonth));
        }

        const range = this.chartWeekRange(this.activeChartPeriod === 'last_week' ? -1 : 0);
        return this.runsInRange(range.start, range.end);
    }

    private chartPeriodComparisonRuns(): RunRecord[] {
        if (this.activeChartPeriod === 'monthly') {
            const latestDate = this.parseDate(this.runs[0]?.date) || this.parseDate(`${this.activeYearMonth}-01`) || new Date();
            const previousMonth = new Date(latestDate.getFullYear(), latestDate.getMonth() - 1, 1);
            const previousMonthKey = this.yearMonthKey(previousMonth);
            return this.runs.filter((run) => run.date.startsWith(previousMonthKey));
        }

        const range = this.chartWeekRange(this.activeChartPeriod === 'last_week' ? -2 : -1);
        return this.runsInRange(range.start, range.end);
    }

    private chartWeekRange(offsetWeeks: number): { start: Date; end: Date } {
        const referenceDate = this.parseDate(this.runs[0]?.date) || this.parseDate(this.todayDateKey) || new Date();
        const start = this.addDays(this.weekStart(referenceDate), offsetWeeks * 7);
        return {
            start,
            end: this.addDays(start, 7)
        };
    }

    private runsInRange(start: Date, end: Date): RunRecord[] {
        return this.runs.filter((run) => {
            const date = this.parseDate(run.date);
            return Boolean(date && date >= start && date < end);
        });
    }

    private averagePaceForRuns(runs: RunRecord[]): number | null {
        const distance = runs.reduce((sum, run) => sum + run.distance_km, 0);
        const duration = runs.reduce((sum, run) => sum + (this.durationSeconds(run) || 0), 0);
        return distance && duration ? duration / distance : null;
    }

    private buildGalleryItems(): GalleryItem[] {
        if (this.galleryTab === 'journal') {
            return this.buildJournalRuns()
                .map((run) => {
                    const km = run.journal_only ? '일기만 저장' : this.distanceText(run.distance_km, true);
                    const date = this.displayDate(run.date, false);
                    return {
                        id: run.id || `${run.date}-journal`,
                        km,
                        date,
                        stats: [
                            { label: run.journal_only ? '종류' : '거리', value: km },
                            { label: run.journal_only ? '날짜' : this.paceDisplaySettingsText, value: run.journal_only ? this.displayDate(run.date, true) : this.paceText(run.avg_pace) },
                            { label: '시간', value: run.journal_only ? '-' : this.shortDuration(run) }
                        ],
                        runType: run.run_type,
                        altText: run.journal_only ? `${date} 일기 보기` : `${date} ${km} 러닝 일기 보기`,
                        run,
                        journal: run.journal || ''
                    };
                })
                .slice(0, 60);
        }

        if (this.galleryTab === 'media') {
            return this.runs
                .flatMap((run) => (run.media || []).map((media) => {
                    const km = this.distanceText(run.distance_km, true);
                    const date = this.displayDate(run.date, false);
                    return {
                        id: media.id,
                        km,
                        date,
                        stats: [
                            { label: '종류', value: this.mediaTypeLabel(media.media_type) },
                            { label: '기록', value: km },
                            { label: '날짜', value: date }
                        ],
                        runType: run.run_type,
                        altText: `${date} ${km} 러닝 첨부 ${this.mediaTypeLabel(media.media_type)}`,
                        imageUrl: media.media_url,
                        media,
                        mediaType: media.media_type
                    };
                }))
                .slice(0, 60);
        }

        return this.runs
            .filter((run) => Boolean(run.image_url))
            .slice(0, 8)
            .map((run) => {
                const km = this.distanceText(run.distance_km, true);
                const date = this.displayDate(run.date, false);
                return {
                    id: run.id || `${run.date}-${run.image_url}`,
                    km,
                    date,
                    stats: [
                        { label: this.paceDisplaySettingsText, value: this.paceText(run.avg_pace) },
                        { label: '시간', value: this.shortDuration(run) },
                        { label: '칼로리', value: run.calories ?? '-' }
                    ],
                    runType: run.run_type,
                    altText: `${date} ${km} 러닝 기록 캡처`,
                    imageUrl: run.image_url
                };
            });
    }

    private buildChatMessages(): ChatMessage[] {
        const pendingGoal = this.goalProgressCards.find((goal) => !goal.achieved);
        const rankingMessage = this.rankingMotivationDisplayText && this.rankingEntries.length > 1
            ? this.rankingMotivationDisplayText
            : '';
        if (pendingGoal && rankingMessage) {
            return [
                { sender: 'ai', text: pendingGoal.message },
                { sender: 'ai', text: rankingMessage }
            ];
        }
        if (pendingGoal) {
            return [
                { sender: 'ai', text: pendingGoal.message }
            ];
        }

        if (rankingMessage) {
            return [
                { sender: 'ai', text: rankingMessage }
            ];
        }

        if (!this.runs.length) {
            return [
                { sender: 'ai', text: '기록을 올리면 너의 러닝에 대해 얘기해줄 수 있어.' }
            ];
        }

        if (this.isCycleFeatureEnabled && this.cycleSummary.current_phase_label) {
            return [
                {
                    sender: 'ai',
                    text: `입력한 기록 기준 현재 주기 단계는 ${this.cycleSummary.current_phase_label}야. 오늘 강도는 컨디션을 우선해서 조절해볼게.`
                }
            ];
        }

        const latest = this.runs[0];
        return [
            {
                sender: 'ai',
                text: `최근 기록은 ${this.displayDate(latest.date, false)} ${this.distanceText(latest.distance_km)}, ${this.paceDisplaySettingsText} ${this.paceText(latest.avg_pace)}야.`
            }
        ];
    }

    private scaleBars(values: number[], labels: string[]): ChartBar[] {
        if (!values.some((value) => value > 0)) return [];

        const max = Math.max(...values);
        const highlightIndex = this.lastIndex(values, (value) => value > 0);
        return values.map((value, index) => ({
            label: labels[index],
            height: value > 0 ? Math.max(14, Math.round((value / max) * 92)) : 4,
            highlight: index === highlightIndex,
            valueText: this.compactDistanceValue(value)
        }));
    }

    private scalePaceBars(values: Array<number | null>, labels: string[]): ChartBar[] {
        const valid = values.filter(this.isNumber);
        if (!valid.length) return [];

        const fastest = Math.min(...valid);
        const slowest = Math.max(...valid);
        const range = slowest - fastest;
        const highlightIndex = this.lastIndex(values, (value) => value !== null);

        return values.map((value, index) => {
            let height = 4;
            if (value !== null) {
                height = range ? 35 + Math.round(((slowest - value) / range) * 57) : 68;
            }

            return {
                label: labels[index],
                height,
                highlight: index === highlightIndex,
                valueText: value !== null ? this.compactPaceValue(value) : '-'
            };
        });
    }

    private compactDistanceValue(value: number): string {
        if (!Number.isFinite(value) || value <= 0) return '0';

        const converted = this.appSettings.unit === 'mile' ? value / KM_PER_MILE : value;
        const rounded = this.round1(converted);
        return Number.isInteger(rounded) ? String(rounded) : rounded.toFixed(1);
    }

    private compactPaceValue(seconds: number): string {
        return this.formatPace(seconds).replace(/"$/, '');
    }

    private distanceChangeText(current: number, previous: number, previousLabel: string = '지난주'): string {
        if (!current || !previous) return '비교 기록 없음';

        const diff = this.round2(current - previous);
        if (diff >= 0) return `▲ ${previousLabel}보다 ${this.distanceText(diff)}↑`;
        return `▼ ${previousLabel}보다 ${this.distanceText(Math.abs(diff))}↓`;
    }

    private paceChangeText(current: number | null, previous: number | null): string {
        if (!current || !previous) return '비교 기록 없음';

        if (this.appSettings.paceDisplay === 'speed') {
            const currentSpeed = this.speedForPaceSeconds(current);
            const previousSpeed = this.speedForPaceSeconds(previous);
            const diff = currentSpeed - previousSpeed;
            if (!Number.isFinite(diff) || Math.abs(diff) < 0.05) return '변화 없음';
            const unit = this.paceUnitLabel;
            if (diff >= 0) return `▲ ${diff.toFixed(1)}${unit} 빠름`;
            return `▼ ${Math.abs(diff).toFixed(1)}${unit} 느림`;
        }

        const diff = Math.round(previous - current);
        if (diff >= 0) return `▲ ${diff}초 빠름`;
        return `▼ ${Math.abs(diff)}초 느림`;
    }

    private speedForPaceSeconds(seconds: number): number {
        if (!Number.isFinite(seconds) || seconds <= 0) return 0;
        const kmPerHour = 3600 / seconds;
        return this.appSettings.unit === 'mile' ? kmPerHour / KM_PER_MILE : kmPerHour;
    }

    private computeStreak(monthRuns: RunRecord[]): number {
        const dates = new Set(monthRuns.map((run) => run.date));
        const latest = this.parseDate(monthRuns[0]?.date);
        if (!latest) return 0;

        let cursor = latest;
        let count = 0;
        while (dates.has(this.dateKey(cursor))) {
            count += 1;
            cursor = this.addDays(cursor, -1);
        }

        return count;
    }

    private dotClass(status: CalendarStatus, supportActivityType: RunType | null = null): string | undefined {
        if (status === 'future') return undefined;
        if (supportActivityType === 'strength') return 'dot dot-strength';
        if (supportActivityType === 'home_training') return 'dot dot-home-training';
        if (status === 'run') return 'dot dot-green';
        if (status === 'rest') return 'dot dot-gray';
        return undefined;
    }

    private primarySupportActivityType(runs: RunRecord[]): RunType | null {
        const activity = runs.find((run) => SUPPORT_ACTIVITY_TYPES.has(this.normalizeRunType(run.run_type)));
        return activity ? this.normalizeRunType(activity.run_type) : null;
    }

    private calendarDayRecordLabel(runs: RunRecord[], isRest: boolean): string {
        if (!runs.length) return isRest ? ', 휴식일' : ', 러닝 기록 없음';

        const supportRuns = runs.filter((run) => SUPPORT_ACTIVITY_TYPES.has(this.normalizeRunType(run.run_type)));
        if (supportRuns.length === runs.length && supportRuns.length === 1) {
            return `, ${this.runTypeLabel(supportRuns[0].run_type)} 기록`;
        }
        if (supportRuns.length === runs.length) {
            return `, 운동 기록 ${supportRuns.length}개`;
        }
        return `, 러닝 기록 ${runs.length}개`;
    }

    private durationSeconds(run: RunRecord): number | null {
        const parsed = this.parseDuration(run.duration);
        if (parsed !== null) return parsed;

        const pace = this.paceSeconds(run.avg_pace);
        if (pace === null) return null;
        return pace * run.distance_km;
    }

    private parseDuration(value?: string | null): number | null {
        if (!value) return null;

        const parts = value.split(':').map((part) => Number(part));
        if (parts.length === 3 && parts.every(Number.isFinite)) {
            return parts[0] * 3600 + parts[1] * 60 + parts[2];
        }
        if (parts.length === 2 && parts.every(Number.isFinite)) {
            return parts[0] * 60 + parts[1];
        }
        return null;
    }

    private paceSeconds(value?: string | null): number | null {
        if (!value) return null;

        const match = value.match(/(\d{1,2})\s*[':]\s*(\d{1,2})/);
        if (!match) return null;
        return Number(match[1]) * 60 + Number(match[2]);
    }

    public shortDuration(run: RunRecord): string {
        const seconds = this.durationSeconds(run);
        if (seconds === null) return '-';

        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const remain = Math.round(seconds % 60);
        if (hours) return `${hours}:${String(minutes).padStart(2, '0')}:${String(remain).padStart(2, '0')}`;
        return `${minutes}'${String(remain).padStart(2, '0')}"`;
    }

    private durationParts(seconds: number): { value: string; unit: string } {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.round((seconds % 3600) / 60);
        return {
            value: `${hours}h`,
            unit: `${minutes}m`
        };
    }

    private formatPace(seconds: number | null): string {
        if (seconds === null || !Number.isFinite(seconds)) return '-';

        if (this.appSettings.paceDisplay === 'speed') {
            const unitDistance = this.appSettings.unit === 'mile' ? 1 / KM_PER_MILE : 1;
            const speed = unitDistance * 3600 / seconds;
            return Number.isFinite(speed) ? speed.toFixed(1) : '-';
        }

        const unitSeconds = this.appSettings.unit === 'mile' ? seconds * KM_PER_MILE : seconds;
        const rounded = Math.round(unitSeconds);
        const minutes = Math.floor(rounded / 60);
        const remain = rounded % 60;
        return `${minutes}'${String(remain).padStart(2, '0')}"`;
    }

    private storagePaceText(seconds: number | null): string | null {
        if (seconds === null || !Number.isFinite(seconds)) return null;
        const rounded = Math.round(seconds);
        const minutes = Math.floor(rounded / 60);
        const remain = rounded % 60;
        return `${minutes}:${String(remain).padStart(2, '0')}`;
    }

    public displayPace(value?: string | number | null): string {
        const seconds = typeof value === 'number' ? value : this.paceSeconds(value);
        return this.formatPace(seconds);
    }

    public paceText(value?: string | number | null): string {
        const pace = this.displayPace(value);
        return pace === '-' ? '-' : `${pace}${this.paceUnitLabel}`;
    }

    public displayDate(value: string, withWeekday: boolean): string {
        const date = this.parseDate(value);
        if (!date) return '-';

        const text = `${date.getMonth() + 1}월 ${date.getDate()}일`;
        if (!withWeekday) return text;

        const weekdays = ['일', '월', '화', '수', '목', '금', '토'];
        return `${text} (${weekdays[date.getDay()]})`;
    }

    public formatBadgeDate(value?: string | null): string {
        if (!value) return '미획득';

        const date = this.parseDate(value.slice(0, 10));
        if (!date) return '미획득';

        return `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, '0')}.${String(date.getDate()).padStart(2, '0')}`;
    }

    public formatChatSessionTime(value: string): string {
        const date = this.parseDateTime(value);
        if (!date) return '';

        return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
    }

    public formatDistance(value: number): string {
        const km = Number(value);
        if (!Number.isFinite(km)) return '0.00';
        const converted = this.appSettings.unit === 'mile' ? km / KM_PER_MILE : km;
        return converted.toFixed(2);
    }

    public distanceText(value: number, spaced: boolean = false): string {
        return `${this.formatDistance(value)}${spaced ? ' ' : ''}${this.distanceUnitLabel}`;
    }

    private displayDistanceToKm(value: number): number {
        const numeric = Number(value);
        if (!Number.isFinite(numeric)) return 0;
        return this.round2(this.appSettings.unit === 'mile' ? numeric * KM_PER_MILE : numeric);
    }

    private round2(value: number): number {
        return Math.round(value * 100) / 100;
    }

    private round1(value: number): number {
        return Math.round(value * 10) / 10;
    }

    private average(values: number[]): number {
        return values.reduce((sum, value) => sum + value, 0) / values.length;
    }

    private metricCard(label: string, value: string | number, unit: string): StatCard {
        return { label, value, unit: this.valueUnit(value, unit) };
    }

    private valueUnit(value: string | number, unit: string): string {
        return value === '-' ? '' : unit;
    }

    private lastIndex<T>(values: T[], predicate: (value: T) => boolean): number {
        for (let index = values.length - 1; index >= 0; index--) {
            if (predicate(values[index])) return index;
        }
        return 0;
    }

    private isNumber(value: unknown): value is number {
        return typeof value === 'number' && Number.isFinite(value);
    }

    private hydrationUploadPayload(): Partial<RunRecord> {
        const before = this.waterAmountFromInput(this.waterBeforeInput);
        const after = this.waterAmountFromInput(this.waterAfterInput);
        const payload: Partial<RunRecord> = {};
        if (before !== null) payload.water_before_ml = before;
        if (after !== null) payload.water_after_ml = after;
        return payload;
    }

    private musicUploadPayload(includeJournal: boolean = true): Partial<RunRecord> {
        const payload: Partial<RunRecord> = {};
        const playlistName = String(this.playlistNameInput || '').trim();
        const uploadJournal = String(this.uploadJournalText || '').trim();
        const selectedTracks = this.selectedMusicTracks.map((track) => ({
            id: track.id,
            title: track.title,
            artist: track.artist,
            album: track.album || '',
            album_art_url: track.album_art_url || '',
            url: track.url || ''
        }));
        const musicUrl = String(this.musicUrlInput || '').trim() || selectedTracks.find((track) => track.url)?.url || '';

        if (playlistName) payload.playlist_name = playlistName;
        if (musicUrl) payload.music_url = musicUrl;
        if (selectedTracks.length) payload.top_tracks = selectedTracks;
        if (includeJournal && uploadJournal) payload.journal = uploadJournal;
        return payload;
    }

    private resetHydrationInputs(): void {
        this.waterBeforeInput = '';
        this.waterAfterInput = '';
    }

    private resetMusicInputs(): void {
        this.selectedMusicTrackIds = [];
        this.playlistNameInput = '';
        this.musicUrlInput = '';
        this.uploadJournalText = '';
    }

    private waterAmountFromInput(value: string): number | null {
        return this.normalizeWaterMl(value);
    }

    private normalizeWaterMl(value: unknown): number | null {
        const amount = this.toNumber(value);
        if (amount === null) return null;

        const rounded = Math.round(amount);
        if (rounded <= 0 || rounded > 20000) return null;
        return rounded;
    }

    private waterTotalMl(run: RunRecord): number {
        return (this.normalizeWaterMl(run.water_before_ml) || 0) + (this.normalizeWaterMl(run.water_after_ml) || 0);
    }

    private hydrationTargetMl(distanceKm: number): number {
        if (!Number.isFinite(distanceKm) || distanceKm < 8) return 0;
        return Math.max(500, Math.round(distanceKm * 80));
    }

    private hasJournal(run: RunRecord): boolean {
        return Boolean(run.journal && run.journal.trim());
    }

    private buildJournalRuns(): RunRecord[] {
        const entries: RunRecord[] = this.runs
            .filter((run) => this.hasJournal(run))
            .map((run) => ({ ...run, journal_only: false }));
        const datesWithRunJournal = new Set(entries.map((run) => run.date));
        const runsByDate = this.runs.reduce((map, run) => {
            if (!map.has(run.date)) map.set(run.date, run);
            return map;
        }, new Map<string, RunRecord>());

        for (const note of this.calendarNotes.values()) {
            const memo = (note.memo || '').trim();
            if (!memo || datesWithRunJournal.has(note.date)) continue;

            const matchingRun = runsByDate.get(note.date);
            if (matchingRun) {
                entries.push({
                    ...matchingRun,
                    journal: memo,
                    journal_only: false
                });
                continue;
            }

            entries.push({
                id: `day-note:${note.date}`,
                date: note.date,
                distance_km: 0,
                avg_pace: null,
                duration: null,
                run_type: 'jogging',
                journal: memo,
                media: [],
                journal_only: true,
                created_at: note.updated_at || null
            });
        }

        return entries.sort((a, b) => {
            const dateCompare = b.date.localeCompare(a.date);
            if (dateCompare) return dateCompare;
            return String(b.created_at || '').localeCompare(String(a.created_at || ''));
        });
    }

    private toNumber(value: unknown): number | null {
        if (value === null || value === undefined || value === '') return null;
        if (typeof value === 'string') {
            const match = value.replace(/\s/g, '').match(/-?\d+(?:[,.]\d+)*/);
            if (!match) return null;

            let numericText = match[0];
            if (numericText.includes(',') && numericText.includes('.')) {
                numericText = numericText.replace(/,/g, '');
            } else if (numericText.includes(',')) {
                const parts = numericText.split(',');
                numericText = parts[parts.length - 1].length <= 2
                    ? `${parts.slice(0, -1).join('')}.${parts[parts.length - 1]}`
                    : numericText.replace(/,/g, '');
            }

            const parsed = Number(numericText);
            return Number.isFinite(parsed) ? parsed : null;
        }

        const numeric = Number(value);
        return Number.isFinite(numeric) ? numeric : null;
    }

    private distanceKmFromText(value: unknown): number | null {
        const numeric = this.toNumber(value);
        if (numeric === null) return null;
        const text = String(value || '').toLowerCase();
        return text.includes('mile') || text.includes('mi') ? numeric * KM_PER_MILE : numeric;
    }

    private convertDistanceTextUnits(value: string): string {
        if (!value) return '';
        return value.replace(/(\d+(?:[,.]\d+)?)\s*km\b/gi, (_match, amount: string) => {
            const km = this.toNumber(amount);
            return km === null ? _match : this.distanceText(km);
        });
    }

    private parseDate(value?: string | null): Date | null {
        if (!value) return null;

        const match = value.match(/^(\d{4})-(\d{2})-(\d{2})$/);
        if (!match) return null;

        return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
    }

    private parseDateTime(value?: string | null): Date | null {
        if (!value) return null;

        const date = new Date(value);
        return Number.isNaN(date.getTime()) ? null : date;
    }

    private chatDateLabel(value: string): string {
        return this.chatDayLabel(this.chatDateKey(value));
    }

    private chatDayLabel(key: string): string {
        if (!key) return '날짜 없음';

        const today = new Date();
        const yesterday = this.addDays(today, -1);
        if (key === this.dateKey(today)) return '오늘';
        if (key === this.dateKey(yesterday)) return '어제';
        const date = this.parseDate(key);
        if (!date) return key;
        return `${date.getFullYear()}년 ${date.getMonth() + 1}월 ${date.getDate()}일`;
    }

    private chatSessionDayKey(session: ChatSession): string {
        return this.normalizeDateKey(session.day_key)
            || this.chatDateKey(session.updated_at)
            || this.chatDateKey(session.created_at)
            || this.chatDateKey(session.messages[0]?.created_at)
            || '';
    }

    private chatDateKey(value?: unknown): string {
        const explicit = this.normalizeDateKey(value);
        if (explicit) return explicit;
        const text = typeof value === 'string' ? value : '';
        const date = this.parseDateTime(text);
        return date ? this.dateKey(date) : '';
    }

    private formatWeatherBase(base: WeatherResponseData['base']): string {
        const date = typeof base?.date === 'string' ? base.date : '';
        const time = typeof base?.time === 'string' ? base.time : '';
        if (!/^\d{8}$/.test(date) || !/^\d{4}$/.test(time)) return '';

        return `${Number(date.slice(4, 6))}/${Number(date.slice(6, 8))} ${time.slice(0, 2)}시 발표`;
    }

    private compactChatText(value: string, maxLength: number): string {
        const text = String(value || '').replace(/\s+/g, ' ').trim();
        if (!text) return '새 대화';
        return text.length > maxLength ? `${text.slice(0, maxLength)}...` : text;
    }

    private textValue(value: unknown, fallback: string): string {
        if (typeof value !== 'string') return fallback;
        const text = value.trim();
        return text || fallback;
    }

    private normalizeWeatherTone(value: unknown): WeatherTone {
        return value === 'sunny' || value === 'cloud' || value === 'rain' || value === 'snow' || value === 'mixed'
            ? value
            : 'cloud';
    }

    private normalizeRunType(value: unknown): RunType {
        if (
            value === 'long' ||
            value === 'interval' ||
            value === 'tempo' ||
            value === 'race' ||
            value === 'recovery' ||
            value === 'strength' ||
            value === 'home_training'
        ) {
            return value;
        }
        return 'jogging';
    }

    private isRunningRecord(run: RunRecord): boolean {
        return !SUPPORT_ACTIVITY_TYPES.has(this.normalizeRunType(run.run_type));
    }

    private normalizeGoalType(value: unknown): GoalType | null {
        if (value === 'distance' || value === 'count' || value === 'duration' || value === 'pace') {
            return value;
        }
        return null;
    }

    private normalizeChallengeType(value: unknown): ChallengeType | null {
        if (value === 'total_distance' || value === 'individual_distance' || value === 'count') {
            return value;
        }
        return null;
    }

    private normalizeRankingPeriod(value: unknown): RankingPeriod | null {
        if (value === 'this_week' || value === 'last_week' || value === 'this_month') {
            return value;
        }
        return null;
    }

    private normalizeRankingScope(value: unknown): RankingScope | null {
        if (value === 'global' || value === 'following') {
            return value;
        }
        return null;
    }

    public challengeValueText(type: ChallengeType, value: unknown): string {
        const number = this.toNumber(value) || 0;
        if (type === 'count') return `${Math.round(number)}회`;
        return this.distanceText(number);
    }

    private resetChallengeForm(): void {
        this.challengeForm = {
            title: '',
            type: 'total_distance',
            goal_value: '',
            start_date: this.dateKey(new Date()),
            end_date: this.dateKey(this.addDays(new Date(), 30))
        };
    }

    private normalizeCyclePhase(value: unknown): CyclePhase {
        return this.normalizeCyclePhaseOrNull(value) || 'menstrual';
    }

    private normalizeCyclePhaseOrNull(value: unknown): CyclePhase | null {
        if (value === 'menstrual' || value === 'follicular' || value === 'ovulation' || value === 'luteal') {
            return value;
        }
        return null;
    }

    public cyclePhaseLabel(phase?: CyclePhase | null): string {
        return CYCLE_PHASE_OPTIONS.find((item) => item.id === phase)?.label || '';
    }

    private weatherIconForTone(tone: WeatherTone): string {
        if (tone === 'sunny') return 'fa-solid fa-sun';
        if (tone === 'rain') return 'fa-solid fa-umbrella';
        if (tone === 'snow') return 'fa-solid fa-snowflake';
        if (tone === 'mixed') return 'fa-solid fa-cloud-rain';
        return 'fa-solid fa-cloud';
    }

    private normalizeDateKey(value: unknown): string | null {
        const date = typeof value === 'string' ? value : '';
        return /^\d{4}-\d{2}-\d{2}$/.test(date) ? date : null;
    }

    private normalizeYearMonth(value: unknown): string | null {
        const text = typeof value === 'string' ? value : '';
        const match = text.match(/^(\d{4})-(\d{1,2})/);
        if (!match) return null;

        const month = Number(match[2]);
        if (!Number.isInteger(month) || month < 1 || month > 12) return null;
        return `${match[1]}-${String(month).padStart(2, '0')}`;
    }

    private cycleRequestHeaders(): HeadersInit {
        return {
            'Content-Type': 'application/json',
            'X-Cycle-Consent': 'true',
            ...authHeaderForUrl('/api/cycles')
        };
    }

    private cloneDefaultSettings(): AppSettings {
        return {
            ...DEFAULT_APP_SETTINGS,
            reminderDays: [...DEFAULT_APP_SETTINGS.reminderDays]
        };
    }

    private loadAppSettings(): void {
        if (typeof window === 'undefined' || !window.localStorage) {
            this.applyThemeMode();
            return;
        }

        try {
            const raw = window.localStorage.getItem(this.appSettingsStorageKey);
            this.appSettings = this.normalizeAppSettings(raw ? JSON.parse(raw) : {});
            this.healthKitAcknowledged = this.appSettings.healthKitConnected;
        } catch {
            this.appSettings = this.cloneDefaultSettings();
        } finally {
            this.pacerPersonaDraft = this.appSettings.pacerPersona;
            this.applyThemeMode();
        }
    }

    private persistAppSettings(): void {
        if (typeof window === 'undefined' || !window.localStorage) return;

        try {
            window.localStorage.setItem(this.appSettingsStorageKey, JSON.stringify(this.appSettings));
        } catch {
            return;
        }
    }

    private normalizeGender(value: unknown): string {
        const text = String(value || '').trim().toLowerCase();
        if (['male', 'm', 'man', 'men', '남', '남자', '남성'].includes(text)) return 'male';
        if (['female', 'f', 'woman', 'women', '여', '여자', '여성'].includes(text)) return 'female';
        return '';
    }

    private normalizePacerPersona(value: unknown): PacerPersona | null {
        const persona = typeof value === 'string' ? value.trim() : '';
        return PACER_PERSONA_OPTIONS.some((option) => option.id === persona) ? persona as PacerPersona : null;
    }

    private normalizeAppSettings(value: unknown): AppSettings {
        const source = value && typeof value === 'object' ? value as Record<string, unknown> : {};
        const settings = this.cloneDefaultSettings();

        if (source['unit'] === 'mile' || source['unit'] === 'km') {
            settings.unit = source['unit'];
        }
        if (source['paceDisplay'] === 'speed' || source['paceDisplay'] === 'pace') {
            settings.paceDisplay = source['paceDisplay'];
        }
        if (source['themeMode'] === 'dark' || source['themeMode'] === 'light' || source['themeMode'] === 'system') {
            settings.themeMode = source['themeMode'];
        }
        if (typeof source['notificationsEnabled'] === 'boolean') {
            settings.notificationsEnabled = source['notificationsEnabled'];
        }
        if (Array.isArray(source['reminderDays'])) {
            const validDays = new Set(WEEKDAY_OPTIONS.map((option) => option.id));
            settings.reminderDays = source['reminderDays'].filter((day): day is WeekdayId => typeof day === 'string' && validDays.has(day as WeekdayId));
        }
        if (typeof source['reminderTime'] === 'string' && /^\d{2}:\d{2}$/.test(source['reminderTime'])) {
            settings.reminderTime = source['reminderTime'];
        }
        if (typeof source['restRecommendationEnabled'] === 'boolean') {
            settings.restRecommendationEnabled = source['restRecommendationEnabled'];
        }
        if (typeof source['healthKitConnected'] === 'boolean') {
            settings.healthKitConnected = source['healthKitConnected'];
        }
        if (typeof source['appleMusicConnected'] === 'boolean') {
            settings.appleMusicConnected = source['appleMusicConnected'];
        }
        if (typeof source['appLockEnabled'] === 'boolean') {
            settings.appLockEnabled = source['appLockEnabled'];
        }
        const pacerPersona = this.normalizePacerPersona(source['pacerPersona']);
        if (pacerPersona) {
            settings.pacerPersona = pacerPersona;
        }

        return settings;
    }

    private applyThemeMode(): void {
        if (this.appSettings.themeMode === 'system') {
            this.isDark = typeof window !== 'undefined' && window.matchMedia
                ? window.matchMedia('(prefers-color-scheme: dark)').matches
                : true;
            return;
        }

        this.isDark = this.appSettings.themeMode === 'dark';
    }

    private startSystemThemeListener(): void {
        if (typeof window === 'undefined' || !window.matchMedia) return;
        if (this.systemThemeQuery) return;

        this.systemThemeQuery = window.matchMedia('(prefers-color-scheme: dark)');
        if (typeof this.systemThemeQuery.addEventListener === 'function') {
            this.systemThemeQuery.addEventListener('change', this.systemThemeListener);
        } else {
            this.systemThemeQuery.addListener(this.systemThemeListener);
        }
    }

    private installDashboardViewportSync(): void {
        if (typeof document === 'undefined' || typeof window === 'undefined') return;

        const root = document.documentElement;
        const body = document.body;
        this.dashboardThemeMeta = document.querySelector('meta[name="theme-color"]');
        this.dashboardAppRootElement = document.querySelector('app-root');
        this.previousDashboardThemeColor = this.dashboardThemeMeta?.getAttribute('content') || '';
        this.previousRootBackground = root.style.background;
        this.previousBodyBackground = body?.style.background || '';
        this.previousAppRootBackground = this.dashboardAppRootElement?.style.background || '';
        this.previousRootScreenBg = root.style.getPropertyValue(this.dashboardScreenBgProperty);
        this.previousBodyScreenBg = body?.style.getPropertyValue(this.dashboardScreenBgProperty) || '';
        this.previousAppRootScreenBg = this.dashboardAppRootElement?.style.getPropertyValue(this.dashboardScreenBgProperty) || '';

        root.classList.add(this.dashboardViewportClass);
        body?.classList.add(this.dashboardViewportClass);
        this.syncDashboardChrome();
        this.syncDashboardViewportHeight();

        window.addEventListener('resize', this.updateDashboardViewportHeight, { passive: true });
        window.addEventListener('orientationchange', this.updateDashboardViewportHeight, { passive: true });
        window.visualViewport?.addEventListener('resize', this.updateDashboardViewportHeight, { passive: true });
        window.visualViewport?.addEventListener('scroll', this.updateDashboardViewportHeight, { passive: true });
        window.setTimeout(this.updateDashboardViewportHeight, 250);
    }

    private uninstallDashboardViewportSync(): void {
        if (typeof document === 'undefined' || typeof window === 'undefined') return;

        window.removeEventListener('resize', this.updateDashboardViewportHeight);
        window.removeEventListener('orientationchange', this.updateDashboardViewportHeight);
        window.visualViewport?.removeEventListener('resize', this.updateDashboardViewportHeight);
        window.visualViewport?.removeEventListener('scroll', this.updateDashboardViewportHeight);

        const root = document.documentElement;
        const body = document.body;
        root.classList.remove(this.dashboardViewportClass);
        body?.classList.remove(this.dashboardViewportClass);
        root.style.removeProperty(this.dashboardViewportProperty);
        body?.style.removeProperty(this.dashboardViewportProperty);

        if (this.dashboardThemeMeta && this.previousDashboardThemeColor) {
            this.dashboardThemeMeta.setAttribute('content', this.previousDashboardThemeColor);
        }
        root.style.background = this.previousRootBackground;
        if (body) body.style.background = this.previousBodyBackground;
        if (this.dashboardAppRootElement) this.dashboardAppRootElement.style.background = this.previousAppRootBackground;
        this.restoreStyleProperty(root, this.dashboardScreenBgProperty, this.previousRootScreenBg);
        if (body) this.restoreStyleProperty(body, this.dashboardScreenBgProperty, this.previousBodyScreenBg);
        if (this.dashboardAppRootElement) {
            this.restoreStyleProperty(this.dashboardAppRootElement, this.dashboardScreenBgProperty, this.previousAppRootScreenBg);
        }
        this.dashboardThemeMeta = null;
        this.dashboardAppRootElement = null;
    }

    private syncDashboardChrome(): void {
        if (typeof document === 'undefined') return;

        const color = this.dashboardScreenBackground();
        const root = document.documentElement;
        const body = document.body;
        root.style.setProperty(this.dashboardScreenBgProperty, color);
        root.style.background = color;
        if (body) {
            body.style.setProperty(this.dashboardScreenBgProperty, color);
            body.style.background = color;
        }
        if (this.dashboardAppRootElement) {
            this.dashboardAppRootElement.style.setProperty(this.dashboardScreenBgProperty, color);
            this.dashboardAppRootElement.style.background = color;
        }
        this.dashboardThemeMeta?.setAttribute('content', color);
        this.setNativeSafeAreaBackground(color).catch(() => null);
    }

    private nativeAuthPlugin(): any {
        const capacitor = (window as any).Capacitor;
        if (!capacitor) return null;
        if (capacitor.Plugins?.RunningMateAuth) return capacitor.Plugins.RunningMateAuth;
        if (typeof capacitor.registerPlugin === 'function') {
            return capacitor.registerPlugin('RunningMateAuth');
        }
        return null;
    }

    private async setNativeSafeAreaBackground(color: string): Promise<void> {
        if (!isNativeLocalOrigin()) return;
        const plugin = this.nativeAuthPlugin();
        if (!plugin?.setSafeAreaBackground) return;
        await plugin.setSafeAreaBackground({ color });
    }

    private syncDashboardViewportHeight(): void {
        if (typeof document === 'undefined' || typeof window === 'undefined') return;

        const viewportHeight = Math.max(
            (window.visualViewport?.height || 0) + (window.visualViewport?.offsetTop || 0),
            window.innerHeight || 0,
            document.documentElement.clientHeight || 0
        );
        const height = Math.ceil(viewportHeight);
        if (!height) return;

        const value = `${height}px`;
        document.documentElement.style.setProperty(this.dashboardViewportProperty, value);
        document.body?.style.setProperty(this.dashboardViewportProperty, value);
    }

    private dashboardScreenBackground(): string {
        return this.isDark ? '#12121c' : '#f7f7f9';
    }

    private restoreStyleProperty(element: HTMLElement, property: string, value: string): void {
        if (value) {
            element.style.setProperty(property, value);
        } else {
            element.style.removeProperty(property);
        }
    }

    private stopSystemThemeListener(): void {
        if (!this.systemThemeQuery) return;

        if (typeof this.systemThemeQuery.removeEventListener === 'function') {
            this.systemThemeQuery.removeEventListener('change', this.systemThemeListener);
        } else {
            this.systemThemeQuery.removeListener(this.systemThemeListener);
        }
        this.systemThemeQuery = null;
    }

    private downloadTextFile(filename: string, content: string, mimeType: string): void {
        if (typeof document === 'undefined') return;

        const blob = new Blob([content], { type: mimeType });
        const url = window.URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = filename;
        anchor.rel = 'noopener';
        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();
        window.setTimeout(() => window.URL.revokeObjectURL(url), 0);
    }

    private buildRunsCsv(): string {
        const header = [
            'date',
            'distance_km',
            'avg_pace',
            'duration',
            'run_type',
            'calories',
            'avg_heart_rate',
            'cadence',
            'elevation_gain',
            'playlist_name',
            'music_url',
            'top_tracks',
            'journal'
        ];
        const rows = this.runs.map((run) => [
            run.date,
            run.distance_km,
            run.avg_pace || '',
            run.duration || '',
            run.run_type,
            run.calories ?? '',
            run.avg_heart_rate ?? '',
            run.cadence ?? '',
            run.elevation_gain ?? '',
            run.playlist_name || '',
            run.music_url || '',
            (run.top_tracks || []).map((track) => `${track.title} - ${track.artist}`).join(' | '),
            run.journal || ''
        ]);

        return [header, ...rows]
            .map((row) => row.map((value) => this.escapeCsvValue(value)).join(','))
            .join('\n');
    }

    private escapeCsvValue(value: unknown): string {
        const text = String(value ?? '');
        if (!/[",\n\r]/.test(text)) return text;
        return `"${text.replace(/"/g, '""')}"`;
    }

    private loadCycleLocalSettings(): void {
        if (typeof window === 'undefined' || !window.localStorage) return;

        try {
            this.isCycleFeatureEnabled = window.localStorage.getItem(this.cycleEnabledStorageKey) === 'true';
            const overlayValue = window.localStorage.getItem(this.cycleOverlayStorageKey);
            this.isCycleOverlayEnabled = overlayValue === null ? true : overlayValue === 'true';
            this.syncCycleDraftWithSelectedDate();
            this.refreshDerivedState();
            this.cdr.detectChanges();
        } catch {
            return;
        }
    }

    private persistCycleLocalSettings(): void {
        if (typeof window === 'undefined' || !window.localStorage) return;

        try {
            window.localStorage.setItem(this.cycleEnabledStorageKey, String(this.isCycleFeatureEnabled));
            window.localStorage.setItem(this.cycleOverlayStorageKey, String(this.isCycleOverlayEnabled));
        } catch {
            return;
        }
    }

    private syncCycleDraftWithSelectedDate(): void {
        const date = this.selectedCalendarDate || this.todayDateKey;
        if (!this.normalizeDateKey(this.cycleStartDate)) {
            this.cycleStartDate = date;
        }
        if (!this.normalizeDateKey(this.cycleEndDate)) {
            this.cycleEndDate = this.cycleStartDate;
        }
        const log = this.selectedCalendarCycleLog;
        if (log) {
            this.selectedCycleFlowLevel = this.normalizeCycleFlowLevel(log.flow_level) || this.selectedCycleFlowLevel;
            this.selectedCycleConditionEmoji = this.normalizeCycleConditionEmoji(log.condition_emoji) || this.selectedCycleConditionEmoji;
            this.cycleNoteText = log.note || '';
        } else {
            this.cycleNoteText = '';
        }
        this.isCycleNoteEditing = false;
    }

    private memoForDate(date: string | null | undefined): string {
        if (!date) return '';
        return this.calendarNotes.get(date)?.memo || '';
    }

    private syncSelectedCalendarMemo(): void {
        this.calendarMemoText = this.memoForDate(this.selectedCalendarDate);
        this.calendarMemoStatus = '';
    }

    private syncUploadJournalWithSelectedDate(): void {
        this.uploadJournalText = this.memoForDate(this.selectedCalendarDate);
        this.uploadJournalStatus = '';
    }

    private syncWeightInputForDate(): void {
        const date = this.normalizeDateKey(this.weightDate);
        if (!date) return;

        const existing = this.weightLogs.find((log) => log.date === date);
        this.weightInput = existing ? existing.weight_kg.toFixed(1) : '';
        this.weightStatus = '';
    }

    private isRestDate(date: string | null | undefined): boolean {
        return Boolean(date && this.restDays.includes(date));
    }

    private hasRunsOnDate(date: string | null | undefined): boolean {
        return Boolean(date && this.runs.some((run) => run.date === date));
    }

    private weekStart(date: Date): Date {
        const start = new Date(date);
        const day = start.getDay() || 7;
        start.setHours(0, 0, 0, 0);
        start.setDate(start.getDate() - day + 1);
        return start;
    }

    private addDays(date: Date, days: number): Date {
        const next = new Date(date);
        next.setDate(next.getDate() + days);
        return next;
    }

    private dateKey(date: Date): string {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    private showToast(message: string, type: 'success' | 'error' | 'info' = 'info'): void {
        this.toast.show(message, type);
    }

    private yearMonthKey(date: Date): string {
        return this.dateKey(date).slice(0, 7);
    }

    private selectCalendarDateKey(date: string): void {
        if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) return;
        if (Date.now() < this.calendarDateClickSuppressUntil) return;

        if (this.selectedCalendarDate !== date && !this.isUploading) {
            this.uploadProgress = 0;
            this.uploadStatus = '';
            this.calendarMediaDraftFiles = [];
            this.calendarMediaDraftStatus = '';
            this.resetRunRecordEditState();
        }
        this.selectedCalendarDate = date;
        this.syncSelectedCalendarMemo();
        this.syncUploadJournalWithSelectedDate();
        if (this.shouldShowCycleFeature && this.isCycleFeatureEnabled) {
            this.cycleStartDate = date;
            if (!this.normalizeDateKey(this.cycleEndDate) || this.cycleEndDate < date) {
                this.cycleEndDate = date;
            }
        }
        this.selectedCalendarRuns = this.buildSelectedCalendarRuns();
        this.cdr.detectChanges();
        this.revealSelectedCalendarRecords();
    }

    private revealSelectedCalendarRecords(): void {
        window.setTimeout(() => {
            this.elementRef.nativeElement
                .querySelector('.calendar-records')
                ?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }, 0);
    }

    private resizeActiveJournalInput(): void {
        window.setTimeout(() => {
            const input = this.elementRef.nativeElement.querySelector('.run-journal-input');
            if (input instanceof HTMLTextAreaElement) {
                input.style.height = 'auto';
                input.style.height = `${input.scrollHeight}px`;
                input.focus();
            }
        }, 0);
    }

    private bindNativeClick(selector: string, handler: (target: HTMLElement) => void): void {
        const host = this.elementRef.nativeElement;
        const listener = (event: Event) => {
            const target = event.target instanceof HTMLElement ? event.target.closest(selector) : null;
            if (!(target instanceof HTMLElement) || !host.contains(target)) return;

            event.preventDefault();
            event.stopPropagation();
            handler(target);
            this.cdr.detectChanges();
        };

        host.addEventListener('click', listener, true);
        this.cleanupHandlers.push(() => host.removeEventListener('click', listener, true));
    }
}
