import React from 'react';
import { GeoJSON, MapContainer, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';

// FONTOS: A CSS importok sorrendje számít!
import 'leaflet/dist/leaflet.css';
import 'primereact/resources/themes/lara-light-blue/theme.css';
import 'primereact/resources/primereact.min.css';
import 'primeicons/primeicons.css';
import 'primeflex/primeflex.css';
import Dashboard from '../components/Dashboard';
import { useDashboard, type MapViewState } from '../hooks/useDashboard';
import { CROP_GROUP_COLORS, DEFAULT_CROP_COLOR, type CategoryKey } from '../config/globals';
import type { FeatureCollection, Geometry, Feature } from 'geojson';
import Legend from '../components/Legend';

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
  const { mapView, sowingMap, selectedRegion, selectedCategories } = dashboardState;

  const sowingGeoJson = React.useMemo<FeatureCollection<Geometry, { crop_group?: string | null }> | null>(() => {
    if (!sowingMap || !Array.isArray(sowingMap.features) || sowingMap.features.length === 0) {
      return null;
    }

    const activeCategories = selectedCategories.length > 0 ? new Set<CategoryKey>(selectedCategories) : null;

    const filtered = sowingMap.features.filter((feature) => {
      if (!activeCategories) {
        return true;
      }
      const group = feature.crop_group ?? (feature.properties?.crop_group as string | null | undefined);
      if (!group) {
        return false;
      }
      return activeCategories.has(group as CategoryKey);
    });

    if (filtered.length === 0) {
      return null;
    }

    return {
      type: 'FeatureCollection',
      features: filtered.map((feature, index) => ({
        type: 'Feature',
        id: index,
        properties: {
          crop_group: feature.crop_group ?? (feature.properties?.crop_group as string | null | undefined) ?? null,
          ...(feature.properties ?? {}),
        },
        geometry: feature.geometry as Geometry,
      })),
    };
  }, [sowingMap, selectedCategories]);

  const cropStyle = React.useCallback((feature: Feature<Geometry, { crop_group?: string | null }>) => {
    const group = feature?.properties?.crop_group ?? null;
    const color = (group && CROP_GROUP_COLORS[group as CategoryKey]) ?? DEFAULT_CROP_COLOR;

    return {
      color,
      weight: 1,
      fillColor: color,
      fillOpacity: 0.35,
    };
  }, []);

  const sowingLayerKey = React.useMemo(() => {
    if (!sowingMap) {
      return 'sowing-none';
    }
    const categoriesKey = selectedCategories.length ? selectedCategories.slice().sort().join('|') : 'all';
    const base = `${sowingMap.count}-${categoriesKey}`;
    return selectedRegion ? `${selectedRegion}-${base}` : base;
  }, [sowingMap, selectedRegion, selectedCategories]);

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
          <RegionFlyTo mapView={mapView} />
          {sowingGeoJson && (
            <GeoJSON key={sowingLayerKey} data={sowingGeoJson} style={cropStyle} />
          )}
        </MapContainer>
        <Legend position="top-right" shape="square" title="Technology categories" />
      </div>
    </div>
  );
};

export default HomePage;
