export type FetchTopicsParams = {
  country: string;
  year: number;
  categories?: string[];
};

export type TopicRecord = {
  year: number;
  country: string;
  geo: string;
  category_key: string;
  category_label: string;
  product: string;
  prod_code: string;
  price_eur_tonne: number;
};

export type TopicResult = {
  requested_category: string | null;
  found: boolean;
  record: TopicRecord | null;
};

export type FetchTopicsResponse = {
  found: boolean;
  country: string;
  year: number;
  requested_categories: string[] | null;
  results?: TopicResult[];
  record?: TopicRecord | null;
};
