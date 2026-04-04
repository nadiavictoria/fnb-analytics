import React, { useEffect, useMemo, useState } from 'react';
import { GeoJSON, MapContainer, TileLayer } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import AudienceBars from './AudienceBars';
import CriteriaSummary from './CriteriaSummary';
import DecisionHero from './DecisionHero';
import OpportunityBubbleChart from './OpportunityBubbleChart';
import ShortlistList from './ShortlistList';
import TradeoffMatrix from './TradeoffMatrix';
import './Dashboard.css';
import { getAudienceRows } from './insights';

const getConcepts = (conceptsObj) => {
  if (!conceptsObj || typeof conceptsObj !== 'object') return [];
  return Object.entries(conceptsObj).map(([key, value]) => ({
    key,
    description: value.description,
    areas: value.areas || [],
  }));
};

const fetchJsonWithFallback = async (paths) => {
  for (const path of paths) {
    try {
      const response = await fetch(path);
      if (!response.ok) continue;
      const text = await response.text();
      if (!text.trim()) continue;
      return JSON.parse(text);
    } catch {
      // Try the next path.
    }
  }
  throw new Error('Unable to load dashboard data.');
};

const Dashboard = () => {
  const [concepts, setConcepts] = useState([]);
  const [selectedConceptKey, setSelectedConceptKey] = useState('');
  const [selectedAreaName, setSelectedAreaName] = useState('');
  const [paretoData, setParetoData] = useState(null);
  const [geoJson, setGeoJson] = useState(null);
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        const [data, geo] = await Promise.all([
          fetchJsonWithFallback([
            '/data/pareto_shortlists_updated.json',
          ]),
          fetchJsonWithFallback([
            '/data/SG2019planning_area.geojson',
          ]),
        ]);

        const conceptItems = getConcepts(data.concepts);
        setParetoData(data);
        setGeoJson(geo);
        setConcepts(conceptItems);

        if (conceptItems.length > 0) {
          setSelectedConceptKey(conceptItems[0].key);
        }
      } catch {
        setLoadError('Unable to load dashboard data.');
      }
    };

    loadDashboard();
  }, []);

  const selectedConcept = useMemo(
    () => paretoData?.concepts?.[selectedConceptKey] || null,
    [paretoData, selectedConceptKey],
  );

  const shortlistAreas = useMemo(() => selectedConcept?.areas || [], [selectedConcept]);
  const maximizeKeys = selectedConcept?.maximize || [];
  const minimizeKeys = selectedConcept?.minimize || [];
  const areaDetails = useMemo(
    () =>
      shortlistAreas.find((area) => area.planning_area === selectedAreaName) ||
      shortlistAreas[0] ||
      null,
    [selectedAreaName, shortlistAreas],
  );

  const handleConceptChange = (event) => {
    setSelectedConceptKey(event.target.value);
    setSelectedAreaName('');
  };

  const handleAreaSelect = (area) => {
    setSelectedAreaName(area.planning_area);
  };

  const renderMap = () => {
    if (loadError) {
      return <div className="dashboard-map-state">{loadError}</div>;
    }

    if (!geoJson || !areaDetails) {
      return <div className="dashboard-map-state">Loading map...</div>;
    }

    const highlightArea = areaDetails.planning_area;
    const rankedAreas = new Map(
      shortlistAreas.map((area) => [area.planning_area, area.rank]),
    );

    const onEachFeature = (feature, layer) => {
      const featureArea = feature.properties.PLN_AREA_N;
      const shortlistRank = rankedAreas.get(featureArea);

      if (featureArea === highlightArea) {
        layer.setStyle({
          color: '#b45309',
          weight: 3,
          fillColor: '#f59e0b',
          fillOpacity: 0.7,
        });
      } else if (shortlistRank) {
        const fillOpacity = Math.max(0.2, 0.5 - (shortlistRank - 2) * 0.08);
        layer.setStyle({
          color: '#b45309',
          weight: 1.75,
          fillColor: '#fbbf24',
          fillOpacity,
        });
      } else {
        layer.setStyle({
          color: '#6b7280',
          weight: 1,
          fillColor: '#d1d5db',
          fillOpacity: 0.12,
        });
      }
    };

    return (
      <MapContainer
        center={[1.3521, 103.8198]}
        className="dashboard-map"
        scrollWheelZoom={false}
        zoom={11}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <GeoJSON key={highlightArea} data={geoJson} onEachFeature={onEachFeature} />
      </MapContainer>
    );
  };

  const audienceRows = getAudienceRows(areaDetails?.income_mix);
  const activeSelectedAreaName =
    areaDetails?.planning_area || selectedAreaName || shortlistAreas[0]?.planning_area || '';
  const demographicRows = Array.isArray(areaDetails?.demographic_breakdown)
    ? areaDetails.demographic_breakdown.map((row, index) => ({
        key: row.key || `segment-${index}`,
        label: row.label || `Segment ${index + 1}`,
        share: row.share,
        color: ['#1d4ed8', '#2563eb', '#0f766e', '#38bdf8', '#64748b', '#94a3b8'][index] || '#94a3b8',
      }))
    : [];

  return (
    <div className="dashboard-root">
      <div className="dashboard-left">
        <div className="dashboard-left-sticky">
          <div className="dashboard-heading">
            <h1>MakanMetrics</h1>
            <p>
              Compare shortlisted planning areas by fit, market environment, and
              concept-specific strengths.
            </p>
          </div>

          <div className="dashboard-card dashboard-controls">
            <div className="dashboard-concept-focus">
              <label className="form-label dashboard-focus-label">Select Concept:</label>
              <select
                className="form-select dashboard-concept-select"
                onChange={handleConceptChange}
                value={selectedConceptKey}
              >
                {concepts.map((concept) => (
                  <option key={concept.key} value={concept.key}>
                    {concept.description}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <ShortlistList
            areas={shortlistAreas}
            onSelectArea={handleAreaSelect}
            selectedAreaName={activeSelectedAreaName}
          />
        </div>
      </div>

      <div className="dashboard-right">
        <DecisionHero
          areaDetails={areaDetails}
          areas={shortlistAreas}
          selectedConcept={selectedConcept}
        />

        <div className="dashboard-map-card">
          <div className="dashboard-section-head">
            <div>
              <h2>Shortlist On Map</h2>
              <p>The active area is darkest, and the rest of the shortlist stays visible for geographic context.</p>
            </div>
          </div>
          {renderMap()}
          <div className="map-legend">
            <span><i className="legend-swatch legend-selected" /> Selected area</span>
            <span><i className="legend-swatch legend-shortlist" /> Other shortlisted areas</span>
            <span><i className="legend-swatch legend-background" /> Other planning areas</span>
          </div>
        </div>

        <CriteriaSummary
          areaDetails={areaDetails}
          areas={shortlistAreas}
          conceptDescription={selectedConcept?.description}
          maximize={maximizeKeys}
          minimize={minimizeKeys}
        />

        <TradeoffMatrix
          areas={shortlistAreas}
          selectedAreaName={activeSelectedAreaName}
          maximize={maximizeKeys}
          minimize={minimizeKeys}
        />

        <div className="dashboard-charts-section">
          <div className="dashboard-section-head">
            <div>
              <h2>Decision Lenses</h2>
              <p>Use these views to compare tradeoffs, audience fit, and cost-pressure without scanning many separate charts.</p>
            </div>
          </div>

          <div className="dashboard-lenses-grid">
            <OpportunityBubbleChart
              areas={shortlistAreas}
              selectedAreaName={activeSelectedAreaName}
            />
            <AudienceBars
              title="Income Mix"
              subtitle="Bar lengths make the area’s household composition easier to compare than a pie."
              rows={audienceRows}
            />
            <AudienceBars
              title="Demographic Mix"
              subtitle="Audience shares shown as bars so the dominant segments stand out immediately."
              rows={demographicRows}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
