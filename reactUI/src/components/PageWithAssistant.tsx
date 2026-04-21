import type { ReactNode } from 'react'
import { Grid } from '@mantine/core'
import { AssistantChat } from './AssistantChat'

export function PageWithAssistant({ children }: { children: ReactNode }) {
  return (
    <Grid align='stretch' style={{ height: 'calc(100vh - 96px)', overflow: 'hidden' }}>
      <Grid.Col span={{ base: 8, lg: 8 }} style={{ minHeight: 0 }}>
        <div style={{ height: '100%', overflowY: 'auto', paddingRight: 8 }}>
          {children}
        </div>
      </Grid.Col>
      <Grid.Col span={{ base: 4, lg: 4 }} style={{ minHeight: 0 }}>
        <div style={{ height: '100%', minHeight: 0, display: 'flex', paddingLeft: 8 }}>
          <AssistantChat />
        </div>
      </Grid.Col>
    </Grid>
  )
}