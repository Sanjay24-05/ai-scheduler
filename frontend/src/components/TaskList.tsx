/**
 * Task list component
 */
import { useState } from 'react';
import { apiService } from '../services/api';
import type { Task } from '../types';
import { format } from 'date-fns';

interface TaskListProps {
    tasks: Task[];
    onUpdate: () => void;
}

export default function TaskList({ tasks, onUpdate }: TaskListProps) {
    const [deletingId, setDeletingId] = useState<number | null>(null);

    const handleComplete = async (id: number) => {
        try {
            await apiService.completeTask(id);
            onUpdate();
        } catch (error) {
            console.error('Failed to complete task:', error);
            alert('Failed to complete task');
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm('Are you sure you want to delete this task?')) return;

        try {
            setDeletingId(id);
            await apiService.deleteTask(id);
            onUpdate();
        } catch (error) {
            console.error('Failed to delete task:', error);
            alert('Failed to delete task');
        } finally {
            setDeletingId(null);
        }
    };

    const getPriorityColor = (priority: string) => {
        switch (priority) {
            case 'high':
                return 'bg-red-100 text-red-800';
            case 'medium':
                return 'bg-yellow-100 text-yellow-800';
            case 'low':
                return 'bg-green-100 text-green-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'completed':
                return 'bg-green-100 text-green-800';
            case 'scheduled':
                return 'bg-blue-100 text-blue-800';
            case 'pending':
                return 'bg-gray-100 text-gray-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    if (tasks.length === 0) {
        return (
            <div className="text-center py-12 bg-white rounded-lg shadow">
                <p className="text-gray-500">No tasks yet. Create your first task to get started!</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {tasks.map((task) => (
                <div
                    key={task.id}
                    className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
                >
                    <div className="flex justify-between items-start">
                        <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                                <h3 className="text-lg font-semibold text-gray-900">{task.title}</h3>
                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(task.priority)}`}>
                                    {task.priority}
                                </span>
                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}>
                                    {task.status}
                                </span>
                            </div>

                            {task.description && (
                                <p className="text-gray-600 mb-3">{task.description}</p>
                            )}

                            <div className="flex flex-wrap gap-4 text-sm text-gray-500">
                                {task.estimated_duration && (
                                    <span>⏱️ {task.estimated_duration} min</span>
                                )}
                                {task.deadline && (
                                    <span>📅 Due: {format(new Date(task.deadline), 'MMM d, yyyy')}</span>
                                )}
                                {task.is_flexible && (
                                    <span>🔄 Flexible</span>
                                )}
                            </div>
                        </div>

                        <div className="flex gap-2 ml-4">
                            {task.status === 'pending' && (
                                <button
                                    onClick={() => handleComplete(task.id)}
                                    className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-sm rounded transition-colors"
                                >
                                    Complete
                                </button>
                            )}
                            <button
                                onClick={() => handleDelete(task.id)}
                                disabled={deletingId === task.id}
                                className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-sm rounded transition-colors disabled:opacity-50"
                            >
                                {deletingId === task.id ? 'Deleting...' : 'Delete'}
                            </button>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}
