import { useEffect, useMemo, useState } from 'react';
import { fetchCountries, fetchRegions, fetchTopics, fetchSowingMap, fetchPredicate } from '../services/DashboardService';
import type { Country } from '../types/Country';
import type { RegionShape, RegionGeometry } from '../types/Region';
import { TARGET_ZOOM, type CategoryKey } from '../config/globals';
import type { FetchTopicsResponse } from '../types/Topic';
import type { SowingMapResponse } from '../types/SowingMap';
import type { PredicateSuggestion } from '../types/Predicate';

interface Year {
  label: string;
  value: number;
}

interface MapViewState {
  center: [number, number];
  zoom: number;
}

const computeCenter = (geometry: RegionGeometry | null): [number, number] | null => {
  if (!geometry) {
    return null;
  }

  let hasPoint = false;
  let minLat = Infinity;
  let maxLat = -Infinity;
  let minLng = Infinity;
  let maxLng = -Infinity;

  const track = (lng: number, lat: number) => {
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
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
      ring.forEach(([lng, lat]) => track(lng, lat));
    });
  } else {
    geometry.coordinates.forEach((polygon) => {
      polygon.forEach((ring) => {
        ring.forEach(([lng, lat]) => track(lng, lat));
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

const computeBoundingBox = (geometry: RegionGeometry | null): [number, number, number, number] | null => {
  if (!geometry) {
    return null;
  }

  let hasPoint = false;
  let minLat = Infinity;
  let maxLat = -Infinity;
  let minLng = Infinity;
  let maxLng = -Infinity;

  const track = (lng: number, lat: number) => {
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
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
      ring.forEach(([lng, lat]) => track(lng, lat));
    });
  } else {
    geometry.coordinates.forEach((polygon) => {
      polygon.forEach((ring) => {
        ring.forEach(([lng, lat]) => track(lng, lat));
      });
    });
  }

  if (!hasPoint) {
    return null;
  }

  return [minLng, minLat, maxLng, maxLat];
};

export const useDashboard = () => {
  const currentYear = new Date().getFullYear() - 1;
  const years: Year[] = Array.from({ length: 26 }, (_, i) => ({
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
  const [notes, setNotes] = useState<string>('');
  const [mapView, setMapView] = useState<MapViewState | null>(null);
  const [sowingMap, setSowingMap] = useState<SowingMapResponse | null>(null);
  const [selectedCategories, setSelectedCategories] = useState<CategoryKey[]>([]);
  const [topics, setTopics] = useState<FetchTopicsResponse | null>(null);
  const [suggestions, setSuggestions] = useState<PredicateSuggestion[]>([]);
  const [isSuggesting, setIsSuggesting] = useState(false);

  const toggleCategory = (key: CategoryKey) =>
    setSelectedCategories((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key],
    );

  const regions = useMemo(
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
          const uniqueRegions = fetchedRegions.reduce((acc: RegionShape[], current) => {
            const isDuplicate = acc.some(region => region.name_latn === current.name_latn);
            if (!isDuplicate) {
              acc.push(current);
            }
            return acc;
          }, []);

          setRegionsData(uniqueRegions);
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
    let isMounted = true;

    if (!selectedRegion) {
      setMapView(null);
      setSowingMap(null);
      return () => {
        isMounted = false;
      };
    }

    const region = regionsData.find((item) => item.name_latn === selectedRegion);
    const center = computeCenter(region?.geom ?? null);

    if (!center) {
      setMapView(null);
    } else {
      setMapView({ center, zoom: TARGET_ZOOM });
    }

    const bounds = computeBoundingBox(region?.geom ?? null);
    if (!bounds) {
      setSowingMap(null);
      return () => {
        isMounted = false;
      };
    }

    const coordinatesParam = bounds.join(',');
    setSowingMap(null);

    const loadSowingMap = async () => {
      try {
        const data = await fetchSowingMap(coordinatesParam);
        if (isMounted) {
          setSowingMap(data);
        }
      } catch (error) {
        console.error('Failed to load sowing map', error);
        if (isMounted) {
          setSowingMap(null);
        }
      }
    };

    loadSowingMap();

    return () => {
      isMounted = false;
    };
  }, [selectedRegion, regionsData]);

  useEffect(() => {
    let isMounted = true;

    const loadTopics = async () => {
      if (!selectedCountry || !selectedYear) {
        if (isMounted) {
          setTopics(null);
        }
        return;
      }

      try {
        const response = await fetchTopics({
          country: selectedCountry,
          year: selectedYear,
          categories: selectedCategories,
        });
        if (isMounted) {
          setTopics(response);
        }
      } catch (error) {
        console.error('Failed to load topics', error);
        if (isMounted) {
          setTopics(null);
        }
      }
    };

    loadTopics();

    return () => {
      isMounted = false;
    };
  }, [selectedCountry, selectedYear, selectedCategories]);

  const searchCountries = (event: { query: string }) => {
    const query = event.query.toLowerCase();
    setFilteredCountries(
      countryNames.filter((country) => country.toLowerCase().includes(query))
    );
  };

  const handleSuggest = async () => {
    if (!selectedCountry) {
      console.warn('No country selected for predictions');
      return;
    }
    setIsSuggesting(true);
    try {
      const response = await fetchPredicate({
        country: selectedCountry,
        categories: selectedCategories,
        targetYear: selectedYear + 1,
      });
      setSuggestions(response.results);
    } catch (error) {
      console.error('Failed to load predicate suggestions', error);
      setSuggestions([]);
    } finally {
      setIsSuggesting(false);
    }
  };

  return {
    countries,
    regionsData,
    mapView,
    sowingMap,
    topics,
    selectedCountry,
    setSelectedCountry,
    filteredCountries,
    searchCountries,
    selectedRegion,
    setSelectedRegion,
    regions,
    selectedYear,
    setSelectedYear,
    years,
    notes,
    setNotes,
    selectedCategories,
    toggleCategory,
    handleSuggest,
    suggestions,
    isSuggesting,
  };
};

export type UseDashboardReturn = ReturnType<typeof useDashboard>;
export type { MapViewState };
