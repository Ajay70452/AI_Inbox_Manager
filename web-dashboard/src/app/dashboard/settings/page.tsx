'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { Mail, CheckCircle, XCircle, RefreshCw } from 'lucide-react'

interface AccountToken {
  id: string
  provider: string
  email: string
  is_active: boolean
  last_sync_at: string | null
}

export default function SettingsPage() {
  const queryClient = useQueryClient()

  const { data: accounts = [], isLoading } = useQuery<AccountToken[]>({
    queryKey: ['account-tokens'],
    queryFn: async () => {
      const response = await api.get('/auth/accounts')
      return response.data.accounts || []
    },
  })

  const syncMutation = useMutation({
    mutationFn: async (provider: string) => {
      const response = await api.post(`/emails/sync?provider=${provider}`, {
        force: false,
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['account-tokens'] })
    },
  })

  const disconnectMutation = useMutation({
    mutationFn: async (accountId: string) => {
      await api.delete(`/auth/accounts/${accountId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['account-tokens'] })
    },
  })

  const handleConnectGmail = () => {
    // Get token from localStorage (where Zustand persists it)
    const authStorage = localStorage.getItem('auth-storage')
    const token = authStorage ? JSON.parse(authStorage).state.token : null

    if (token) {
      window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/auth/gmail/authorize?token=${token}`
    }
  }

  const handleConnectOutlook = () => {
    // Get token from localStorage (where Zustand persists it)
    const authStorage = localStorage.getItem('auth-storage')
    const token = authStorage ? JSON.parse(authStorage).state.token : null

    if (token) {
      window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/auth/outlook/authorize?token=${token}`
    }
  }

  const gmailAccount = accounts.find((acc) => acc.provider === 'gmail')
  const outlookAccount = accounts.find((acc) => acc.provider === 'outlook')

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-2">
          Manage your email accounts and preferences
        </p>
      </div>

      {/* Email Accounts */}
      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200 mb-8">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Email Accounts</h2>

        {/* Gmail Account */}
        <div className="mb-6">
          <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div className="flex items-center gap-4">
              <div className="bg-red-100 p-3 rounded-lg">
                <Mail className="h-6 w-6 text-red-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Gmail</h3>
                {gmailAccount ? (
                  <>
                    <p className="text-sm text-gray-600">{gmailAccount.email}</p>
                    <div className="flex items-center gap-2 mt-1">
                      {gmailAccount.is_active ? (
                        <span className="flex items-center gap-1 text-xs text-green-600">
                          <CheckCircle className="h-3 w-3" />
                          Connected
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-xs text-red-600">
                          <XCircle className="h-3 w-3" />
                          Disconnected
                        </span>
                      )}
                      {gmailAccount.last_sync_at && (
                        <span className="text-xs text-gray-500">
                          • Last sync: {new Date(gmailAccount.last_sync_at).toLocaleString()}
                        </span>
                      )}
                    </div>
                  </>
                ) : (
                  <p className="text-sm text-gray-500">Not connected</p>
                )}
              </div>
            </div>
            <div className="flex gap-2">
              {gmailAccount ? (
                <>
                  <button
                    onClick={() => syncMutation.mutate('gmail')}
                    disabled={syncMutation.isPending}
                    className="flex items-center gap-2 px-4 py-2 bg-primary-50 text-primary-700 rounded-lg hover:bg-primary-100 transition disabled:opacity-50"
                  >
                    <RefreshCw className="h-4 w-4" />
                    Sync Now
                  </button>
                  <button
                    onClick={() => disconnectMutation.mutate(gmailAccount.id)}
                    disabled={disconnectMutation.isPending}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition disabled:opacity-50"
                  >
                    Disconnect
                  </button>
                </>
              ) : (
                <button
                  onClick={handleConnectGmail}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition"
                >
                  Connect Gmail
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Outlook Account */}
        <div>
          <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div className="flex items-center gap-4">
              <div className="bg-blue-100 p-3 rounded-lg">
                <Mail className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Outlook</h3>
                {outlookAccount ? (
                  <>
                    <p className="text-sm text-gray-600">{outlookAccount.email}</p>
                    <div className="flex items-center gap-2 mt-1">
                      {outlookAccount.is_active ? (
                        <span className="flex items-center gap-1 text-xs text-green-600">
                          <CheckCircle className="h-3 w-3" />
                          Connected
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-xs text-red-600">
                          <XCircle className="h-3 w-3" />
                          Disconnected
                        </span>
                      )}
                      {outlookAccount.last_sync_at && (
                        <span className="text-xs text-gray-500">
                          • Last sync: {new Date(outlookAccount.last_sync_at).toLocaleString()}
                        </span>
                      )}
                    </div>
                  </>
                ) : (
                  <p className="text-sm text-gray-500">Not connected</p>
                )}
              </div>
            </div>
            <div className="flex gap-2">
              {outlookAccount ? (
                <>
                  <button
                    onClick={() => syncMutation.mutate('outlook')}
                    disabled={syncMutation.isPending}
                    className="flex items-center gap-2 px-4 py-2 bg-primary-50 text-primary-700 rounded-lg hover:bg-primary-100 transition disabled:opacity-50"
                  >
                    <RefreshCw className="h-4 w-4" />
                    Sync Now
                  </button>
                  <button
                    onClick={() => disconnectMutation.mutate(outlookAccount.id)}
                    disabled={disconnectMutation.isPending}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition disabled:opacity-50"
                  >
                    Disconnect
                  </button>
                </>
              ) : (
                <button
                  onClick={handleConnectOutlook}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition"
                >
                  Connect Outlook
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* AI Preferences */}
      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
        <h2 className="text-xl font-bold text-gray-900 mb-6">AI Preferences</h2>

        <div className="space-y-4">
          <div>
            <label className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">
                Auto-process new emails
              </span>
              <input type="checkbox" defaultChecked className="rounded" />
            </label>
            <p className="text-xs text-gray-500 mt-1">
              Automatically generate AI insights for incoming emails
            </p>
          </div>

          <div>
            <label className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">
                Generate auto-reply drafts
              </span>
              <input type="checkbox" defaultChecked className="rounded" />
            </label>
            <p className="text-xs text-gray-500 mt-1">
              Create AI-powered reply suggestions for all emails
            </p>
          </div>

          <div>
            <label className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">
                Extract tasks automatically
              </span>
              <input type="checkbox" defaultChecked className="rounded" />
            </label>
            <p className="text-xs text-gray-500 mt-1">
              Identify and extract action items from emails
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
