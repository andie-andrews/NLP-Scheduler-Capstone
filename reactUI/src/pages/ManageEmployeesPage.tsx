import { useEffect, useMemo, useState } from 'react'
import { Button, Card, Group, Radio, Select, Stack, Table, Text, TextInput, Title } from '@mantine/core'
import { api } from '../api/client'
import { PageWithAssistant } from '../components/PageWithAssistant'
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

  const roleSelectData = roleOptions.map((r) => ({ label: r.label, value: String(r.value) }))

  return (
    <PageWithAssistant>
      <Stack>
        <Title order={2}>Manage Employees</Title>

        <Group>
          <TextInput
            placeholder='Search employees'
            value={query}
            onChange={(e) => setQuery(e.currentTarget.value)}
            style={{ flex: 1 }}
          />
          <Button onClick={() => { setForm(emptyForm); setMode('create') }}>Create</Button>
          <Button variant='light' onClick={openEdit} disabled={!selectedEmployee}>Edit</Button>
          <Button color='red' variant='light' onClick={() => setMode('delete')} disabled={!selectedEmployee}>Delete</Button>
        </Group>

        <Table striped highlightOnHover withTableBorder withColumnBorders>
          <Table.Thead>
            <Table.Tr>
              <Table.Th />
              <Table.Th>ID</Table.Th>
              <Table.Th>Name</Table.Th>
              <Table.Th>Email</Table.Th>
              <Table.Th>Role</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {employees.map((e) => (
              <Table.Tr key={e.id}>
                <Table.Td>
                  <Radio checked={selectedId === e.id} onChange={() => setSelectedId(e.id)} aria-label={`select-${e.id}`} />
                </Table.Td>
                <Table.Td>{e.id}</Table.Td>
                <Table.Td>{e.firstName} {e.lastName}</Table.Td>
                <Table.Td>{e.email}</Table.Td>
                <Table.Td>{roleOptions.find((r) => r.value === e.roleId)?.label ?? e.roleId}</Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>

        {mode !== 'none' && (
          <Card withBorder>
            <Stack>
              <Title order={4}>{mode === 'create' ? 'Create Employee' : mode === 'edit' ? 'Edit Employee' : 'Delete Employee'}</Title>
              {mode === 'delete' ? (
                <Text>Delete {selectedEmployee?.firstName} {selectedEmployee?.lastName}?</Text>
              ) : (
                <>
                  <TextInput
                    label='First name'
                    value={form.firstName}
                    onChange={(e) => setForm((f) => ({ ...f, firstName: e.currentTarget.value }))}
                  />
                  <TextInput
                    label='Last name'
                    value={form.lastName}
                    onChange={(e) => setForm((f) => ({ ...f, lastName: e.currentTarget.value }))}
                  />
                  <TextInput
                    label='Email'
                    value={form.email}
                    onChange={(e) => setForm((f) => ({ ...f, email: e.currentTarget.value }))}
                  />
                  <Select
                    label='Role'
                    data={roleSelectData}
                    value={String(form.roleId)}
                    onChange={(value) => setForm((f) => ({ ...f, roleId: Number(value ?? 1) }))}
                    allowDeselect={false}
                  />
                </>
              )}
              <Group>
                <Button onClick={() => void submit()}>Confirm</Button>
                <Button variant='default' onClick={() => setMode('none')}>Cancel</Button>
              </Group>
            </Stack>
          </Card>
        )}
      </Stack>
    </PageWithAssistant>
  )
}
