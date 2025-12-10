'use client'

import { useState, useEffect } from 'react'
import { Mail, CheckCircle, XCircle, RefreshCw } from 'lucide-react'
import api from '@/lib/api'
import { useAuthStore } from '@/stores/authStore'

interface ConnectedAccount {
  id: string
  provider: string
  email_address: string
  is_active: boolean
  connected_at: string
}

export default function IntegrationsPage() {
  const { token } = useAuthStore()
  const [accounts, setAccounts] = useState<ConnectedAccount[]>([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)

  useEffect(() => {
    loadConnectedAccounts()
  }, [])

  const loadConnectedAccounts = async () => {
    try {
      const response = await api.get('/auth/accounts')
      setAccounts(response.data.accounts || [])
    } catch (error) {
      console.error('Failed to load accounts:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleConnectGmail = () => {
    // Redirect to Gmail OAuth
    window.location.href = 'http://localhost:8000/api/v1/auth/oauth/google'
  }

  const handleConnectOutlook = () => {
    // Redirect to Outlook OAuth
    window.location.href = 'http://localhost:8000/api/v1/auth/oauth/outlook'
  }

  const handleSyncEmails = async () => {
    setSyncing(true)
    try {
      await api.post('/integrations/sync')
      alert('Email sync started! This may take a few minutes.')
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to start sync')
    } finally {
      setSyncing(false)
    }
  }

  return (
    <div className="max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Integrations</h1>
        <p className="text-gray-600">Connect your email accounts to enable AI insights</p>
      </div>

      {/* Connected Accounts */}
      {accounts.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Connected Accounts</h2>
          <div className="space-y-3">
            {accounts.map((account) => (
              <div
                key={account.id}
                className="flex items-center justify-between p-4 bg-green-50 border border-green-200 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <div>
                    <p className="font-medium text-gray-900">{account.email_address}</p>
                    <p className="text-sm text-gray-600">
                      {account.provider === 'google' ? 'Gmail' : 'Outlook'} • Connected{' '}
                      {new Date(account.connected_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleSyncEmails}
                  disabled={syncing}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  <RefreshCw className={`h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
                  {syncing ? 'Syncing...' : 'Sync Now'}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Connect New Account */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Connect Email Account</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Gmail */}
          <div className="border border-gray-200 rounded-lg p-6 hover:border-primary-500 transition">
            <div className="flex items-center gap-3 mb-4">
              <div className="bg-red-100 p-3 rounded-lg">
                <Mail className="h-6 w-6 text-red-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Gmail</h3>
                <p className="text-sm text-gray-600">Google Workspace</p>
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Connect your Gmail account to sync emails and enable AI insights.
            </p>
            <button
              onClick={handleConnectGmail}
              className="w-full bg-primary-600 text-white py-2 rounded-lg hover:bg-primary-700 transition"
            >
              Connect Gmail
            </button>
          </div>

          {/* Outlook */}
          <div className="border border-gray-200 rounded-lg p-6 hover:border-primary-500 transition">
            <div className="flex items-center gap-3 mb-4">
              <div className="bg-blue-100 p-3 rounded-lg">
                <Mail className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Outlook</h3>
                <p className="text-sm text-gray-600">Microsoft 365</p>
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Connect your Outlook account to sync emails and enable AI insights.
            </p>
            <button
              onClick={handleConnectOutlook}
              className="w-full bg-primary-600 text-white py-2 rounded-lg hover:bg-primary-700 transition"
            >
              Connect Outlook
            </button>
          </div>
        </div>
      </div>

      {/* Features Info */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-xl p-6">
        <h3 className="font-semibold text-gray-900 mb-3">What happens after connecting?</h3>
        <ul className="space-y-2 text-sm text-gray-700">
          <li className="flex items-start gap-2">
            <CheckCircle className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <span>Your emails will be synced securely (read-only access)</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <span>AI will analyze and classify emails by priority (High/Medium/Low)</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <span>Auto-reply drafts will be generated for important emails</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <span>Tasks and action items will be automatically extracted</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <span>Access AI insights via the Chrome extension sidebar in Gmail/Outlook</span>
          </li>
        </ul>
      </div>
    </div>
  )
}
