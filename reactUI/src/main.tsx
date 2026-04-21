import React from 'react'
import ReactDOM from 'react-dom/client'
import { MantineProvider } from '@mantine/core'
import { Provider } from 'react-redux'
import App from './App'
import { AuthProvider } from './context/AuthContext'
import { store } from './store'
import '@mantine/core/styles.css'
import './styles.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <MantineProvider defaultColorScheme='light'>
      <Provider store={store}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </Provider>
    </MantineProvider>
  </React.StrictMode>,
)
