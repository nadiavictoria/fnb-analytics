import React, { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import FootfallBarChart from './FootfallBarChart';
import CompetitorBarChart from './CompetitorBarChart';
import RentProxyBarChart from './RentProxyBarChart';
import IncomeMixPieChart from './IncomeMixPieChart';
import DemographicPieChart from './DemographicPieChart';
import './Dashboard.css';
import CriteriaSummary from './CriteriaSummary';

const SINGAPORE_BOUNDS = L.latLngBounds([1.1304, 103.6020], [1.4784, 104.0850]);

// Fits the map to Singapore on mount and locks minZoom to that level
function SingaporeFit() {
  const map = useMap();
  useEffect(() => {
    map.fitBounds(SINGAPORE_BOUNDS, { padding: [8, 8] });
    map.once('moveend', () => {
      map.setMinZoom(map.getZoom());
    });
  }, [map]);
  return null;
}

const LOCK_ZOOM = 11;

// Ports the same map interaction logic from pareto_map_updated.html
function MapController({ geoJson, highlightArea }) {
  const map = useMap();
  const geoJsonLayerRef = useRef(null);
  const tooltipRef = useRef(null);
  const isDraggingRef = useRef(false);
  const isClickingRef = useRef(false);

  useEffect(() => {
    if (!tooltipRef.current) {
      tooltipRef.current = L.tooltip({ permanent: false, direction: 'top', offset: [0, -4] });
    }

    const onDragStart   = () => { isDraggingRef.current = true; };
    const onDragEnd     = () => { isDraggingRef.current = false; };
    const onMouseDown   = () => { isClickingRef.current = true; };
    const onMouseUp     = () => { isClickingRef.current = false; };
    const onZoomEnd   = () => {
      if (map.getZoom() > LOCK_ZOOM) {
        map.dragging.enable();
      } else {
        map.dragging.disable();
        tooltipRef.current.remove();
      }
    };

    map.on('dragstart',  onDragStart);
    map.on('dragend',    onDragEnd);
    map.on('zoomend',    onZoomEnd);
    map.on('mousedown',  onMouseDown);
    map.on('mouseup',    onMouseUp);

    return () => {
      map.off('dragstart',  onDragStart);
      map.off('dragend',    onDragEnd);
      map.off('zoomend',    onZoomEnd);
      map.off('mousedown',  onMouseDown);
      map.off('mouseup',    onMouseUp);
    };
  }, [map]);

  useEffect(() => {
    if (!geoJson) return;

    if (geoJsonLayerRef.current) {
      geoJsonLayerRef.current.remove();
    }

    geoJsonLayerRef.current = L.geoJSON(geoJson, {
      style: (feature) => {
        const isSelected = feature.properties.PLN_AREA_N === highlightArea;
        return isSelected
          ? { color: 'red', weight: 3, fillOpacity: 0.5 }
          : { color: '#3388ff', weight: 1, fillOpacity: 0.1 };
      },
      onEachFeature: (feature, layer) => {
        const areaName = feature.properties.PLN_AREA_N;
        const content = `<strong>${areaName}</strong>`;
        layer.on('mouseover', (e) => {
          tooltipRef.current.setContent(content).setLatLng(e.latlng).addTo(map);
        });
        layer.on('mousemove', (e) => {
          tooltipRef.current.setLatLng(e.latlng);
        });
        layer.on('mouseout', () => {
          if (!isDraggingRef.current && !isClickingRef.current) tooltipRef.current.remove();
        });
      },
    }).addTo(map);

    // Fit bounds to the selected area
    if (highlightArea) {
      const highlighted = [];
      geoJsonLayerRef.current.eachLayer((layer) => {
        if (layer.feature.properties.PLN_AREA_N === highlightArea) {
          highlighted.push(layer);
        }
      });
      if (highlighted.length > 0) {
        map.fitBounds(L.featureGroup(highlighted).getBounds().pad(0.18));
      }
    }
  }, [geoJson, highlightArea, map]);

  return null;
}

const getConcepts = (conceptsObj) => {
  if (!conceptsObj || typeof conceptsObj !== 'object') return [];
  return Object.values(conceptsObj).map(c => c.description);
};

const Dashboard = () => {
  const [concepts, setConcepts]               = useState([]);
  const [selectedConcept, setSelectedConcept] = useState('Affordable everyday dining');
  const [rankOptions]                         = useState([1, 2, 3, 4, 5]);
  const [selectedRank, setSelectedRank]       = useState(1);
  const [areaDetails, setAreaDetails]         = useState(null);
  const [paretoData, setParetoData]           = useState(null);
  const [geoJson, setGeoJson]                 = useState(null);

  useEffect(() => {
    fetch('/data/pareto_shortlists_updated.json')
      .then(res => res.json())
      .then(data => {
        setParetoData(data);
        setConcepts(getConcepts(data.concepts));
      });
    fetch('/data/SG2019planning_area.geojson')
      .then(res => res.json())
      .then(data => setGeoJson(data));
  }, []);

  // Derive conceptKey from selectedConcept description
  const conceptKey = paretoData?.concepts
    ? Object.keys(paretoData.concepts).find(
        key => paretoData.concepts[key].description === selectedConcept
      )
    : null;

  useEffect(() => {
    if (!paretoData || !conceptKey) { setAreaDetails(null); return; }
    const areas = paretoData.concepts[conceptKey].areas || [];
    setAreaDetails(areas.find(a => a.rank === selectedRank) || null);
  }, [paretoData, conceptKey, selectedRank]);

  const barChartAreas = conceptKey ? (paretoData?.concepts[conceptKey]?.areas || []) : [];

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
              <IncomeMixPieChart incomeMix={areaDetails?.income_mix} />
            </div>
            <div className="dashboard-pie-cell">
              <DemographicPieChart
                primaryDemographic={areaDetails?.primary_demographic}
                primaryShare={areaDetails?.primary_demographic_share}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="dashboard-right">
        <div style={{ flex: 1, minHeight: 300, width: '100%' }}>
          {geoJson ? (
            <MapContainer
              style={{ height: 400, borderRadius: 8, width: '100%' }}
              center={[1.3521, 103.8198]}
              zoom={11}
              zoomControl={true}
              dragging={false}
              minZoom={10}
              maxZoom={18}
              maxBounds={SINGAPORE_BOUNDS}
              maxBoundsViscosity={1.0}
              scrollWheelZoom={true}
            >
              <SingaporeFit />
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                maxZoom={19}
              />
              <MapController
                geoJson={geoJson}
                highlightArea={areaDetails?.planning_area}
              />
            </MapContainer>
          ) : (
            <div style={{ border: '1px solid #ccc', height: 400, borderRadius: 8, background: '#f9f9f9', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span>Loading map...</span>
            </div>
          )}
        </div>

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
