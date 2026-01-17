/**
 * Main Dashboard component
 */
import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { apiService } from '../services/api.ts';
import type { Task, Schedule } from '../types/index.ts';
import TaskList from '../components/TaskList.tsx';
import TaskForm from '../components/TaskForm.tsx';
import ScheduleView from '../components/ScheduleView.tsx';

export default function Dashboard() {
    const { user, logout } = useAuth();
    const [tasks, setTasks] = useState<Task[]>([]);
    const [schedules, setSchedules] = useState<Schedule[]>([]);
    const [loading, setLoading] = useState(true);
    const [showTaskForm, setShowTaskForm] = useState(false);
    const [activeTab, setActiveTab] = useState<'tasks' | 'schedule'>('tasks');

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [tasksData, schedulesData] = await Promise.all([
                apiService.getTasks(),
                apiService.getCurrentSchedule(),
            ]);
            setTasks(tasksData);
            setSchedules(schedulesData);
        } catch (error) {
            console.error('Failed to load data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleTaskCreated = () => {
        setShowTaskForm(false);
        loadData();
    };

    const handleGenerateSchedule = async () => {
        try {
            const pendingTasks = tasks.filter((t) => t.status === 'pending');
            const taskIds = pendingTasks.map((t) => t.id);

            if (taskIds.length === 0) {
                alert('No pending tasks to schedule');
                return;
            }

            await apiService.generateSchedule(taskIds);
            await loadData();
            setActiveTab('schedule');
            alert('Schedule generated successfully!');
        } catch (error) {
            console.error('Failed to generate schedule:', error);
            alert('Failed to generate schedule');
        }
    };

    const handleSyncToCalendar = async () => {
        try {
            await apiService.syncToCalendar();
            await loadData();
            alert('Schedule synced to Google Calendar successfully!');
        } catch (error) {
            console.error('Failed to sync to calendar:', error);
            alert('Failed to sync to Google Calendar. Please make sure you have granted calendar permissions.');
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-xl">Loading...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex justify-between items-center">
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">AI Scheduler</h1>
                            <p className="text-sm text-gray-600">Welcome, {user?.name}</p>
                        </div>
                        <div className="flex gap-4">
                            <button
                                onClick={handleSyncToCalendar}
                                className="btn-secondary"
                            >
                                Sync to Calendar
                            </button>
                            <button
                                onClick={handleGenerateSchedule}
                                className="btn-primary"
                            >
                                Generate Schedule
                            </button>
                            <button
                                onClick={logout}
                                className="btn-secondary"
                            >
                                Logout
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Tabs */}
                <div className="mb-6 border-b border-gray-200">
                    <nav className="-mb-px flex space-x-8">
                        <button
                            onClick={() => setActiveTab('tasks')}
                            className={`py-4 px-1 border-b-2 font-medium text-sm ${activeTab === 'tasks'
                                ? 'border-primary-500 text-primary-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                }`}
                        >
                            Tasks ({tasks.length})
                        </button>
                        <button
                            onClick={() => setActiveTab('schedule')}
                            className={`py-4 px-1 border-b-2 font-medium text-sm ${activeTab === 'schedule'
                                ? 'border-primary-500 text-primary-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                }`}
                        >
                            Schedule ({schedules.length})
                        </button>
                    </nav>
                </div>

                {/* Content */}
                {activeTab === 'tasks' ? (
                    <div>
                        <div className="mb-4 flex justify-between items-center">
                            <h2 className="text-xl font-semibold">Your Tasks</h2>
                            <button
                                onClick={() => setShowTaskForm(true)}
                                className="btn-primary"
                            >
                                + Add Task
                            </button>
                        </div>

                        {showTaskForm && (
                            <div className="mb-6">
                                <TaskForm
                                    onSuccess={handleTaskCreated}
                                    onCancel={() => setShowTaskForm(false)}
                                />
                            </div>
                        )}

                        <TaskList tasks={tasks} onUpdate={loadData} />
                    </div>
                ) : (
                    <div>
                        <h2 className="text-xl font-semibold mb-4">Your Schedule</h2>
                        <ScheduleView
                            schedules={schedules}
                            onSync={handleSyncToCalendar}
                        />
                    </div>
                )}
            </main>
        </div>
    );
}
