import React from 'react';
import { Bar } from 'react-chartjs-2';
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Title,
  Tooltip,
} from 'chart.js';
import DirectionChip from './DirectionChip';
import { DATA_UNAVAILABLE, formatChartValue, formatCurrency, formatPercent } from './display';
import { getBarColors } from './chartColors';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const sharedChartColor = {
  background: 'rgba(59, 130, 246, 0.55)',
  border: 'rgba(37, 99, 235, 0.85)',
};

const formatValueByUnit = (value, unit) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return DATA_UNAVAILABLE;
  }
  if (unit === '%') return formatPercent(value);
  if (unit === 'SGD') return formatCurrency(value);
  if (unit === '/5') return `${Number(value).toFixed(2)}/5`;
  return formatChartValue(value);
};

const yAxisLabel = (unit) => {
  if (unit === '%') return 'Percentage';
  if (unit === 'SGD') return 'SGD';
  if (unit === '/5') return 'Rating';
  if (unit === 'visits') return 'Visits';
  if (unit === 'competitors') return 'Competitors';
  return unit || 'Value';
};

const tickFormatter = (value, unit) => {
  if (unit === '%') return `${Number(value * 100).toFixed(0)}%`;
  if (unit === 'SGD') return Number(value).toFixed(0);
  if (unit === '/5') return Number(value).toFixed(1);
  return formatChartValue(value);
};

const MetricComparisonChart = ({
  areas,
  metricKey,
  selectedAreaName,
  direction,
  fallbackLabel,
  fallbackUnit,
}) => {
  if (!areas || areas.length === 0) return <div className="chart-empty">{DATA_UNAVAILABLE}</div>;

  const metricEntries = areas.map((area) => {
    const display = (area.criteria_display || []).find((item) => item.key === metricKey);
    return {
      area,
      display,
      value: display?.value ?? null,
    };
  });

  const chartLabel = metricEntries.find((entry) => entry.display?.label)?.display?.label || fallbackLabel || metricKey;
  const unit = metricEntries.find((entry) => entry.display?.unit)?.display?.unit || fallbackUnit || null;
  const barColors = getBarColors(
    metricEntries.map((entry) => entry.area),
    selectedAreaName,
    sharedChartColor,
  );

  const data = {
    labels: metricEntries.map((entry) => entry.area.planning_area),
    datasets: [
      {
        label: chartLabel,
        data: metricEntries.map((entry) => entry.value),
        backgroundColor: barColors.backgroundColor,
        borderColor: barColors.borderColor,
        borderWidth: 1.5,
        borderRadius: 6,
        barThickness: 18,
        maxBarThickness: 22,
        categoryPercentage: 0.72,
        barPercentage: 0.86,
      },
    ],
  };

  const options = {
    indexAxis: 'y',
    maintainAspectRatio: false,
    responsive: true,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (context) => `${chartLabel}: ${formatValueByUnit(context.raw, unit)}`,
          afterLabel: (context) => `Rank ${metricEntries[context.dataIndex].area.rank}`,
        },
      },
    },
    scales: {
      x: {
        title: { display: true, text: yAxisLabel(unit) },
        ticks: {
          callback: (value) => tickFormatter(value, unit),
        },
      },
      y: {
        title: { display: true, text: 'Planning area' },
      },
    },
  };

  return (
    <div className="metric-chart-wrap">
      <div className="metric-chart-title">
        <span>{chartLabel}</span>
        <DirectionChip direction={direction} />
      </div>
      <div className="metric-chart-canvas">
        <Bar data={data} options={options} />
      </div>
    </div>
  );
};

export default MetricComparisonChart;
