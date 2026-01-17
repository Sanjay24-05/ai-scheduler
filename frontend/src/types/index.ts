/**
 * TypeScript type definitions for the application
 */

export interface User {
    id: number;
    google_id: string;
    email: string;
    name: string;
    profile_picture?: string;
    created_at?: string;
    updated_at?: string;
}

export const TaskPriority = {
    HIGH: 'high',
    MEDIUM: 'medium',
    LOW: 'low',
} as const;

export type TaskPriority = typeof TaskPriority[keyof typeof TaskPriority];

export const TaskStatus = {
    PENDING: 'pending',
    SCHEDULED: 'scheduled',
    COMPLETED: 'completed',
    CANCELLED: 'cancelled',
} as const;

export type TaskStatus = typeof TaskStatus[keyof typeof TaskStatus];

export interface Task {
    id: number;
    user_id: number;
    title: string;
    description?: string;
    priority: TaskPriority;
    deadline?: string;
    estimated_duration?: number;
    is_flexible: boolean;
    status: TaskStatus;
    ai_metadata?: Record<string, unknown>;
    dependencies?: number[];
    created_at?: string;
    updated_at?: string;
    completed_at?: string;
}

export interface Schedule {
    id: number;
    user_id: number;
    task_id: number;
    start_time: string;
    end_time: string;
    calendar_event_id?: string;
    is_synced: boolean;
    reasoning?: string;
    created_at?: string;
    updated_at?: string;
    task?: Task;
}

export interface UserPreferences {
    id: number;
    user_id: number;
    working_hours_start: string;
    working_hours_end: string;
    lunch_time: string;
    lunch_duration: number;
    break_frequency: number;
    break_duration: number;
    buffer_time: number;
    timezone: string;
    created_at?: string;
    updated_at?: string;
}

export interface CalendarEvent {
    id: string;
    summary: string;
    start: string;
    end: string;
    status?: string;
    description?: string;
}

export interface AIAnalysis {
    title: string;
    estimated_duration?: number;
    priority: string;
    deadline?: string;
    dependencies: number[];
    is_flexible: boolean;
    confidence: number;
    missing_info: string[];
}

export interface ScheduleResult {
    schedule: Array<{
        task_id: number;
        task_title: string;
        start_time: string;
        end_time: string;
        reasoning: string;
    }>;
    conflicts: Array<{
        task_id: number;
        task_title: string;
        reason: string;
    }>;
    message: string;
}
