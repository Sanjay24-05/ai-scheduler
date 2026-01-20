/**
 * Task creation form component with conversational AI
 */
import { useState, useRef, useEffect, type FormEvent } from 'react';
import { apiService } from '../services/api.ts';
import { TaskPriority, type Message } from '../types/index.ts';
import AIChatBubble from './AIChatBubble';

interface TaskFormProps {
    onSuccess: () => void;
    onCancel: () => void;
}

type FormStep = 'CHAT' | 'REVIEW';

export default function TaskForm({ onSuccess, onCancel }: TaskFormProps) {
    const [step, setStep] = useState<FormStep>('CHAT');
    const [messages, setMessages] = useState<Message[]>([
        { role: 'assistant', content: "Hi! What's on your mind? Tell me about a task you'd like to schedule." }
    ]);
    const [chatInput, setChatInput] = useState('');
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        priority: 'medium',
        deadline: '',
        estimated_duration: '',
        is_flexible: true,
    });
    const [batch, setBatch] = useState<typeof formData[]>([]);
    const [analyzing, setAnalyzing] = useState(false);
    const [submitting, setSubmitting] = useState(false);

    const chatEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleChatSubmit = async (e?: FormEvent) => {
        if (e) e.preventDefault();
        if (!chatInput.trim() || analyzing) return;

        const userMessage = chatInput.trim();
        setChatInput('');

        // Add user message to chat
        const newMessages: Message[] = [...messages, { role: 'user', content: userMessage }];
        setMessages(newMessages);

        try {
            setAnalyzing(true);

            // Only send actual user/assistant messages to AI (filter out system/intro)
            const history = newMessages.slice(1);
            const result = await apiService.analyzeTask(userMessage, history);

            const tasks = Array.isArray((result as any)?.analysis?.tasks)
                ? (result as any).analysis.tasks
                : [(result as any).analysis];

            const completed: typeof formData[] = [];
            const needsClarification: typeof formData[] = [];
            const clarificationPrompts: string[] = [];

            tasks.forEach((t: any, idx: number) => {
                const data = {
                    title: t?.title || '',
                    description: '',
                    priority: t?.priority || 'medium',
                    deadline: t?.deadline || '',
                    estimated_duration: t?.estimated_duration?.toString?.() || '',
                    is_flexible: t?.is_flexible ?? true,
                };

                if (t?.status === 'COMPLETE') {
                    completed.push(data);
                } else {
                    needsClarification.push(data);
                    if (t?.missing_info?.length) {
                        clarificationPrompts.push(`For task ${idx + 1} (${data.title || 'unnamed'}), could you clarify the ${t.missing_info.join(' or ')}?`);
                    }
                }
            });

            if (completed.length) {
                setBatch(prev => [...prev, ...completed]);
            }

            if (needsClarification.length) {
                setFormData(needsClarification[0]);
                const prompt = clarificationPrompts[0] || "I need a bit more detail for the next task.";
                setMessages([...newMessages, { role: 'assistant', content: prompt }]);
                setStep('REVIEW');
            } else {
                setMessages([...newMessages, {
                    role: 'assistant',
                    content: completed.length > 1
                        ? `Great, I detected ${completed.length} tasks and queued them. Add more or submit the batch when ready.`
                        : "Got it! I've filled in the details for you. Anything else to add, or shall we save this?"
                }]);
                setStep('REVIEW');
            }
        } catch (error) {
            console.error('Failed to analyze task:', error);
            setMessages([...newMessages, { role: 'assistant', content: "Sorry, I hit a snag. Let's try that again or fill it out manually below." }]);
        } finally {
            setAnalyzing(false);
        }
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        await handleAddToBatch();
        await handleSubmitBatch(true);
    };

    const handleAddToBatch = async () => {
        if (!formData.title.trim()) {
            alert('Title is required');
            return;
        }

        setBatch(prev => [...prev, formData]);

        // Reset form for next task
        setFormData({
            title: '',
            description: '',
            priority: 'medium',
            deadline: '',
            estimated_duration: '',
            is_flexible: true,
        });
        setStep('CHAT');
        setMessages([{ role: 'assistant', content: "Great! Add another task or submit the batch when you're ready." }]);
    };

    const handleSubmitBatch = async (skipEmptyCheck = false) => {
        if (!skipEmptyCheck && batch.length === 0) {
            alert('Add at least one task to the batch');
            return;
        }

        // Include current form data if not empty and user clicks submit-all directly
        const finalBatch = [...batch];
        if (!skipEmptyCheck && formData.title.trim()) {
            finalBatch.push(formData);
        }

        if (finalBatch.length === 0) {
            alert('Nothing to submit');
            return;
        }

        try {
            setSubmitting(true);
            await apiService.createTasks(finalBatch.map(t => ({
                title: t.title,
                description: t.description || undefined,
                priority: t.priority as TaskPriority,
                deadline: t.deadline || undefined,
                estimated_duration: t.estimated_duration ? parseInt(t.estimated_duration) : undefined,
                is_flexible: t.is_flexible,
            })));
            setBatch([]);
            onSuccess();
        } catch (error) {
            console.error('Failed to create tasks:', error);
            alert('Failed to create tasks');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="bg-gray-50 rounded-xl shadow-xl overflow-hidden border border-gray-200">
            <div className="bg-primary-600 px-6 py-4 flex justify-between items-center">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <span className="text-2xl">🤖</span> AI Task Planner
                </h3>
                <button onClick={onCancel} className="text-white/80 hover:text-white transition-colors">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <div className="flex flex-col md:flex-row h-[500px]">
                {/* Chat Section */}
                <div className="flex-1 flex flex-col bg-white border-r border-gray-100">
                    <div className="flex-1 overflow-y-auto p-4 space-y-2 custom-scrollbar">
                        {messages.map((msg, i) => (
                            <AIChatBubble key={i} message={msg} />
                        ))}
                        {analyzing && (
                            <div className="flex justify-start mb-4">
                                <div className="bg-gray-50 rounded-2xl px-4 py-2 border border-gray-100 text-gray-400">
                                    <div className="flex gap-1">
                                        <div className="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                                        <div className="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                                        <div className="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                                    </div>
                                </div>
                            </div>
                        )}
                        <div ref={chatEndRef} />
                    </div>

                    <form onSubmit={handleChatSubmit} className="p-4 bg-gray-50 border-t border-gray-100">
                        <div className="relative">
                            <input
                                type="text"
                                value={chatInput}
                                onChange={(e) => setChatInput(e.target.value)}
                                placeholder="Describe your task..."
                                className="w-full pr-12 py-3 px-4 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none shadow-sm transition-all"
                                disabled={analyzing}
                            />
                            <button
                                type="submit"
                                disabled={analyzing || !chatInput.trim()}
                                className="absolute right-2 top-1.5 p-2 text-primary-600 hover:bg-primary-50 rounded-lg transition-colors disabled:opacity-50"
                            >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                                </svg>
                            </button>
                        </div>
                    </form>
                </div>

                {/* Manual Review Section */}
                <div className={`w-full md:w-[320px] bg-gray-50/50 p-6 flex flex-col ${step === 'CHAT' ? 'opacity-90' : ''}`}>
                    <div className="flex justify-between items-center mb-6">
                        <h4 className="font-bold text-gray-700 uppercase text-[10px] tracking-widest">Manual Review</h4>
                        <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${step === 'REVIEW' ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-500'}`}>
                            {step === 'REVIEW' ? 'READY' : 'EXTRACTING...'}
                        </span>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4 flex-1 overflow-y-auto pr-2 custom-scrollbar">
                        <div>
                            <label className="text-[10px] font-bold text-gray-400 mb-1 block">TITLE</label>
                            <input
                                type="text"
                                value={formData.title}
                                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                                className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-xs focus:ring-2 focus:ring-primary-500 outline-none transition-all"
                                placeholder="Auto-filled by AI..."
                                required
                            />
                        </div>

                        <div>
                            <label className="text-[10px] font-bold text-gray-400 mb-1 block">PRIORITY</label>
                            <div className="flex gap-1.5">
                                {['low', 'medium', 'high'].map((p) => (
                                    <button
                                        key={p}
                                        type="button"
                                        onClick={() => setFormData({ ...formData, priority: p })}
                                        className={`flex-1 py-1 rounded text-[10px] font-bold transition-all border ${formData.priority === p
                                            ? 'bg-primary-600 text-white border-primary-600 shadow-sm'
                                            : 'bg-white text-gray-400 border-gray-100 hover:border-primary-200'
                                            }`}
                                    >
                                        {p.toUpperCase()}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <label className="text-[10px] font-bold text-gray-400 mb-1 block">MINS</label>
                                <input
                                    type="number"
                                    value={formData.estimated_duration}
                                    onChange={(e) => setFormData({ ...formData, estimated_duration: e.target.value })}
                                    className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-xs outline-none"
                                />
                            </div>
                            <div className="flex flex-col justify-end">
                                <label className="flex items-center gap-2 cursor-pointer pb-2">
                                    <input
                                        type="checkbox"
                                        checked={formData.is_flexible}
                                        onChange={(e) => setFormData({ ...formData, is_flexible: e.target.checked })}
                                        className="rounded border-gray-300 text-primary-600 h-3 w-3"
                                    />
                                    <span className="text-[9px] font-bold text-gray-400 uppercase">Flex</span>
                                </label>
                            </div>
                        </div>

                        <div>
                            <label className="text-[10px] font-bold text-gray-400 mb-1 block">DEADLINE</label>
                            <input
                                type="datetime-local"
                                value={formData.deadline}
                                onChange={(e) => setFormData({ ...formData, deadline: e.target.value })}
                                className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-[10px] outline-none"
                            />
                        </div>

                        <div className="pt-4 space-y-2">
                            <button
                                type="button"
                                onClick={handleAddToBatch}
                                disabled={submitting || !formData.title}
                                className="w-full py-2.5 bg-white text-primary-700 border border-primary-200 rounded-lg text-xs font-bold shadow-sm hover:bg-primary-50 transition-all disabled:opacity-50"
                            >
                                Add to Batch
                            </button>
                            <button
                                type="button"
                                onClick={() => handleSubmitBatch()}
                                disabled={submitting || (batch.length === 0 && !formData.title)}
                                className="w-full py-2.5 bg-primary-600 text-white rounded-lg text-xs font-bold shadow-md hover:bg-primary-700 transition-all disabled:opacity-50"
                            >
                                {submitting ? 'CREATING...' : `Create ${batch.length + (formData.title ? 1 : 0)} Task${batch.length + (formData.title ? 1 : 0) === 1 ? '' : 's'}`}
                            </button>
                            <button
                                type="button"
                                onClick={() => setStep('REVIEW')}
                                className="w-full py-2 text-gray-400 hover:text-primary-600 text-[10px] font-bold transition-all uppercase tracking-widest"
                            >
                            </button>
                        </div>
                    </form>

                    {batch.length > 0 && (
                        <div className="mt-4 bg-white border border-gray-100 rounded-lg p-3 text-xs space-y-2">
                            <div className="font-bold text-gray-700">Queued Tasks ({batch.length})</div>
                            <ol className="list-decimal list-inside text-gray-600 space-y-1">
                                {batch.map((t, idx) => (
                                    <li key={idx} className="flex justify-between">
                                        <span>{t.title}</span>
                                        <span className="text-gray-400">{t.priority}</span>
                                    </li>
                                ))}
                            </ol>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
