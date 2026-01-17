/**
 * Task creation form component
 */
import { useState, type FormEvent } from 'react';
import { apiService } from '../services/api.ts';
import { TaskPriority } from '../types/index.ts';

interface TaskFormProps {
    onSuccess: () => void;
    onCancel: () => void;
}

export default function TaskForm({ onSuccess, onCancel }: TaskFormProps) {
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        priority: 'medium',
        deadline: '',
        estimated_duration: '',
        is_flexible: true,
    });
    const [analyzing, setAnalyzing] = useState(false);
    const [submitting, setSubmitting] = useState(false);

    const handleAnalyze = async () => {
        if (!formData.title) {
            alert('Please enter a task title first');
            return;
        }

        try {
            setAnalyzing(true);
            const result = await apiService.analyzeTask(formData.title);

            // Update form with AI analysis
            setFormData((prev) => ({
                ...prev,
                title: result.analysis.title || prev.title,
                estimated_duration: result.analysis.estimated_duration?.toString() || prev.estimated_duration,
                priority: result.analysis.priority || prev.priority,
                deadline: result.analysis.deadline || prev.deadline,
                is_flexible: result.analysis.is_flexible ?? prev.is_flexible,
            }));

            if (result.analysis.missing_info.length > 0) {
                alert(`AI needs more info: ${result.analysis.missing_info.join(', ')}`);
            }
        } catch (error) {
            console.error('Failed to analyze task:', error);
            alert('Failed to analyze task');
        } finally {
            setAnalyzing(false);
        }
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();

        try {
            setSubmitting(true);
            await apiService.createTask({
                title: formData.title,
                description: formData.description || undefined,
                priority: formData.priority as TaskPriority,
                deadline: formData.deadline || undefined,
                estimated_duration: formData.estimated_duration ? parseInt(formData.estimated_duration) : undefined,
                is_flexible: formData.is_flexible,
            });
            onSuccess();
        } catch (error) {
            console.error('Failed to create task:', error);
            alert('Failed to create task');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Create New Task</h3>

            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Task Title *
                    </label>
                    <div className="flex gap-2">
                        <input
                            type="text"
                            required
                            value={formData.title}
                            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                            className="input-field flex-1"
                            placeholder="e.g., Finish project report by Friday"
                        />
                        <button
                            type="button"
                            onClick={handleAnalyze}
                            disabled={analyzing}
                            className="btn-secondary whitespace-nowrap"
                        >
                            {analyzing ? 'Analyzing...' : '🤖 AI Analyze'}
                        </button>
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Description
                    </label>
                    <textarea
                        value={formData.description}
                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                        className="input-field"
                        rows={3}
                        placeholder="Additional details about the task..."
                    />
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Priority
                        </label>
                        <select
                            value={formData.priority}
                            onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                            className="input-field"
                        >
                            <option value="low">Low</option>
                            <option value="medium">Medium</option>
                            <option value="high">High</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Duration (minutes)
                        </label>
                        <input
                            type="number"
                            value={formData.estimated_duration}
                            onChange={(e) => setFormData({ ...formData, estimated_duration: e.target.value })}
                            className="input-field"
                            placeholder="60"
                            min="1"
                        />
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Deadline
                    </label>
                    <input
                        type="datetime-local"
                        value={formData.deadline}
                        onChange={(e) => setFormData({ ...formData, deadline: e.target.value })}
                        className="input-field"
                    />
                </div>

                <div className="flex items-center">
                    <input
                        type="checkbox"
                        id="is_flexible"
                        checked={formData.is_flexible}
                        onChange={(e) => setFormData({ ...formData, is_flexible: e.target.checked })}
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    />
                    <label htmlFor="is_flexible" className="ml-2 block text-sm text-gray-700">
                        Task is flexible (can be rescheduled)
                    </label>
                </div>

                <div className="flex gap-3 pt-4">
                    <button
                        type="submit"
                        disabled={submitting}
                        className="btn-primary flex-1"
                    >
                        {submitting ? 'Creating...' : 'Create Task'}
                    </button>
                    <button
                        type="button"
                        onClick={onCancel}
                        className="btn-secondary"
                    >
                        Cancel
                    </button>
                </div>
            </form>
        </div>
    );
}
