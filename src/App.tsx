import { useMemo, useState } from 'react';
import {
  Activity, ArrowUpRight, Bell, ChevronRight, Crosshair, Database, Download, Filter,
  Gauge, Hospital as HospitalIcon, Layers3, MapPinned, Menu, Plus, RefreshCw, Search,
  Settings2, Siren, SlidersHorizontal, X, Zap,
} from 'lucide-react';
import { EmergencyHeader } from '@/components/EmergencyHeader';
import { HospitalCard } from '@/components/HospitalCard';
import { RealTimeMap } from '@/components/RealTimeMap';
import { TrafficSignalPanel } from '@/components/TrafficSignalPanel';
import { VehicleCard } from '@/components/VehicleCard';
import { DetectionPanel } from '@/components/DetectionPanel';
import { AlertTray } from '@/components/AlertTray';
import { ContactPanel } from '@/components/ContactPanel';
import { DriverView } from '@/components/DriverView';
import { IncidentTimeline } from '@/components/IncidentTimeline';
import { LiveVideoFeed } from '@/components/LiveVideoFeed';
import { useTheme } from '@/hooks/useTheme';
import { useAlertSystem } from '@/hooks/useAlertSystem';
import {
  corridors, getHospitalById, hospitals, rankHospitals, route, signals, vehicles,
  type ContactLog, type Hospital, type Role,
} from '@/data';
import type { DetectionResult } from '@/detection';

function App() {
  const { theme, toggle } = useTheme();
  const [role, setRole] = useState<Role>('operator');
  const [selectedVehicleId, setSelectedVehicleId] = useState(vehicles[0].id);
  const [selectedHospitalId, setSelectedHospitalId] = useState(hospitals[0].id);
  const [showDetection, setShowDetection] = useState(false);
  const [toast, setToast] = useState('');
  const [search, setSearch] = useState('');
  const [soundEnabled, setSoundEnabled] = useState(() => localStorage.getItem('intellicross-sound') !== 'false');
  const [volume] = useState(0.7);
  const [lockedVehicles, setLockedVehicles] = useState<Set<string>>(new Set());
  const [contactLogs, setContactLogs] = useState<ContactLog[]>([]);
  const [sidebarTab, setSidebarTab] = useState<'vehicles' | 'alerts' | 'contact' | 'timeline'>('vehicles');

  const { alerts, barkQueue, acknowledgeAlert, dismissBark, clearAll } = useAlertSystem(soundEnabled, volume);
  const unackCount = alerts.filter((a) => !a.acknowledged).length;

  const selectedVehicle = vehicles.find((v) => v.id === selectedVehicleId) ?? vehicles[0];
  const selectedHospital = hospitals.find((h) => h.id === selectedHospitalId) ?? hospitals[0];
  const rankedHospitals = useMemo(() => rankHospitals(selectedVehicle, hospitals), [selectedVehicle]);
  const visibleHospitals = useMemo(() =>
    hospitals.filter((h) => h.name.toLowerCase().includes(search.toLowerCase()) || h.city.toLowerCase().includes(search.toLowerCase())),
    [search]);

  const notify = (message: string) => { setToast(message); window.setTimeout(() => setToast(''), 3200); };

  const hospitalAction = (action: string, hospital: Hospital) => notify(`${action} request sent to ${hospital.name}`);

  const selectVehicle = (id: string) => {
    setSelectedVehicleId(id);
    const v = vehicles.find((x) => x.id === id);
    if (v) {
      setSelectedHospitalId(v.destinationHospitalId);
      notify(`Tracking ${id} — route to ${v.destination} active`);
    }
  };

  const toggleLockRoute = (id: string) => {
    setLockedVehicles((prev) => {
      const next = new Set(prev);
      if (next.has(id)) { next.delete(id); notify(`Route unlocked for ${id}`); }
      else { next.add(id); notify(`Route locked for ${id} — assignment fixed`); }
      return next;
    });
  };

  const toggleSound = () => {
    const next = !soundEnabled;
    setSoundEnabled(next);
    localStorage.setItem('intellicross-sound', String(next));
    notify(next ? 'Alert sound enabled' : 'Alert sound muted');
  };

  const logContact = (log: ContactLog) => setContactLogs((prev) => [log, ...prev]);

  const vehicleWithLock = (v: typeof vehicles[0]) => ({ ...v, lockedRoute: lockedVehicles.has(v.id) });
  const selectedVehicleWithLock = vehicleWithLock(selectedVehicle);

  // Driver view
  if (role === 'driver') {
    return (
      <div className="app-shell" data-theme={theme}>
        <EmergencyHeader
          alertCount={0} isLive onAlerts={() => {}} theme={theme} onToggleTheme={toggle}
          role={role} onRoleChange={setRole} modelStatus="web_trained_v1" latency={42}
        />
        <main className="driver-main">
          <div className="mobile-toolbar"><button><Menu size={19} /></button><strong>Driver View</strong><button><Bell size={18} /></button></div>
          <DriverView
            vehicle={selectedVehicleWithLock}
            onShareETA={() => notify('ETA shared with hospital dispatch')}
            onRequestGreenWave={() => notify('Green wave requested — signals coordinating')}
          />
          <div className="driver-vehicle-select">
            <label>SELECT VEHICLE</label>
            <div className="driver-vehicle-buttons">
              {vehicles.map((v) => (
                <button key={v.id} className={v.id === selectedVehicleId ? 'active' : ''} onClick={() => selectVehicle(v.id)}>
                  {v.id}
                </button>
              ))}
            </div>
          </div>
        </main>
        {toast && <div className="toast"><span className="toast-check">✓</span>{toast}<button onClick={() => setToast('')}><X size={14} /></button></div>}
      </div>
    );
  }

  // Operator view
  return (
    <div className="app-shell" data-theme={theme}>
      <EmergencyHeader
        alertCount={unackCount} isLive onAlerts={() => setSidebarTab('alerts')}
        theme={theme} onToggleTheme={toggle} role={role} onRoleChange={setRole}
        modelStatus="web_trained_v1" latency={42}
      />
      <aside className="sidebar">
        <div className="sidebar-label">COMMAND CENTER</div>
        <nav>
          <button className={`nav-item ${sidebarTab === 'vehicles' ? 'active' : ''}`} onClick={() => setSidebarTab('vehicles')}><Activity size={17} /> Overview</button>
          <button className={`nav-item ${sidebarTab === 'alerts' ? 'active' : ''}`} onClick={() => setSidebarTab('alerts')}><Siren size={17} /> Emergencies {unackCount > 0 && <b>{unackCount}</b>}</button>
          <button className={`nav-item ${sidebarTab === 'contact' ? 'active' : ''}`} onClick={() => setSidebarTab('contact')}><HospitalIcon size={17} /> Contact</button>
          <button className={`nav-item ${sidebarTab === 'timeline' ? 'active' : ''}`} onClick={() => setSidebarTab('timeline')}><MapPinned size={17} /> Timeline</button>
        </nav>
        <div className="sidebar-label secondary">SYSTEM</div>
        <nav>
          <button className="nav-item"><Database size={17} /> Data &amp; reports</button>
          <button className="nav-item"><Settings2 size={17} /> Settings</button>
        </nav>
        <div className="sidebar-bottom">
          <div className="network-status">
            <span />
            <div><b>All systems operational</b><small>Last sync 12 sec ago</small></div>
          </div>
          <div className="sidebar-version">INTELLICROSS <span>v3.0.0</span></div>
        </div>
      </aside>

      <main className="main-content">
        <div className="mobile-toolbar"><button><Menu size={19} /></button><strong>Overview</strong><button><Bell size={18} /></button></div>

        <div className="page-heading">
          <div>
            <div className="breadcrumb">COMMAND CENTER <ChevronRight size={13} /> OPERATOR OVERVIEW</div>
            <h1>Emergency operations</h1>
            <p>Monitor, coordinate, and route active response units across Delhi NCR.</p>
          </div>
          <div className="heading-actions">
            <button className="secondary-button" onClick={() => notify('Dashboard data refreshed')}><RefreshCw size={15} /> Refresh</button>
            <button className="primary-button" onClick={() => setShowDetection(true)}><Plus size={16} /> New detection</button>
          </div>
        </div>

        <section className="overview-strip">
          <div><span className="strip-icon red"><Siren size={17} /></span><div><label>ACTIVE EMERGENCIES</label><strong>03 <small>+1 today</small></strong></div></div>
          <div><span className="strip-icon orange"><Gauge size={17} /></span><div><label>AVG RESPONSE TIME</label><strong>06:42 <small>min</small></strong></div></div>
          <div><span className="strip-icon blue"><HospitalIcon size={17} /></span><div><label>AVAILABLE BEDS</label><strong>314 <small>across 4 facilities</small></strong></div></div>
          <div><span className="strip-icon green"><Crosshair size={17} /></span><div><label>ROUTE OPTIMIZATION</label><strong>92% <small>accuracy</small></strong></div></div>
          <div className="strip-sync"><span className="live-dot" /> Data streaming <b>•</b> 14 sources</div>
        </section>

        {/* Collapsible side panel area */}
        <div className="content-layout">
          <div className="content-main">
            <div className="section-heading main-section-heading">
              <div>
                <div className="eyebrow"><Siren size={13} /> ACTIVE RESPONSE UNITS</div>
                <h2>Vehicles in the field <span className="count-badge">{vehicles.length}</span></h2>
              </div>
              <div className="heading-tools">
                <button className="icon-button"><Filter size={16} /></button>
                <button className="text-button">View all <ArrowUpRight size={15} /></button>
              </div>
            </div>
            <div className="vehicle-grid">
              {vehicles.map((v) => (
                <VehicleCard
                  key={v.id}
                  vehicle={vehicleWithLock(v)}
                  selected={v.id === selectedVehicleId}
                  onSelect={() => selectVehicle(v.id)}
                  onLockRoute={() => toggleLockRoute(v.id)}
                  onContact={(ch) => notify(`Contact via ${ch} logged for ${v.id}`)}
                />
              ))}
              <button className="add-vehicle-card" onClick={() => setShowDetection(true)}>
                <span><Plus size={19} /></span>
                <strong>Detect a new unit</strong>
                <small>Use AI vision to scan a feed</small>
              </button>
            </div>

            <section className="map-section">
              <div className="section-heading">
                <div>
                  <div className="eyebrow"><MapPinned size={13} /> LIVE GEO-SPATIAL VIEW</div>
                  <h2>Response route <span className="route-tag"><span /> {selectedVehicle.id} → {selectedHospital.name}</span></h2>
                </div>
                <div className="map-tools">
                  <button className="map-tool active"><Layers3 size={15} /> Street</button>
                  <button className="map-tool"><SlidersHorizontal size={15} /> Layers</button>
                  <button className="icon-button"><Download size={16} /></button>
                </div>
              </div>
              <RealTimeMap vehicle={selectedVehicleWithLock} hospital={selectedHospital} signals={signals} corridors={corridors} route={route} theme={theme} />
            </section>

            <TrafficSignalPanel signals={signals} />

            <section className="hospitals-section">
              <div className="section-heading">
                <div>
                  <div className="eyebrow"><HospitalIcon size={13} /> DESTINATION PLANNING</div>
                  <h2>Hospital availability <span className="count-badge blue-badge">{visibleHospitals.length}</span></h2>
                </div>
                <div className="hospital-search">
                  <Search size={15} />
                  <input placeholder="Search hospitals" value={search} onChange={(e) => setSearch(e.target.value)} />
                </div>
              </div>
              <div className="hospital-grid">
                {visibleHospitals.map((hospital, index) => (
                  <div key={hospital.id} onClick={() => setSelectedHospitalId(hospital.id)}>
                    <HospitalCard hospital={hospital} recommended={rankedHospitals[0]?.id === hospital.id && index === 0} vehicle={selectedVehicleWithLock} onAction={hospitalAction} />
                  </div>
                ))}
              </div>
            </section>
          </div>

          <div className="content-side">
            {sidebarTab === 'alerts' && (
              <AlertTray
                alerts={alerts}
                barkQueue={barkQueue}
                soundEnabled={soundEnabled}
                onToggleSound={toggleSound}
                onAcknowledge={acknowledgeAlert}
                onDismissBark={dismissBark}
                onClearAll={clearAll}
                onSelectVehicle={selectVehicle}
              />
            )}
            {sidebarTab === 'contact' && (
              <ContactPanel selectedVehicleId={selectedVehicleId} onLogContact={logContact} contactLogs={contactLogs} />
            )}
            {sidebarTab === 'timeline' && (
              <IncidentTimeline vehicleId={selectedVehicleId} />
            )}
            {sidebarTab === 'vehicles' && (
              <>
                <LiveVideoFeed
                  cameraId={selectedVehicle.corridorId ? `CAM-${selectedVehicle.corridorId.slice(-2)}` : 'CAM-001'}
                  cameraName={corridors.find((c) => c.id === selectedVehicle.corridorId)?.name ?? 'Roadway Camera 01'}
                  vehicleId={selectedVehicle.id}
                />
                <IncidentTimeline vehicleId={selectedVehicleId} />
              </>
            )}
          </div>
        </div>
      </main>

      {showDetection && (
        <DetectionPanel
          onClose={() => setShowDetection(false)}
          onDetect={(result: DetectionResult) => {
            if (result.emergency_detected) {
              notify(`Emergency vehicle detected: ${result.top_class} (${Math.round(result.top_confidence * 100)}% confidence)`);
              setSelectedVehicleId(vehicles[0].id);
            } else {
              notify('Scan complete: no emergency vehicles detected');
            }
          }}
        />
      )}
      {toast && <div className="toast"><span className="toast-check">✓</span>{toast}<button onClick={() => setToast('')}><X size={14} /></button></div>}
    </div>
  );
}

export default App;
