/**
 * Component for displaying AI and user chat messages
 */
import type { Message } from '../types';

interface AIChatBubbleProps {
    message: Message;
}

export default function AIChatBubble({ message }: AIChatBubbleProps) {
    const isAssistant = message.role === 'assistant';

    return (
        <div className={`flex ${isAssistant ? 'justify-start' : 'justify-end'} mb-4`}>
            <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 shadow-sm ${isAssistant
                        ? 'bg-white text-gray-800 border border-gray-100'
                        : 'bg-primary-600 text-white'
                    }`}
            >
                {isAssistant && (
                    <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-bold text-primary-500 uppercase tracking-wider">
                            AI Assistant
                        </span>
                    </div>
                )}
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
            </div>
        </div>
    );
}
