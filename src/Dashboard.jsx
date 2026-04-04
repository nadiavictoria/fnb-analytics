import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import FootfallBarChart from './FootfallBarChart';
import CompetitorBarChart from './CompetitorBarChart';
import RentProxyBarChart from './RentProxyBarChart';
import IncomeMixPieChart from './IncomeMixPieChart';
import DemographicPieChart from './DemographicPieChart';
import './Dashboard.css';
import CriteriaSummary from './CriteriaSummary';

// Helper to get unique concepts from the data
const getConcepts = (conceptsObj) => {
  if (!conceptsObj || typeof conceptsObj !== 'object') return [];
  return Object.values(conceptsObj).map(c => c.description);
};

const Dashboard = () => {
  const [concepts, setConcepts] = useState([]);
  const [selectedConcept, setSelectedConcept] = useState('Affordable everyday dining');
  const [rankOptions] = useState([1,2,3,4,5]);
  const [selectedRank, setSelectedRank] = useState(1);
  const [areaDetails, setAreaDetails] = useState(null);
  const [paretoData, setParetoData] = useState(null);
  const [geoJson, setGeoJson] = useState(null);

  useEffect(() => {
    // Fetch pareto_shortlists_updated.json from main directory
    fetch('/pareto_shortlists_updated.json')
      .then(res => res.json())
      .then(data => {
        setParetoData(data);
        setConcepts(getConcepts(data.concepts));
      });
    // Fetch geojson from main directory
    fetch('/SG2019planning_area.geojson')
      .then(res => res.json())
      .then(data => setGeoJson(data));
  }, []);

  useEffect(() => {
    // Find area details for selected concept and rank
    if (!paretoData || !paretoData.concepts) return;
    // Find the concept key by matching description
    const conceptKey = Object.keys(paretoData.concepts).find(
      key => paretoData.concepts[key].description === selectedConcept
    );
    if (!conceptKey) {
      setAreaDetails(null);
      return;
    }
    const areas = paretoData.concepts[conceptKey].areas || [];
    const area = areas.find(a => a.rank === selectedRank);
    setAreaDetails(area || null);
  }, [paretoData, selectedConcept, selectedRank]);

  // Render map with highlighted area
  const renderMap = () => {
    if (!geoJson || !areaDetails) {
      return (
        <div style={{ border: '1px solid #ccc', height: 400, borderRadius: 8, background: '#f9f9f9', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <span>Loading map...</span>
        </div>
      );
    }
    // Find the feature matching the planning_area
    const highlightArea = areaDetails.planning_area;
    const onEachFeature = (feature, layer) => {
      if (feature.properties.PLN_AREA_N === highlightArea) {
        layer.setStyle({ color: 'red', weight: 3, fillOpacity: 0.5 });
      } else {
        layer.setStyle({ color: '#3388ff', weight: 1, fillOpacity: 0.1 });
      }
    };
    return (
      <MapContainer style={{ height: 400, borderRadius: 8 }} center={[1.3521, 103.8198]} zoom={11} scrollWheelZoom={false}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {/* Force GeoJSON to rerender by changing key when highlightArea changes */}
        <GeoJSON key={highlightArea} data={geoJson} onEachFeature={onEachFeature} />
      </MapContainer>
    );
  };

  // Get areas for the selected concept for the bar chart
  let barChartAreas = [];
  if (paretoData && paretoData.concepts) {
    const conceptKey = Object.keys(paretoData.concepts).find(
      key => paretoData.concepts[key].description === selectedConcept
    );
    if (conceptKey) {
      barChartAreas = paretoData.concepts[conceptKey].areas || [];
    }
  }

  return (
    <div className="dashboard-root">
      <div className="dashboard-left">
        <h1 style={{ marginBottom: 8 }}>MakanMetrics</h1>
        <div className="row mb-3">
          <div className="col-md-7 mb-2 mb-md-0">
            <label className="form-label">Concept:</label>
            <select
              value={selectedConcept}
              onChange={e => setSelectedConcept(e.target.value)}
              className="form-select"
            >
              {concepts.map(concept => (
                <option key={concept} value={concept}>{concept}</option>
              ))}
            </select>
          </div>
          <div className="col-md-5">
            <label className="form-label">Rank:</label>
            <select
              value={selectedRank}
              onChange={e => setSelectedRank(Number(e.target.value))}
              className="form-select"
            >
              {rankOptions.map(rank => (
                <option key={rank} value={rank}>{rank}</option>
              ))}
            </select>
          </div>
        </div>
        <div style={{ marginTop: 0, marginBottom: 8 }}>
          <CriteriaSummary areaDetails={areaDetails} />
          <div className="dashboard-pie-row">
            <div className="dashboard-pie-cell">
              <IncomeMixPieChart incomeMix={areaDetails && areaDetails.income_mix} />
            </div>
            <div className="dashboard-pie-cell">
              <DemographicPieChart
                primaryDemographic={areaDetails && areaDetails.primary_demographic}
                primaryShare={areaDetails && areaDetails.primary_demographic_share}
              />
            </div>
          </div>
        </div>
      </div>
      <div
        style={{
          flex: 1,
          minWidth: 320,
          maxWidth: 700,
          width: '100%',
          position: 'relative',
          display: 'flex',
          flexDirection: 'column',
          height: 'auto',
        }}
      >
        <div style={{ flex: 1, minHeight: 300, width: '100%' }}>{renderMap()}</div>
        <div className="dashboard-charts-grid">
          <div className="dashboard-chart-cell">
            <FootfallBarChart areas={barChartAreas} />
          </div>
          <div className="dashboard-chart-cell">
            <CompetitorBarChart areas={barChartAreas} />
          </div>
          <div className="dashboard-chart-cell">
            <RentProxyBarChart areas={barChartAreas} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
