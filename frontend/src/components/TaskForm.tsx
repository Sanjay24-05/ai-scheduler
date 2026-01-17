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

            // Update form with AI analysis incrementally
            setFormData((prev) => ({
                ...prev,
                title: result.analysis.title || prev.title,
                description: prev.description, // Keep description manual
                estimated_duration: result.analysis.estimated_duration?.toString() || prev.estimated_duration,
                priority: result.analysis.priority || prev.priority,
                deadline: result.analysis.deadline || prev.deadline,
                is_flexible: result.analysis.is_flexible ?? prev.is_flexible,
            }));

            if (result.analysis.status === 'COMPLETE') {
                setMessages([...newMessages, {
                    role: 'assistant',
                    content: "Got it! I've filled in the details for you. Anything else to add, or shall we save this?"
                }]);
                setStep('REVIEW');
            } else {
                // If needs clarification, ask questions
                if (result.analysis.missing_info.length > 0) {
                    const botMsg = `Could you tell me a bit more about the ${result.analysis.missing_info.join(' or ')}?`;
                    setMessages([...newMessages, { role: 'assistant', content: botMsg }]);
                } else {
                    setMessages([...newMessages, { role: 'assistant', content: "I see. Tell me more so I can schedule this perfectly." }]);
                }
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
                                type="submit"
                                disabled={submitting || !formData.title}
                                className="w-full py-2.5 bg-primary-600 text-white rounded-lg text-xs font-bold shadow-md hover:bg-primary-700 transition-all disabled:opacity-50"
                            >
                                {submitting ? 'CREATING...' : 'CREATE TASK'}
                            </button>
                            <button
                                type="button"
                                onClick={() => setStep('REVIEW')}
                                className="w-full py-2 text-gray-400 hover:text-primary-600 text-[10px] font-bold transition-all uppercase tracking-widest"
                            >
                                Manual Entry 👉
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}
