import React from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';

// FONTOS: A CSS importok sorrendje számít!
import 'leaflet/dist/leaflet.css';
import 'primereact/resources/themes/lara-light-blue/theme.css';
import 'primereact/resources/primereact.min.css';
import 'primeicons/primeicons.css';
import 'primeflex/primeflex.css';
import Dashboard from '../components/Dashboard';
import { useDashboard, type MapViewState } from '../hooks/useDashboard';

// Fix Leaflet default marker icon issue
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const RegionFlyTo: React.FC<{ mapView: MapViewState | null }> = ({ mapView }) => {
  const map = useMap();

  React.useEffect(() => {
    if (!mapView) {
      return;
    }

    map.flyTo(mapView.center, mapView.zoom, { duration: 1.2 });
  }, [mapView, map]);

  return null;
};

const HomePage: React.FC = () => {
  const dashboardState = useDashboard();

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100%' }}>
      <Dashboard state={dashboardState} />

      <div style={{ flex: 1, position: 'relative' }}>
        <MapContainer
          center={[46.5, 2.5]}
          zoom={6}
          style={{ height: '100%', width: '100%', position: 'absolute', top: 0, left: 0 }}
          scrollWheelZoom
        >
          <TileLayer
            attribution="&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors"
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <RegionFlyTo mapView={dashboardState.mapView} />
        </MapContainer>
      </div>
    </div>
  );
};

export default HomePage;
