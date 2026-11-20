import { useEffect, useRef, useState } from 'react'

const WS_URL = import.meta.env.VITE_WS_URL || (
  import.meta.env.VITE_API_URL
    ? import.meta.env.VITE_API_URL.replace(/\/+$/, '').replace(/^http(s?):/, 'ws$1:') + '/ws/telemetry'
    : 'ws://localhost:8000/ws/telemetry'
)

/**
 * Subscribes to the backend's live telemetry stream and keeps the most
 * recent IntersectionStatus in state. Auto-reconnects with backoff if
 * the backend restarts (which happens a lot during development).
 */
export function useTelemetry() {
  const [status, setStatus] = useState(null)
  const [connected, setConnected] = useState(false)
  const [history, setHistory] = useState([]) // last N snapshots, for the density sparkline
  const retryDelay = useRef(1000)

  useEffect(() => {
    let ws
    let cancelled = false
    let retryTimeout

    const connect = () => {
      ws = new WebSocket(WS_URL)

      ws.onopen = () => {
        setConnected(true)
        retryDelay.current = 1000
      }

      ws.onmessage = (event) => {
        const parsed = JSON.parse(event.data)
        setStatus(parsed)
        setHistory((prev) => {
          const next = [...prev, parsed]
          return next.length > 40 ? next.slice(next.length - 40) : next
        })
      }

      ws.onclose = () => {
        setConnected(false)
        if (cancelled) return
        retryTimeout = setTimeout(connect, retryDelay.current)
        retryDelay.current = Math.min(retryDelay.current * 1.5, 10000)
      }

      ws.onerror = () => {
        ws.close()
      }
    }

    connect()

    return () => {
      cancelled = true
      clearTimeout(retryTimeout)
      ws && ws.close()
    }
  }, [])

  return { status, connected, history }
}
