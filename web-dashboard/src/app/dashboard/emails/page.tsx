'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { Mail, TrendingUp, AlertCircle, Clock } from 'lucide-react'

interface EmailThread {
  id: string
  subject: string
  last_message_at: string
  summary?: {
    summary_text: string
  }
  priority?: {
    priority_level: string
  }
  sentiment?: {
    sentiment_label: string
  }
}

export default function EmailsPage() {
  const [filter, setFilter] = useState<'all' | 'high' | 'urgent'>('all')

  const { data: threads = [], isLoading } = useQuery<EmailThread[]>({
    queryKey: ['email-threads', filter],
    queryFn: async () => {
      const response = await api.get('/threads', {
        params: {
          priority: filter === 'all' ? undefined : filter,
          limit: 50,
        },
      })
      return response.data
    },
  })

  const priorityColors = {
    high: 'bg-red-100 text-red-700',
    medium: 'bg-yellow-100 text-yellow-700',
    low: 'bg-green-100 text-green-700',
  }

  const sentimentColors = {
    positive: 'bg-green-100 text-green-700',
    neutral: 'bg-gray-100 text-gray-700',
    negative: 'bg-red-100 text-red-700',
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Email Insights</h1>
        <p className="text-gray-600 mt-2">
          View AI-generated insights for your email threads
        </p>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-2 rounded-lg font-medium transition ${
            filter === 'all'
              ? 'bg-primary-600 text-white'
              : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'
          }`}
        >
          All
        </button>
        <button
          onClick={() => setFilter('high')}
          className={`px-4 py-2 rounded-lg font-medium transition ${
            filter === 'high'
              ? 'bg-primary-600 text-white'
              : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'
          }`}
        >
          High Priority
        </button>
        <button
          onClick={() => setFilter('urgent')}
          className={`px-4 py-2 rounded-lg font-medium transition ${
            filter === 'urgent'
              ? 'bg-primary-600 text-white'
              : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'
          }`}
        >
          Urgent
        </button>
      </div>

      {/* Threads List */}
      {isLoading ? (
        <div className="bg-white rounded-xl shadow-sm p-12 border border-gray-200 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="text-gray-500 mt-4">Loading threads...</p>
        </div>
      ) : threads.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm p-12 border border-gray-200 text-center">
          <Mail className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No threads found</h3>
          <p className="text-gray-500">Try adjusting your filters or sync your emails</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="divide-y divide-gray-200">
            {threads.map((thread) => (
              <div
                key={thread.id}
                className="p-6 hover:bg-gray-50 transition cursor-pointer"
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-semibold text-gray-900 text-lg">
                    {thread.subject || '(No subject)'}
                  </h3>
                  <span className="text-xs text-gray-500 ml-4 whitespace-nowrap">
                    {new Date(thread.last_message_at).toLocaleDateString()}
                  </span>
                </div>

                {/* Badges */}
                <div className="flex gap-2 mb-3">
                  {thread.priority && (
                    <span
                      className={`px-3 py-1 text-xs font-medium rounded-full ${
                        priorityColors[thread.priority.priority_level.toLowerCase() as keyof typeof priorityColors] || 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {thread.priority.priority_level}
                    </span>
                  )}
                  {thread.sentiment && (
                    <span
                      className={`px-3 py-1 text-xs font-medium rounded-full ${
                        sentimentColors[thread.sentiment.sentiment_label.toLowerCase() as keyof typeof sentimentColors] || 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {thread.sentiment.sentiment_label}
                    </span>
                  )}
                </div>

                {/* Summary */}
                {thread.summary && (
                  <p className="text-sm text-gray-600 line-clamp-2">
                    {thread.summary.summary_text}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
