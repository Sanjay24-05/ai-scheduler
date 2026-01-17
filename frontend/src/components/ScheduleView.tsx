/**
 * Schedule view component
 */
import type { Schedule } from '../types';
import { format, parseISO } from 'date-fns';

interface ScheduleViewProps {
    schedules: Schedule[];
}

export default function ScheduleView({ schedules }: ScheduleViewProps) {
    if (schedules.length === 0) {
        return (
            <div className="text-center py-12 bg-white rounded-lg shadow">
                <p className="text-gray-500">No scheduled tasks yet. Generate a schedule to get started!</p>
            </div>
        );
    }

    // Group schedules by date
    const groupedSchedules = schedules.reduce((acc, schedule) => {
        const date = format(parseISO(schedule.start_time), 'yyyy-MM-dd');
        if (!acc[date]) {
            acc[date] = [];
        }
        acc[date].push(schedule);
        return acc;
    }, {} as Record<string, Schedule[]>);

    return (
        <div className="space-y-6">
            {Object.entries(groupedSchedules).map(([date, daySchedules]) => (
                <div key={date} className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold mb-4 text-gray-900">
                        {format(parseISO(date), 'EEEE, MMMM d, yyyy')}
                    </h3>

                    <div className="space-y-3">
                        {daySchedules
                            .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
                            .map((schedule) => (
                                <div
                                    key={schedule.id}
                                    className="border-l-4 border-primary-500 pl-4 py-2 hover:bg-gray-50 transition-colors"
                                >
                                    <div className="flex justify-between items-start">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-3 mb-1">
                                                <span className="text-sm font-medium text-gray-600">
                                                    {format(parseISO(schedule.start_time), 'h:mm a')} -{' '}
                                                    {format(parseISO(schedule.end_time), 'h:mm a')}
                                                </span>
                                                {schedule.is_synced && (
                                                    <span className="px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded-full">
                                                        ✓ Synced
                                                    </span>
                                                )}
                                            </div>

                                            <h4 className="font-semibold text-gray-900 mb-1">
                                                {schedule.task?.title || 'Unknown Task'}
                                            </h4>

                                            {schedule.task?.description && (
                                                <p className="text-sm text-gray-600 mb-2">
                                                    {schedule.task.description}
                                                </p>
                                            )}

                                            {schedule.reasoning && (
                                                <p className="text-sm text-gray-500 italic">
                                                    💡 {schedule.reasoning}
                                                </p>
                                            )}
                                        </div>

                                        <div className="flex items-center gap-2 ml-4">
                                            {schedule.task?.priority && (
                                                <span
                                                    className={`px-2 py-1 rounded-full text-xs font-medium ${schedule.task.priority === 'high'
                                                            ? 'bg-red-100 text-red-800'
                                                            : schedule.task.priority === 'medium'
                                                                ? 'bg-yellow-100 text-yellow-800'
                                                                : 'bg-green-100 text-green-800'
                                                        }`}
                                                >
                                                    {schedule.task.priority}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                    </div>
                </div>
            ))}
        </div>
    );
}
