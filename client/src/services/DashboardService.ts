import axios, { type AxiosError } from 'axios';
import { API_URL } from '../constant';
import type { Country } from '../types/Country';
import type { RegionShape } from '../types/Region';
import type { FetchTopicsParams, FetchTopicsResponse } from '../types/Topic';

const normalizeCountryName = (value: string): string => {
  const trimmed = value.trim();
  if (!trimmed) {
    return trimmed;
  }
  return trimmed[0].toUpperCase() + trimmed.slice(1);
};

export const fetchCountries = async (): Promise<Country[]> => {
  const { data } = await axios.get<Country[]>(`${API_URL}/api/dashboard/countries`);
  if (!Array.isArray(data)) {
    throw new Error('Unexpected countries response payload');
  }
  return data.map((country) => ({
    id: country.id,
    name: country.name,
    cntr_code: country.cntr_code,
  }));
};

export const fetchRegions = async (cntrCode: string): Promise<RegionShape[]> => {
  const trimmedCode = cntrCode.trim();
  if (!trimmedCode) {
    return [];
  }

  const { data } = await axios.get<RegionShape[]>(`${API_URL}/api/dashboard/regions`, {
    params: { cntr_code: trimmedCode },
  });
  if (!Array.isArray(data)) {
    throw new Error('Unexpected regions response payload');
  }
  return data.map((region) => ({
    name_latn: region.name_latn,
    geom: region.geom,
  }));
};

export const fetchTopics = async (
  params: FetchTopicsParams,
): Promise<FetchTopicsResponse> => {
  const { country, year, categories } = params;
  if (!country || Number.isNaN(year)) {
    throw new Error('country and year are required for fetchTopics');
  }

  const query: Record<string, string | number> = {
    country: normalizeCountryName(country),
    year,
  };

  if (categories && categories.length > 0) {
    query.category_label = categories.join(',');
  }

  try {
    const { data } = await axios.get<FetchTopicsResponse>(`${API_URL}/api/dashboard/topic`, {
      params: query,
    });
    return data;
  } catch (error) {
    const axiosError = error as AxiosError<FetchTopicsResponse>;
    if (axiosError.response && axiosError.response.status === 404 && axiosError.response.data) {
      return axiosError.response.data;
    }
    throw error;
  }
};
