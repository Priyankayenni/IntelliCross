import { useCallback, useEffect, useRef, useState } from 'react';
import { initialAlerts, vehicles, type AlertItem, type AlertSeverity } from '@/data';

const BARK_SOUNDS: Record<AlertSeverity, number> = {
  critical: 880,
  warning: 660,
  info: 440,
};

export function useAlertSystem(soundEnabled: boolean, volume: number) {
  const [alerts, setAlerts] = useState<AlertItem[]>(initialAlerts);
  const [barkQueue, setBarkQueue] = useState<AlertItem[]>([]);
  const audioCtxRef = useRef<AudioContext | null>(null);

  const playBark = useCallback((severity: AlertSeverity) => {
    if (!soundEnabled) return;
    try {
      if (!audioCtxRef.current) {
        audioCtxRef.current = new AudioContext();
      }
      const ctx = audioCtxRef.current;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.value = BARK_SOUNDS[severity];
      osc.type = 'square';
      gain.gain.setValueAtTime(volume * 0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
      osc.start();
      osc.stop(ctx.currentTime + 0.3);
    } catch {
      // Audio not available
    }
  }, [soundEnabled, volume]);

  const addAlert = useCallback((alert: AlertItem) => {
    setAlerts((prev) => [alert, ...prev]);
    setBarkQueue((prev) => [...prev, alert]);
    playBark(alert.severity);
  }, [playBark]);

  const acknowledgeAlert = useCallback((id: string) => {
    setAlerts((prev) => prev.map((a) => a.id === id ? { ...a, acknowledged: true } : a));
  }, []);

  const dismissBark = useCallback((id: string) => {
    setBarkQueue((prev) => prev.filter((a) => a.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setAlerts((prev) => prev.map((a) => ({ ...a, acknowledged: true })));
    setBarkQueue([]);
  }, []);

  // Simulate periodic incoming alerts
  useEffect(() => {
    const interval = setInterval(() => {
      const vehicle = vehicles[Math.floor(Math.random() * vehicles.length)];
      const severities: AlertSeverity[] = ['critical', 'warning', 'info'];
      const severity = severities[Math.floor(Math.random() * severities.length)];
      const alert: AlertItem = {
        id: `al-${Date.now()}`,
        vehicleId: vehicle.id,
        vehicleType: vehicle.type,
        severity,
        message: `${vehicle.type.charAt(0).toUpperCase() + vehicle.type.slice(1)} ${vehicle.id} status update — corridor ${vehicle.corridorId ?? 'unmonitored'}`,
        location: vehicle.location,
        heading: vehicle.heading,
        confidence: vehicle.confidence,
        nearestHospital: vehicle.destination,
        eta: vehicle.eta,
        timestamp: Date.now(),
        acknowledged: false,
      };
      addAlert(alert);
    }, 45000);
    return () => clearInterval(interval);
  }, [addAlert]);

  return { alerts, barkQueue, addAlert, acknowledgeAlert, dismissBark, clearAll, playBark };
}
