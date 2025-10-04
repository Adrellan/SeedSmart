import { useEffect, useMemo, useState } from 'react';
import { fetchCountries, fetchRegions } from '../services/DashboardService';
import type { Country } from '../types/Country';
import type { RegionGeometry, RegionShape } from '../types/Region';
import { TARGET_ZOOM } from '../config/globals';

interface Year {
  label: string;
  value: number;
}

interface RegionOption {
  label: string;
  value: string;
}

interface MapViewState {
  center: [number, number];
  zoom: number;
}

const extractCenterFromGeometry = (geometry: RegionGeometry | null): [number, number] | null => {
  if (!geometry) {
    return null;
  }

  let minLat = Number.POSITIVE_INFINITY;
  let minLng = Number.POSITIVE_INFINITY;
  let maxLat = Number.NEGATIVE_INFINITY;
  let maxLng = Number.NEGATIVE_INFINITY;
  let hasPoint = false;

  const trackPoint = (lng: number, lat: number) => {
    if (Number.isNaN(lat) || Number.isNaN(lng)) {
      return;
    }
    hasPoint = true;
    if (lat < minLat) minLat = lat;
    if (lat > maxLat) maxLat = lat;
    if (lng < minLng) minLng = lng;
    if (lng > maxLng) maxLng = lng;
  };

  if (geometry.type === 'Polygon') {
    geometry.coordinates.forEach((ring) => {
      ring.forEach(([lng, lat]) => trackPoint(lng, lat));
    });
  } else if (geometry.type === 'MultiPolygon') {
    geometry.coordinates.forEach((polygon) => {
      polygon.forEach((ring) => {
        ring.forEach(([lng, lat]) => trackPoint(lng, lat));
      });
    });
  }

  if (!hasPoint) {
    return null;
  }

  const centerLat = (minLat + maxLat) / 2;
  const centerLng = (minLng + maxLng) / 2;
  return [centerLat, centerLng];
};

export const useDashboard = () => {
  const currentYear = new Date().getFullYear();
  const years: Year[] = Array.from({ length: 11 }, (_, i) => ({
    label: (currentYear + 1 - i).toString(),
    value: currentYear + 1 - i,
  }));

  const [countries, setCountries] = useState<Country[]>([]);
  const [countryNames, setCountryNames] = useState<string[]>([]);
  const [regionsData, setRegionsData] = useState<RegionShape[]>([]);
  const [selectedCountry, setSelectedCountry] = useState<string>('');
  const [filteredCountries, setFilteredCountries] = useState<string[]>([]);
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null);
  const [selectedYear, setSelectedYear] = useState<number>(currentYear);
  const [mapView, setMapView] = useState<MapViewState | null>(null);

  const regions: RegionOption[] = useMemo(
    () => regionsData.map((region) => ({ label: region.name_latn, value: region.name_latn })),
    [regionsData]
  );

  useEffect(() => {
    let isMounted = true;

    const loadCountries = async () => {
      try {
        const countryList = await fetchCountries();
        if (isMounted) {
          setCountries(countryList);
          const names = countryList.map((country) => country.name);
          setCountryNames(names);
          setFilteredCountries(names);
        }
      } catch (error) {
        console.error('Failed to load countries', error);
      }
    };

    loadCountries();

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    let isMounted = true;

    if (!selectedCountry) {
      setSelectedRegion(null);
      setRegionsData([]);
      setMapView(null);
      return () => {
        isMounted = false;
      };
    }

    const matchedCountry = countries.find((country) => country.name === selectedCountry);
    if (!matchedCountry) {
      setSelectedRegion(null);
      setRegionsData([]);
      setMapView(null);
      return () => {
        isMounted = false;
      };
    }

    setSelectedRegion(null);
    setMapView(null);

    const loadRegions = async () => {
      try {
        const fetchedRegions = await fetchRegions(matchedCountry.cntr_code);
        if (isMounted) {
          setRegionsData(fetchedRegions);
        }
      } catch (error) {
        console.error('Failed to load regions', error);
        if (isMounted) {
          setRegionsData([]);
        }
      }
    };

    loadRegions();

    return () => {
      isMounted = false;
    };
  }, [selectedCountry, countries]);

  useEffect(() => {
    if (!selectedRegion) {
      setMapView(null);
      return;
    }

    const region = regionsData.find((item) => item.name_latn === selectedRegion);
    if (!region) {
      setMapView(null);
      return;
    }

    const center = extractCenterFromGeometry(region.geom);
    if (center) {
      setMapView({ center, zoom: TARGET_ZOOM });
    } else {
      setMapView(null);
    }
  }, [selectedRegion, regionsData]);

  const searchCountries = (event: { query: string }) => {
    const query = event.query.toLowerCase();
    setFilteredCountries(
      countryNames.filter((country) => country.toLowerCase().includes(query)),
    );
  };

  const handleSuggest = () => {
    console.log({
      country: selectedCountry,
      region: selectedRegion,
      year: selectedYear,
      regionsData,
      mapView,
    });
  };

  return {
    countries,
    regionsData,
    regions,
    mapView,
    selectedCountry,
    setSelectedCountry,
    filteredCountries,
    searchCountries,
    selectedRegion,
    setSelectedRegion,
    selectedYear,
    setSelectedYear,
    years,
    handleSuggest,
  };
};

export type UseDashboardReturn = ReturnType<typeof useDashboard>;
export type { RegionOption, MapViewState };
