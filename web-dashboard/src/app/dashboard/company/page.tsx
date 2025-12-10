'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { Save, Plus, Trash2 } from 'lucide-react'

interface CompanyContext {
  id: string
  context_type: string
  title: string
  content: string
}

export default function CompanyContextPage() {
  const queryClient = useQueryClient()
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    context_type: 'policy',
    title: '',
    content: '',
  })

  const { data: contexts = [], isLoading } = useQuery<CompanyContext[]>({
    queryKey: ['company-contexts'],
    queryFn: async () => {
      const response = await api.get('/company-context')
      return response.data
    },
  })

  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.post('/company-context', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['company-contexts'] })
      resetForm()
    },
  })

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: any }) => {
      const response = await api.put(`/company-context/${id}`, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['company-contexts'] })
      setEditingId(null)
      resetForm()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/company-context/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['company-contexts'] })
    },
  })

  const resetForm = () => {
    setFormData({ context_type: 'policy', title: '', content: '' })
    setEditingId(null)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (editingId) {
      updateMutation.mutate({ id: editingId, data: formData })
    } else {
      createMutation.mutate(formData)
    }
  }

  const handleEdit = (context: CompanyContext) => {
    setEditingId(context.id)
    setFormData({
      context_type: context.context_type,
      title: context.title,
      content: context.content,
    })
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Company Context</h1>
        <p className="text-gray-600 mt-2">
          Manage your company policies, FAQs, and guidelines to improve AI responses
        </p>
      </div>

      {/* Create/Edit Form */}
      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200 mb-8">
        <h2 className="text-xl font-bold text-gray-900 mb-4">
          {editingId ? 'Edit Context' : 'Add New Context'}
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Type
            </label>
            <select
              value={formData.context_type}
              onChange={(e) => setFormData({ ...formData, context_type: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="policy">Policy</option>
              <option value="faq">FAQ</option>
              <option value="tone">Tone Guideline</option>
              <option value="product">Product Info</option>
              <option value="role">Role Definition</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Title
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="e.g., Email Response Policy"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Content
            </label>
            <textarea
              value={formData.content}
              onChange={(e) => setFormData({ ...formData, content: e.target.value })}
              rows={6}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="Enter your company context..."
              required
            />
          </div>

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={createMutation.isPending || updateMutation.isPending}
              className="flex items-center gap-2 px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition disabled:opacity-50"
            >
              <Save className="h-4 w-4" />
              {editingId ? 'Update' : 'Save'} Context
            </button>
            {editingId && (
              <button
                type="button"
                onClick={resetForm}
                className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
              >
                Cancel
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Contexts List */}
      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Existing Contexts</h2>

        {isLoading ? (
          <p className="text-gray-500">Loading...</p>
        ) : contexts.length === 0 ? (
          <p className="text-gray-500">No contexts yet. Add one above!</p>
        ) : (
          <div className="space-y-4">
            {contexts.map((context) => (
              <div
                key={context.id}
                className="p-4 border border-gray-200 rounded-lg hover:border-primary-300 transition"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="px-3 py-1 text-xs font-medium bg-primary-100 text-primary-700 rounded-full">
                        {context.context_type}
                      </span>
                      <h3 className="font-semibold text-gray-900">{context.title}</h3>
                    </div>
                    <p className="text-sm text-gray-600 whitespace-pre-wrap">
                      {context.content}
                    </p>
                  </div>
                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={() => handleEdit(context)}
                      className="p-2 text-gray-600 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => deleteMutation.mutate(context.id)}
                      className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
