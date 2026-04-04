export const DATA_UNAVAILABLE = 'Data unavailable';

export const displayText = (value) => {
  if (value === null || value === undefined || value === '') {
    return DATA_UNAVAILABLE;
  }
  return value;
};

export const formatPercent = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return DATA_UNAVAILABLE;
  }
  return `${(Number(value) * 100).toFixed(1)}%`;
};

export const formatChartValue = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return DATA_UNAVAILABLE;
  }
  return new Intl.NumberFormat().format(Number(value));
};

export const formatCurrency = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return DATA_UNAVAILABLE;
  }
  return `SGD ${Number(value).toFixed(2)}`;
};
