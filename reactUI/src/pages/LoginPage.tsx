import { useState } from 'react'
import { Alert, Button, Paper, PasswordInput, Stack, TextInput, Title } from '@mantine/core'
import { useAuth } from '../context/AuthContext'

export function LoginPage() {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      await login(username, password)
    } catch {
      setError('Invalid credentials.')
    }
  }

  return (
    <Stack mih='100vh' justify='center' align='center' p='md'>
      <Paper component='form' onSubmit={onSubmit} withBorder radius='md' p='xl' w='100%' maw={420}>
        <Stack>
          <Title order={2}>Welcome to Scheduler Pro</Title>
          <TextInput
            label='Username'
            value={username}
            onChange={(e) => setUsername(e.currentTarget.value)}
            placeholder='Username'
            required
          />
          <PasswordInput
            label='Password'
            value={password}
            onChange={(e) => setPassword(e.currentTarget.value)}
            placeholder='Password'
            required
          />
          {error && <Alert color='red'>{error}</Alert>}
          <Button type='submit'>Login</Button>
        </Stack>
      </Paper>
    </Stack>
  )
}
