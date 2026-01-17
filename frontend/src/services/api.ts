/**
 * API client service for backend communication
 */
import axios from 'axios';
import type { AxiosInstance, AxiosError } from 'axios';
import type {
    User,
    Task,
    Schedule,
    UserPreferences,
    CalendarEvent,
    AIAnalysis,
    ScheduleResult,
    Message,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class APIService {
    private client: AxiosInstance;

    constructor() {
        this.client = axios.create({
            baseURL: API_BASE_URL,
            withCredentials: true,
            headers: {
                'Content-Type': 'application/json',
            },
        });

        // Add response interceptor for error handling
        this.client.interceptors.response.use(
            (response) => response,
            (error: AxiosError) => {
                return Promise.reject(error);
            }
        );
    }

    // Authentication
    async getCurrentUser(): Promise<User> {
        const response = await this.client.get('/auth/me');
        return response.data;
    }

    async logout(): Promise<void> {
        await this.client.post('/auth/logout');
    }

    // Tasks
    async getTasks(filters?: { status?: string; priority?: string }): Promise<Task[]> {
        const response = await this.client.get('/api/tasks', { params: filters });
        return response.data;
    }

    async getTask(id: number): Promise<Task> {
        const response = await this.client.get(`/api/tasks/${id}`);
        return response.data;
    }

    async createTask(data: Partial<Task>): Promise<Task> {
        const response = await this.client.post('/api/tasks', data);
        return response.data;
    }

    async updateTask(id: number, data: Partial<Task>): Promise<Task> {
        const response = await this.client.put(`/api/tasks/${id}`, data);
        return response.data;
    }

    async deleteTask(id: number): Promise<void> {
        await this.client.delete(`/api/tasks/${id}`);
    }

    async completeTask(id: number): Promise<Task> {
        const response = await this.client.post(`/api/tasks/${id}/complete`);
        return response.data;
    }

    // AI
    async analyzeTask(description: string, history?: Message[]): Promise<{ analysis: AIAnalysis; remaining_requests: number }> {
        const response = await this.client.post('/api/ai/analyze-task', { description, history });
        return response.data;
    }

    async getClarifications(taskId: number): Promise<{ questions: string[]; remaining_requests: number }> {
        const response = await this.client.post('/api/ai/ask-clarification', { task_id: taskId });
        return response.data;
    }

    async getScheduleSuggestions(taskIds: number[]): Promise<unknown> {
        const response = await this.client.post('/api/ai/suggest-schedule', { task_ids: taskIds });
        return response.data;
    }

    // Schedule
    async generateSchedule(taskIds: number[], startDate?: string): Promise<ScheduleResult> {
        const response = await this.client.post('/api/schedule/generate', {
            task_ids: taskIds,
            start_date: startDate,
        });
        return response.data;
    }

    async rescheduleAll(): Promise<ScheduleResult> {
        const response = await this.client.post('/api/schedule/reschedule-all');
        return response.data;
    }

    async getCurrentSchedule(days: number = 7): Promise<Schedule[]> {
        const response = await this.client.get('/api/schedule/current', { params: { days } });
        return response.data;
    }

    async getDailySchedule(date: string): Promise<Schedule[]> {
        const response = await this.client.get(`/api/schedule/daily/${date}`);
        return response.data;
    }

    async getScheduleExplanation(taskId: number): Promise<unknown> {
        const response = await this.client.get(`/api/schedule/explain/${taskId}`);
        return response.data;
    }

    // Calendar
    async getCalendarEvents(days: number = 7): Promise<CalendarEvent[]> {
        const response = await this.client.get('/api/calendar/events', { params: { days } });
        return response.data;
    }

    async syncToCalendar(scheduleIds?: number[]): Promise<unknown> {
        const response = await this.client.post('/api/calendar/sync', {
            schedule_ids: scheduleIds,
        });
        return response.data;
    }

    async getAvailability(date: string, duration: number = 60): Promise<unknown> {
        const response = await this.client.get('/api/calendar/availability', {
            params: { date, duration },
        });
        return response.data;
    }

    // Settings
    async getPreferences(): Promise<UserPreferences> {
        const response = await this.client.get('/api/settings');
        return response.data;
    }

    async updatePreferences(data: Partial<UserPreferences>): Promise<UserPreferences> {
        const response = await this.client.put('/api/settings', data);
        return response.data;
    }

    // Time Guidelines (Presets)
    async getTimeGuidelines(): Promise<any[]> {
        const response = await this.client.get('/api/settings/guidelines');
        return response.data;
    }

    async createTimeGuideline(data: any): Promise<any> {
        const response = await this.client.post('/api/settings/guidelines', data);
        return response.data;
    }

    async updateTimeGuideline(id: number, data: any): Promise<any> {
        const response = await this.client.put(`/api/settings/guidelines/${id}`, data);
        return response.data;
    }

    async deleteTimeGuideline(id: number): Promise<void> {
        await this.client.delete(`/api/settings/guidelines/${id}`);
    }

    async resetPreferences(): Promise<UserPreferences> {
        const response = await this.client.post('/api/settings/reset');
        return response.data;
    }
}

export const apiService = new APIService();
