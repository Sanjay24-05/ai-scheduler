/**
 * Time Guidelines management component
 */
import { useState, useEffect } from 'react';
import { apiService } from '../services/api.ts';

interface MiscBreak {
    start_time: string;
    duration: number;
}

interface Guideline {
    id: number;
    name: string;
    working_hours_start: string | null;
    working_hours_end: string | null;
    lunch_time: string | null;
    lunch_duration: number;
    misc_breaks: MiscBreak[];
    days_of_week: number[];
    start_date: string | null;
    end_date: string | null;
    is_active: boolean;
}

export default function TimeGuidelines() {
    const [guidelines, setGuidelines] = useState<Guideline[]>([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [editingId, setEditingId] = useState<number | null>(null);

    const initialFormData = {
        name: '',
        working_hours_start: '',
        working_hours_end: '',
        lunch_time: '',
        lunch_duration: 60,
        buffer_time: 5,
        misc_breaks: [] as MiscBreak[],
        days_of_week: [1, 2, 3, 4, 5],
        start_date: '',
        end_date: '',
        is_active: true
    };

    const [formData, setFormData] = useState(initialFormData);

    useEffect(() => {
        loadGuidelines();
    }, []);

    const loadGuidelines = async () => {
        try {
            setLoading(true);
            const data = await apiService.getTimeGuidelines();
            setGuidelines(data);
        } catch (error) {
            console.error('Failed to load guidelines:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        // Validation: At least one time guideline must be set
        const hasWorkHours = formData.working_hours_start && formData.working_hours_end;
        const hasLunch = formData.lunch_time;
        const hasMiscBreaks = formData.misc_breaks.length > 0;

        if (!hasWorkHours && !hasLunch && !hasMiscBreaks) {
            alert('Please specify at least one time guideline (Working Hours, Lunch, or a Misc Break).');
            return;
        }

        try {
            const dataToSave = {
                ...formData,
                working_hours_start: formData.working_hours_start || null,
                working_hours_end: formData.working_hours_end || null,
                lunch_time: formData.lunch_time || null,
                start_date: formData.start_date || null,
                end_date: formData.end_date || null,
            };

            if (editingId) {
                await apiService.updateTimeGuideline(editingId, dataToSave);
            } else {
                await apiService.createTimeGuideline(dataToSave);
            }

            setShowForm(false);
            setEditingId(null);
            setFormData(initialFormData);
            loadGuidelines();
        } catch (error) {
            console.error('Failed to save guideline:', error);
            alert('Error saving guideline');
        }
    };

    const handleToggleActive = async (g: Guideline) => {
        try {
            await apiService.updateTimeGuideline(g.id, { is_active: !g.is_active });
            loadGuidelines();
        } catch (error) {
            console.error('Failed to toggle active status:', error);
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm('Are you sure you want to delete this preset?')) return;
        try {
            await apiService.deleteTimeGuideline(id);
            loadGuidelines();
        } catch (error) {
            console.error('Failed to delete guideline:', error);
        }
    };

    const handleEdit = (g: Guideline) => {
        setFormData({
            name: g.name,
            working_hours_start: g.working_hours_start ? g.working_hours_start.substring(0, 5) : '',
            working_hours_end: g.working_hours_end ? g.working_hours_end.substring(0, 5) : '',
            lunch_time: g.lunch_time ? g.lunch_time.substring(0, 5) : '',
            lunch_duration: g.lunch_duration,
            buffer_time: g.buffer_time || 5,
            misc_breaks: g.misc_breaks || [],
            days_of_week: g.days_of_week,
            start_date: g.start_date || '',
            end_date: g.end_date || '',
            is_active: g.is_active
        });
        setEditingId(g.id);
        setShowForm(true);
    };

    const toggleDay = (day: number) => {
        setFormData(prev => ({
            ...prev,
            days_of_week: prev.days_of_week.includes(day)
                ? prev.days_of_week.filter(d => d !== day)
                : [...prev.days_of_week, day]
        }));
    };

    const addMiscBreak = () => {
        setFormData(prev => ({
            ...prev,
            misc_breaks: [...prev.misc_breaks, { start_time: '15:00', duration: 15 }]
        }));
    };

    const updateMiscBreak = (index: number, field: keyof MiscBreak, value: any) => {
        const newBreaks = [...formData.misc_breaks];
        newBreaks[index] = { ...newBreaks[index], [field]: value };
        setFormData(prev => ({ ...prev, misc_breaks: newBreaks }));
    };

    const removeMiscBreak = (index: number) => {
        setFormData(prev => ({
            ...prev,
            misc_breaks: prev.misc_breaks.filter((_, i) => i !== index)
        }));
    };

    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

    if (loading && guidelines.length === 0) return <div className="p-8 text-center text-gray-500">Loading guidelines...</div>;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h3 className="text-xl font-bold text-gray-800">Time Guidelines & Presets</h3>
                <button
                    onClick={() => { setShowForm(!showForm); setEditingId(null); setFormData(initialFormData); }}
                    className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-bold shadow hover:bg-primary-700 transition-all"
                >
                    {showForm ? 'Cancel' : '+ New Preset'}
                </button>
            </div>

            {showForm && (
                <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm animate-in fade-in slide-in-from-top-4 duration-300">
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="col-span-full">
                                <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Preset Name</label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={e => setFormData({ ...formData, name: e.target.value })}
                                    className="w-full px-4 py-2 bg-gray-50 border border-gray-100 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none transition-all"
                                    placeholder="e.g., Standard Work Week"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2 italic">Working Hours Start (Optional)</label>
                                <input
                                    type="time"
                                    value={formData.working_hours_start}
                                    onChange={e => setFormData({ ...formData, working_hours_start: e.target.value })}
                                    className="w-full px-4 py-2 bg-gray-50 border border-gray-100 rounded-lg outline-none"
                                />
                            </div>

                            <div>
                                <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2 italic">Working Hours End (Optional)</label>
                                <input
                                    type="time"
                                    value={formData.working_hours_end}
                                    onChange={e => setFormData({ ...formData, working_hours_end: e.target.value })}
                                    className="w-full px-4 py-2 bg-gray-50 border border-gray-100 rounded-lg outline-none"
                                />
                            </div>

                            <div>
                                <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2 italic">Lunch Time (Optional)</label>
                                <input
                                    type="time"
                                    value={formData.lunch_time}
                                    onChange={e => setFormData({ ...formData, lunch_time: e.target.value })}
                                    className="w-full px-4 py-2 bg-gray-50 border border-gray-100 rounded-lg outline-none"
                                />
                            </div>

                            <div>
                                <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Lunch Duration (min)</label>
                                <input
                                    type="number"
                                    value={formData.lunch_duration}
                                    onChange={e => setFormData({ ...formData, lunch_duration: parseInt(e.target.value) })}
                                    className="w-full px-4 py-2 bg-gray-50 border border-gray-100 rounded-lg outline-none"
                                />
                            </div>

                            <div>
                                <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Buffer Between Tasks (min)</label>
                                <input
                                    type="number"
                                    value={formData.buffer_time}
                                    onChange={e => setFormData({ ...formData, buffer_time: parseInt(e.target.value) })}
                                    className="w-full px-4 py-2 bg-gray-50 border border-gray-100 rounded-lg outline-none"
                                />
                            </div>

                            <div className="col-span-full border-t border-gray-50 pt-4">
                                <div className="flex justify-between items-center mb-4">
                                    <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest">Miscellaneous Breaks (Optional)</label>
                                    <button
                                        type="button"
                                        onClick={addMiscBreak}
                                        className="text-[10px] font-bold text-primary-600 hover:text-primary-700 uppercase tracking-widest"
                                    >
                                        + Add Break
                                    </button>
                                </div>

                                <div className="space-y-3">
                                    {formData.misc_breaks.map((brk, idx) => (
                                        <div key={idx} className="flex items-center gap-4 bg-gray-50/50 p-3 rounded-lg border border-gray-100 animate-in fade-in zoom-in-95 duration-200">
                                            <div className="flex-1 grid grid-cols-2 gap-4">
                                                <div>
                                                    <label className="block text-[10px] text-gray-400 mb-1">Start Time</label>
                                                    <input
                                                        type="time"
                                                        value={brk.start_time}
                                                        onChange={e => updateMiscBreak(idx, 'start_time', e.target.value)}
                                                        className="w-full bg-transparent text-sm font-medium outline-none"
                                                    />
                                                </div>
                                                <div>
                                                    <label className="block text-[10px] text-gray-400 mb-1">Duration (min)</label>
                                                    <input
                                                        type="number"
                                                        value={brk.duration}
                                                        onChange={e => updateMiscBreak(idx, 'duration', parseInt(e.target.value))}
                                                        className="w-full bg-transparent text-sm font-medium outline-none"
                                                    />
                                                </div>
                                            </div>
                                            <button
                                                type="button"
                                                onClick={() => removeMiscBreak(idx)}
                                                className="text-red-300 hover:text-red-500 transition-colors"
                                            >
                                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                                            </button>
                                        </div>
                                    ))}
                                    {formData.misc_breaks.length === 0 && (
                                        <p className="text-[10px] text-gray-400 italic">No miscellaneous breaks added.</p>
                                    )}
                                </div>
                            </div>

                            <div className="col-span-full border-t border-gray-50 pt-4">
                                <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">Applicable Days</label>
                                <div className="flex flex-wrap gap-2">
                                    {days.map((day, idx) => (
                                        <button
                                            key={day}
                                            type="button"
                                            onClick={() => toggleDay(idx)}
                                            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all border ${formData.days_of_week.includes(idx)
                                                    ? 'bg-primary-600 text-white border-primary-600'
                                                    : 'bg-white text-gray-400 border-gray-100 hover:border-primary-200'
                                                }`}
                                        >
                                            {day}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className="border-t border-gray-50 pt-4">
                                <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Start Date (Optional)</label>
                                <input
                                    type="date"
                                    value={formData.start_date}
                                    onChange={e => setFormData({ ...formData, start_date: e.target.value })}
                                    className="w-full px-4 py-2 bg-gray-50 border border-gray-100 rounded-lg outline-none"
                                />
                            </div>

                            <div className="border-t border-gray-50 pt-4">
                                <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">End Date (Optional)</label>
                                <input
                                    type="date"
                                    value={formData.end_date}
                                    onChange={e => setFormData({ ...formData, end_date: e.target.value })}
                                    className="w-full px-4 py-2 bg-gray-50 border border-gray-100 rounded-lg outline-none"
                                />
                            </div>
                        </div>

                        <div className="flex justify-end gap-3 pt-4 border-t border-gray-50">
                            <button
                                type="button"
                                onClick={() => { setShowForm(false); setEditingId(null); }}
                                className="px-6 py-2 text-gray-400 font-bold hover:text-gray-600 transition-all uppercase text-xs tracking-widest"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                className="px-8 py-2 bg-primary-600 text-white rounded-lg text-xs font-bold shadow-lg hover:shadow-primary-200 transition-all uppercase tracking-widest"
                            >
                                {editingId ? 'Update Preset' : 'Create Preset'}
                            </button>
                        </div>
                    </form>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {guidelines.map(g => (
                    <div
                        key={g.id}
                        className={`group p-6 rounded-xl border transition-all ${g.is_active
                                ? 'bg-white border-primary-100 shadow-sm'
                                : 'bg-gray-50/50 border-gray-100 opacity-75'
                            }`}
                    >
                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <h4 className="font-bold text-gray-800 text-lg group-hover:text-primary-600 transition-colors uppercase tracking-tight">{g.name}</h4>
                                <div className="flex gap-1.5 mt-1">
                                    {days.map((day, idx) => (
                                        <span
                                            key={day}
                                            className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${g.days_of_week.includes(idx)
                                                    ? 'bg-primary-50 text-primary-600'
                                                    : 'text-gray-300'
                                                }`}
                                        >
                                            {day[0]}
                                        </span>
                                    ))}
                                </div>
                            </div>
                            <button
                                onClick={() => handleToggleActive(g)}
                                className={`relative inline-flex h-5 w-10 items-center rounded-full transition-colors focus:outline-none ${g.is_active ? 'bg-green-500' : 'bg-gray-200'
                                    }`}
                            >
                                <span className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${g.is_active ? 'translate-x-6' : 'translate-x-1'
                                    }`} />
                            </button>
                        </div>

                        <div className="space-y-3 mb-6">
                            {g.working_hours_start && (
                                <div className="flex items-center gap-4 text-xs">
                                    <span className="text-gray-400 font-bold w-12">HOURS</span>
                                    <span className="text-gray-600 font-medium">
                                        {g.working_hours_start.substring(0, 5)} - {g.working_hours_end?.substring(0, 5)}
                                    </span>
                                </div>
                            )}
                            {g.lunch_time && (
                                <div className="flex items-center gap-4 text-xs">
                                    <span className="text-gray-400 font-bold w-12">LUNCH</span>
                                    <span className="text-gray-600 font-medium">
                                        {g.lunch_time.substring(0, 5)} ({g.lunch_duration}m)
                                    </span>
                                </div>
                            )}
                            <div className="flex items-center gap-4 text-xs">
                                <span className="text-gray-400 font-bold w-12">BUFFER</span>
                                <span className="text-gray-600 font-medium">
                                    {g.buffer_time || 5}m between tasks
                                </span>
                            </div>
                            {g.misc_breaks && g.misc_breaks.length > 0 && (
                                <div className="flex items-start gap-4 text-xs">
                                    <span className="text-gray-400 font-bold w-12 mt-0.5">BREAKS</span>
                                    <div className="flex flex-wrap gap-1.5">
                                        {g.misc_breaks.map((brk, i) => (
                                            <span key={i} className="bg-gray-100 px-2 py-0.5 rounded text-gray-500 font-medium">
                                                {brk.start_time.substring(0, 5)} ({brk.duration}m)
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                            {(g.start_date || g.end_date) && (
                                <div className="flex items-center gap-4 text-xs">
                                    <span className="text-gray-400 font-bold w-12">RANGE</span>
                                    <span className="text-gray-600 font-medium italic">
                                        {g.start_date || '...'} to {g.end_date || '...'}
                                    </span>
                                </div>
                            )}
                        </div>

                        <div className="flex justify-end gap-3 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                                onClick={() => handleEdit(g)}
                                className="text-primary-600 hover:text-primary-700 font-bold text-[10px] uppercase tracking-widest"
                            >
                                Edit
                            </button>
                            <button
                                onClick={() => handleDelete(g.id)}
                                className="text-red-400 hover:text-red-600 font-bold text-[10px] uppercase tracking-widest"
                            >
                                Delete
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {guidelines.length === 0 && !showForm && (
                <div className="py-12 text-center bg-gray-50/50 rounded-xl border border-dashed border-gray-200">
                    <p className="text-gray-400 text-sm">No scheduling presets found. Create your first one to get started!</p>
                </div>
            )}
        </div>
    );
}
