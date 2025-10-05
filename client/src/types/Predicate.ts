export interface PredicateSuggestion {
  product: string;
  category_key: string;
  'Soil Type'?: string;
  year: number;
  country: string;
  'Humidity(%)': number;
  'Moisture(%)': number;
  'Nitrogen(mg/Kg)': number;
  'Potassium(mg/Kg)': number;
  'Phosphorous(mg/Kg)': number;
  predicted_profit_margin: number;
}

export interface PredicateResponse {
  results: PredicateSuggestion[];
}
