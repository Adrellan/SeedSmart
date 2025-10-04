import axios from 'axios';
import { API_URL } from '../constant';
import type { Country } from '../types/Country';
import type { RegionShape } from '../types/Region';

export const fetchCountries = async (): Promise<Country[]> => {
  const { data } = await axios.get<Country[]>(`${API_URL}/api/dashboard/countries`);
  if (!Array.isArray(data)) {
    throw new Error('Unexpected countries response payload');
  }
  return data.map((country) => ({
    id: country.id,
    name: country.name,
    cntr_code: country.cntr_code
  }));
};

export const fetchRegions = async (cntrCode: string): Promise<RegionShape[]> => {
  const trimmedCode = cntrCode.trim();
  if (!trimmedCode) {
    return [];
  }

  const { data } = await axios.get<RegionShape[]>(`${API_URL}/api/dashboard/regions`, {
    params: { cntr_code: trimmedCode }
  });
  if (!Array.isArray(data)) {
    throw new Error('Unexpected regions response payload');
  }
  return data.map((region) => ({
    name_latn: region.name_latn,
    geom: region.geom
  }));
};