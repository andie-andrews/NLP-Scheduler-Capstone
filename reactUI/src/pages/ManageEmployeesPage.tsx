import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import type { Employee } from '../types'

const roleOptions = [
  { label: 'Employee', value: 1 },
  { label: 'Supervisor', value: 2 },
]

const emptyForm = { firstName: '', lastName: '', email: '', roleId: 1 }

export function ManageEmployeesPage() {
  const { user } = useAuth()
  const [employees, setEmployees] = useState<Employee[]>([])
  const [query, setQuery] = useState('')
  const [mode, setMode] = useState<'none'|'create'|'edit'|'delete'>('none')
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [form, setForm] = useState(emptyForm)

  const load = () => {
    if (!user) return
    api.getEmployees(user.token, query || undefined).then(setEmployees).catch(() => setEmployees([]))
  }

  useEffect(load, [query, user])

  const selectedEmployee = useMemo(() => employees.find((e) => e.id === selectedId) ?? null, [employees, selectedId])

  const openEdit = () => {
    if (!selectedEmployee) return
    setForm({ firstName: selectedEmployee.firstName, lastName: selectedEmployee.lastName, email: selectedEmployee.email, roleId: selectedEmployee.roleId })
    setMode('edit')
  }

  const submit = async () => {
    if (!user) return
    if (mode === 'create') await api.createEmployee(user.token, form)
    if (mode === 'edit' && selectedEmployee) await api.updateEmployee(user.token, selectedEmployee.id, form)
    if (mode === 'delete' && selectedEmployee) await api.deleteEmployee(user.token, selectedEmployee.id)
    setMode('none')
    setForm(emptyForm)
    load()
  }

  return (
    <section>
      <h2>Manage Employees</h2>
      <input placeholder='Search employees' value={query} onChange={(e) => setQuery(e.target.value)} />
      <div style={{ margin: '8px 0' }}>
        <button onClick={() => { setForm(emptyForm); setMode('create') }}>➕</button>
        <button onClick={openEdit} disabled={!selectedEmployee}>✎</button>
        <button onClick={() => setMode('delete')} disabled={!selectedEmployee}>🗑️</button>
      </div>
      <table><thead><tr><th></th><th>ID</th><th>Name</th><th>Email</th><th>Role</th></tr></thead>
      <tbody>{employees.map((e) => <tr key={e.id}><td><input type='radio' checked={selectedId===e.id} onChange={() => setSelectedId(e.id)} /></td><td>{e.id}</td><td>{e.firstName} {e.lastName}</td><td>{e.email}</td><td>{roleOptions.find((r)=>r.value===e.roleId)?.label ?? e.roleId}</td></tr>)}</tbody></table>

      {mode !== 'none' && (
        <div style={{ marginTop: 16, border: '1px solid #ddd', padding: 12 }}>
          <h3>{mode === 'create' ? 'Create Employee' : mode === 'edit' ? 'Edit Employee' : 'Delete Employee'}</h3>
          {mode === 'delete' ? <p>Delete {selectedEmployee?.firstName} {selectedEmployee?.lastName}?</p> : (
            <>
              <input placeholder='First name' value={form.firstName} onChange={(e) => setForm((f) => ({ ...f, firstName: e.target.value }))} />
              <input placeholder='Last name' value={form.lastName} onChange={(e) => setForm((f) => ({ ...f, lastName: e.target.value }))} />
              <input placeholder='Email' value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} />
              <select value={form.roleId} onChange={(e) => setForm((f) => ({ ...f, roleId: Number(e.target.value) }))}>
                {roleOptions.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
              </select>
            </>
          )}
          <button onClick={submit}>Confirm</button>
          <button onClick={() => setMode('none')}>Cancel</button>
        </div>
      )}
    </section>
  )
}
