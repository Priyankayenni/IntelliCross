# 🎨 FRONTEND-SUPABASE INTEGRATION

**Complete React & Supabase Setup Guide with Code Examples**

---

## 🔌 Supabase Setup in React

### Step 1: Install Supabase Client

```bash
npm install @supabase/supabase-js
```

### Step 2: Create Supabase Configuration

**File: `src/lib/supabase.ts`**

```typescript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseKey = import.meta.env.VITE_SUPABASE_KEY

if (!supabaseUrl || !supabaseKey) {
  throw new Error('Missing Supabase credentials')
}

export const supabase = createClient(supabaseUrl, supabaseKey)
```

### Step 3: Environment Variables

**File: `.env`**

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_KEY=your-anon-public-key-here
VITE_API_URL=https://your-backend.onrender.com
```

---

## 🔐 Authentication Setup

### Authentication Service

**File: `src/services/auth.ts`**

```typescript
import { supabase } from '../lib/supabase'

export const authService = {
  // Sign up with email and password
  async signUp(email: string, password: string, fullName: string) {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: fullName,
        },
      },
    })
    
    if (error) throw new Error(error.message)
    return data
  },

  // Sign in with email and password
  async signIn(email: string, password: string) {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })
    
    if (error) throw new Error(error.message)
    return data
  },

  // Sign out
  async signOut() {
    const { error } = await supabase.auth.signOut()
    if (error) throw new Error(error.message)
  },

  // Get current user
  async getCurrentUser() {
    const { data: { user } } = await supabase.auth.getUser()
    return user
  },

  // Reset password
  async resetPassword(email: string) {
    const { error } = await supabase.auth.resetPasswordForEmail(email)
    if (error) throw new Error(error.message)
  },

  // Update password
  async updatePassword(newPassword: string) {
    const { error } = await supabase.auth.updateUser({
      password: newPassword,
    })
    if (error) throw new Error(error.message)
  },
}
```

### Authentication Hook

**File: `src/hooks/useAuth.ts`**

```typescript
import { useState, useEffect } from 'react'
import { User, Session } from '@supabase/supabase-js'
import { supabase } from '../lib/supabase'

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setSession(session)
        setUser(session?.user ?? null)
      }
    )

    return () => {
      subscription?.unsubscribe()
    }
  }, [])

  return {
    user,
    session,
    loading,
    error,
    isAuthenticated: !!user,
  }
}
```

---

## 📊 Data Operations

### Detection Service

**File: `src/services/detection.ts`**

```typescript
import { supabase } from '../lib/supabase'

export interface Detection {
  id: string
  type: string
  confidence: number
  location: { lat: number; lng: number }
  image_url?: string
  created_at: string
}

export const detectionService = {
  // Get all detections
  async getDetections(limit = 50) {
    const { data, error } = await supabase
      .from('detections')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(limit)

    if (error) throw new Error(error.message)
    return data as Detection[]
  },

  // Get detections by type
  async getDetectionsByType(type: string, limit = 50) {
    const { data, error } = await supabase
      .from('detections')
      .select('*')
      .eq('detection_type', type)
      .order('created_at', { ascending: false })
      .limit(limit)

    if (error) throw new Error(error.message)
    return data as Detection[]
  },

  // Get recent detections (last 24 hours)
  async getRecentDetections() {
    const { data, error } = await supabase
      .from('detections')
      .select('*')
      .gte('created_at', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString())
      .order('created_at', { ascending: false })

    if (error) throw new Error(error.message)
    return data as Detection[]
  },

  // Get detection by ID
  async getDetection(id: string) {
    const { data, error } = await supabase
      .from('detections')
      .select('*')
      .eq('id', id)
      .single()

    if (error) throw new Error(error.message)
    return data as Detection
  },

  // Create detection
  async createDetection(detection: Omit<Detection, 'id' | 'created_at'>) {
    const { data, error } = await supabase
      .from('detections')
      .insert([detection])
      .select()

    if (error) throw new Error(error.message)
    return data[0] as Detection
  },

  // Subscribe to new detections
  subscribeToDetections(callback: (detection: Detection) => void) {
    const subscription = supabase
      .from('detections')
      .on('*', (payload) => {
        callback(payload.new as Detection)
      })
      .subscribe()

    return subscription
  },
}
```

### Alerts Service

**File: `src/services/alerts.ts`**

```typescript
import { supabase } from '../lib/supabase'

export interface Alert {
  id: string
  type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  status: 'pending' | 'acknowledged' | 'resolved'
  hospital_id?: string
  created_at: string
  updated_at: string
}

export const alertService = {
  // Get all alerts for current user
  async getAlerts(status?: string) {
    let query = supabase
      .from('alerts')
      .select('*')
      .order('created_at', { ascending: false })

    if (status) {
      query = query.eq('status', status)
    }

    const { data, error } = await query

    if (error) throw new Error(error.message)
    return data as Alert[]
  },

  // Get critical alerts
  async getCriticalAlerts() {
    const { data, error } = await supabase
      .from('alerts')
      .select('*')
      .eq('severity', 'critical')
      .eq('status', 'pending')
      .order('created_at', { ascending: false })

    if (error) throw new Error(error.message)
    return data as Alert[]
  },

  // Update alert status
  async updateAlertStatus(alertId: string, status: string) {
    const { data, error } = await supabase
      .from('alerts')
      .update({ status, updated_at: new Date().toISOString() })
      .eq('id', alertId)
      .select()

    if (error) throw new Error(error.message)
    return data[0] as Alert
  },

  // Subscribe to alerts
  subscribeToAlerts(callback: (alert: Alert) => void) {
    const subscription = supabase
      .from('alerts')
      .on('*', (payload) => {
        callback(payload.new as Alert)
      })
      .subscribe()

    return subscription
  },
}
```

---

## 🎨 React Components

### Alert Component

**File: `src/components/AlertTray.tsx`**

```typescript
import React, { useState, useEffect } from 'react'
import { Alert, alertService } from '../services/alerts'

export const AlertTray: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadAlerts()

    // Subscribe to new alerts
    const subscription = alertService.subscribeToAlerts((newAlert) => {
      setAlerts((prev) => [newAlert, ...prev])
    })

    return () => {
      subscription?.unsubscribe()
    }
  }, [])

  const loadAlerts = async () => {
    try {
      setLoading(true)
      const data = await alertService.getAlerts()
      setAlerts(data)
    } catch (error) {
      console.error('Failed to load alerts:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAcknowledge = async (alertId: string) => {
    try {
      await alertService.updateAlertStatus(alertId, 'acknowledged')
      setAlerts((prev) =>
        prev.map((alert) =>
          alert.id === alertId ? { ...alert, status: 'acknowledged' } : alert
        )
      )
    } catch (error) {
      console.error('Failed to update alert:', error)
    }
  }

  if (loading) return <div>Loading alerts...</div>

  return (
    <div className="alert-tray bg-white rounded-lg shadow-lg p-4">
      <h2 className="text-xl font-bold mb-4">Active Alerts</h2>
      {alerts.length === 0 ? (
        <p className="text-gray-500">No active alerts</p>
      ) : (
        <div className="space-y-2">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-3 rounded border-l-4 ${
                alert.severity === 'critical'
                  ? 'bg-red-50 border-red-500'
                  : alert.severity === 'high'
                  ? 'bg-orange-50 border-orange-500'
                  : 'bg-yellow-50 border-yellow-500'
              }`}
            >
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-semibold">{alert.type}</p>
                  <p className="text-sm text-gray-600">
                    {new Date(alert.created_at).toLocaleString()}
                  </p>
                </div>
                {alert.status === 'pending' && (
                  <button
                    onClick={() => handleAcknowledge(alert.id)}
                    className="px-3 py-1 bg-blue-500 text-white rounded text-sm"
                  >
                    Acknowledge
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
```

### Detection Panel Component

**File: `src/components/DetectionPanel.tsx`**

```typescript
import React, { useState, useEffect } from 'react'
import { Detection, detectionService } from '../services/detection'

export const DetectionPanel: React.FC = () => {
  const [detections, setDetections] = useState<Detection[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('all')

  useEffect(() => {
    loadDetections()

    // Subscribe to new detections
    const subscription = detectionService.subscribeToDetections((newDetection) => {
      setDetections((prev) => [newDetection, ...prev])
    })

    return () => {
      subscription?.unsubscribe()
    }
  }, [])

  const loadDetections = async () => {
    try {
      setLoading(true)
      const data = await detectionService.getRecentDetections()
      setDetections(data)
    } catch (error) {
      console.error('Failed to load detections:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredDetections =
    filter === 'all'
      ? detections
      : detections.filter((d) => d.type === filter)

  if (loading) return <div>Loading detections...</div>

  return (
    <div className="detection-panel bg-white rounded-lg shadow-lg p-4">
      <h2 className="text-xl font-bold mb-4">Recent Detections</h2>
      
      <div className="mb-4 flex gap-2">
        {['all', 'vehicle', 'pedestrian', 'obstacle'].map((type) => (
          <button
            key={type}
            onClick={() => setFilter(type)}
            className={`px-3 py-1 rounded ${
              filter === type
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 text-gray-700'
            }`}
          >
            {type.charAt(0).toUpperCase() + type.slice(1)}
          </button>
        ))}
      </div>

      <div className="space-y-2 max-h-96 overflow-y-auto">
        {filteredDetections.map((detection) => (
          <div key={detection.id} className="p-3 bg-gray-50 rounded">
            <div className="flex justify-between items-start">
              <div>
                <p className="font-semibold">{detection.type}</p>
                <p className="text-sm text-gray-600">
                  Confidence: {(detection.confidence * 100).toFixed(1)}%
                </p>
                <p className="text-xs text-gray-500">
                  {new Date(detection.created_at).toLocaleString()}
                </p>
              </div>
              {detection.image_url && (
                <img
                  src={detection.image_url}
                  alt="Detection"
                  className="w-16 h-16 rounded"
                />
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
```

---

## 🔄 Real-time Features

### Subscription Cleanup

```typescript
// Always unsubscribe when component unmounts
useEffect(() => {
  const subscription = supabase
    .from('table_name')
    .on('*', (payload) => {
      console.log('Change received!', payload)
    })
    .subscribe()

  return () => {
    subscription.unsubscribe()
  }
}, [])
```

---

## 📁 Project Structure

```
src/
├── lib/
│   └── supabase.ts          # Supabase client config
├── services/
│   ├── auth.ts              # Authentication service
│   ├── detection.ts         # Detection data operations
│   ├── alerts.ts            # Alert data operations
│   └── hospitals.ts         # Hospital data operations
├── hooks/
│   ├── useAuth.ts           # Authentication hook
│   ├── useDetections.ts     # Detections hook
│   └── useAlerts.ts         # Alerts hook
├── components/
│   ├── AlertTray.tsx        # Alert display
│   ├── DetectionPanel.tsx   # Detection list
│   ├── LiveVideoFeed.tsx    # Video feed
│   └── RealTimeMap.tsx      # Map display
├── App.tsx                  # Main app
└── index.tsx                # Entry point
```

---

## ✅ Best Practices

1. **Type Safety:** Always use TypeScript interfaces
2. **Error Handling:** Wrap operations in try-catch
3. **Loading States:** Show loading indicators
4. **Cleanup:** Unsubscribe from realtime listeners
5. **Security:** Never expose service role key in frontend
6. **Performance:** Use React.memo for expensive components
7. **Caching:** Consider implementing local caching

---

## 🧪 Testing

```typescript
// Example test with Supabase
import { render, screen } from '@testing-library/react'
import { AlertTray } from './AlertTray'

describe('AlertTray', () => {
  it('renders alerts', async () => {
    render(<AlertTray />)
    const title = screen.getByText('Active Alerts')
    expect(title).toBeInTheDocument()
  })
})
```

---

## 📚 Resources

- [Supabase Documentation](https://supabase.com/docs)
- [React Documentation](https://react.dev)
- [TypeScript Handbook](https://www.typescriptlang.org/docs)

---

**Next:** Follow [../DEPLOYMENT-ACTION-PLAN.md](../DEPLOYMENT-ACTION-PLAN.md) to deploy
