import React, { useMemo, useState } from "react";
import { AutoComplete } from "primereact/autocomplete";
import { Dropdown } from "primereact/dropdown";
import { Button } from "primereact/button";
import { Checkbox } from "primereact/checkbox";
import { type CategoryKey, CATEGORY_OPTIONS } from "../config/globals";
import type { UseDashboardReturn } from "../hooks/useDashboard";
import "./Dashboard.css";

interface DashboardProps {
  state: UseDashboardReturn;
}

const Dashboard: React.FC<DashboardProps> = ({ state }) => {
  const {
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
    handleSuggest,
  } = state;

  const [selectedCategories, setSelectedCategories] = useState<CategoryKey[]>([]);
  const toggleCategory = (key: CategoryKey) =>
    setSelectedCategories((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key],
    );

  const payload = useMemo(
    () => ({
      country: selectedCountry,
      region: selectedRegion,
      year: selectedYear,
      categories: selectedCategories,
    }),
    [selectedCountry, selectedRegion, selectedYear, selectedCategories],
  );

  const onSuggest = () => {
    handleSuggest();
  };

  return (
    <div className="dashboard-container">
      {/* Header */}
      <div className="dashboard-header">
        <h1 className="dashboard-title">SeedSmart</h1>
        <p className="dashboard-subtitle">Intelligent seed analyzer</p>
      </div>

      <div className="dashboard-content">
        <div className="dashboard-field">
          <label className="dashboard-label">
            <i className="pi pi-map-marker"></i>
            Country
          </label>
          <AutoComplete
            value={selectedCountry}
            suggestions={filteredCountries}
            completeMethod={searchCountries}
            onChange={(e) => setSelectedCountry(e.value)}
            placeholder="Select a country..."
            className="w-full"
          />
        </div>

        <div className="dashboard-field">
          <label className="dashboard-label">
            <i className="pi pi-globe"></i>
            Region
          </label>
          <Dropdown
            value={selectedRegion}
            onChange={(e) => setSelectedRegion(e.value)}
            options={regions}
            optionLabel="label"
            optionValue="value"
            placeholder="Select a region..."
            className="w-full"
            disabled={regions.length === 0}
          />
        </div>

        <div className="dashboard-field">
          <label className="dashboard-label">
            <i className="pi pi-calendar"></i>
            Year
          </label>
          <Dropdown
            value={selectedYear}
            onChange={(e) => setSelectedYear(e.value)}
            options={years}
            placeholder="Select a year..."
            className="w-full"
          />
        </div>

        <div className="two-col">
          <div className="dashboard-field">
            <label className="dashboard-label">
              <i className="pi pi-sliders-h"></i>
              Technology categories
            </label>

            <div className="category-grid">
              {CATEGORY_OPTIONS.map(({ key, label }) => {
                const checkboxId = `cat-${key}`;
                return (
                  <div key={key} className="category-item">
                    <Checkbox
                      inputId={checkboxId}
                      onChange={() => toggleCategory(key)}
                      checked={selectedCategories.includes(key)}
                      style={{ marginTop: "10px", marginRight: "5px" }}
                    />
                    <label htmlFor={checkboxId} className="category-label">
                      {label}
                    </label>
                  </div>
                );
              })}
            </div>
          </div>

          {/* <div className="dashboard-field">
            <label className="dashboard-label">
              <i className="pi pi-comment"></i>
              Notes
            </label>
            <InputTextarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Write notes..."
              rows={10}
              className="w-full"
              autoResize
            />
          </div> */}
        </div>
      </div>

      <div className="dashboard-footer">
        <Button
          label="Get suggestion"
          className="w-full dashboard-button"
          onClick={onSuggest}
        />
      </div>
    </div>
  );
};

export default Dashboard;
