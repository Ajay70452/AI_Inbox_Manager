'use client'

import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { Mail, TrendingUp, Clock, CheckCircle } from 'lucide-react'

interface DashboardStats {
  total_emails: number
  unread_emails: number
  processed_today: number
  avg_response_time: number
}

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery<DashboardStats>({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await api.get('/dashboard/stats')
      return response.data
    },
  })

  const statCards = [
    {
      name: 'Total Emails',
      value: stats?.total_emails || 0,
      icon: Mail,
      color: 'bg-blue-100 text-blue-600',
      change: '+12% from last week',
    },
    {
      name: 'Unread',
      value: stats?.unread_emails || 0,
      icon: TrendingUp,
      color: 'bg-yellow-100 text-yellow-600',
      change: '-5% from yesterday',
    },
    {
      name: 'Processed Today',
      value: stats?.processed_today || 0,
      icon: CheckCircle,
      color: 'bg-green-100 text-green-600',
      change: 'On track',
    },
    {
      name: 'Avg Response Time',
      value: `${stats?.avg_response_time || 0}h`,
      icon: Clock,
      color: 'bg-purple-100 text-purple-600',
      change: '2h faster than average',
    },
  ]

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard Overview</h1>
        <p className="text-gray-600 mt-2">
          Welcome back! Here's what's happening with your emails.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statCards.map((stat) => (
          <div key={stat.name} className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <div className={`p-3 rounded-lg ${stat.color}`}>
                <stat.icon className="h-6 w-6" />
              </div>
            </div>
            <h3 className="text-2xl font-bold text-gray-900">{stat.value}</h3>
            <p className="text-sm text-gray-600 mt-1">{stat.name}</p>
            <p className="text-xs text-gray-500 mt-2">{stat.change}</p>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Activity</h2>
        <div className="space-y-4">
          <ActivityItem
            title="Gmail sync completed"
            description="Synced 45 new emails"
            time="2 minutes ago"
            status="success"
          />
          <ActivityItem
            title="Outlook sync completed"
            description="Synced 12 new emails"
            time="5 minutes ago"
            status="success"
          />
          <ActivityItem
            title="AI processing completed"
            description="Processed 57 email threads"
            time="10 minutes ago"
            status="success"
          />
        </div>
      </div>
    </div>
  )
}

function ActivityItem({
  title,
  description,
  time,
  status,
}: {
  title: string
  description: string
  time: string
  status: 'success' | 'error' | 'warning'
}) {
  const statusColors = {
    success: 'bg-green-100 text-green-600',
    error: 'bg-red-100 text-red-600',
    warning: 'bg-yellow-100 text-yellow-600',
  }

  return (
    <div className="flex items-start gap-4 p-4 rounded-lg hover:bg-gray-50 transition">
      <div className={`p-2 rounded-full ${statusColors[status]}`}>
        <CheckCircle className="h-4 w-4" />
      </div>
      <div className="flex-1">
        <h4 className="font-medium text-gray-900">{title}</h4>
        <p className="text-sm text-gray-600">{description}</p>
      </div>
      <span className="text-xs text-gray-500">{time}</span>
    </div>
  )
}
