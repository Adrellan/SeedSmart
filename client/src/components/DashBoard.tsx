import React from 'react';
import { AutoComplete } from 'primereact/autocomplete';
import { Dropdown } from 'primereact/dropdown';
import { InputTextarea } from 'primereact/inputtextarea';
import { Button } from 'primereact/button';
import { useDashboard } from '../hooks/useDashboard';

const Dashboard: React.FC = () => {
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
    notes,
    setNotes,
    handleSuggest
  } = useDashboard();

  return (
    <div className="w-80 bg-white border-r border-gray-200 p-6 flex flex-col">
      <h1 className="text-3xl font-bold mb-8 text-gray-800">SeedSmart</h1>
      
      {/* Country Search */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2 text-gray-700">
          Country
        </label>
        <AutoComplete
          value={selectedCountry}
          suggestions={filteredCountries}
          completeMethod={searchCountries}
          onChange={(e) => setSelectedCountry(e.value)}
          placeholder="Keresés országra..."
          className="w-full"
        />
      </div>

      {/* Region Dropdown */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2 text-gray-700">
          Region
        </label>
        <Dropdown
          value={selectedRegion}
          onChange={(e) => setSelectedRegion(e.value)}
          options={regions}
          placeholder="Válassz régiót..."
          className="w-full"
        />
      </div>

      {/* Year Dropdown */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2 text-gray-700">
          Year
        </label>
        <Dropdown
          value={selectedYear}
          onChange={(e) => setSelectedYear(e.value)}
          options={years}
          placeholder="Válassz évet..."
          className="w-full"
        />
      </div>

      {/* Suggest Section */}
      <div className="mt-auto">
        <Button 
          label="Suggest" 
          className="w-full mb-4" 
          severity="info"
          onClick={handleSuggest}
        />
        <InputTextarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="lorem ipsum"
          rows={6}
          className="w-full"
        />
      </div>
    </div>
  );
};

export default Dashboard;