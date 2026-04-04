import React from 'react';
import './Dashboard.css';

const directionConfig = {
  maximize: {
    label: 'Maximize',
    icon: '↑',
    className: 'maximize',
  },
  minimize: {
    label: 'Minimize',
    icon: '↓',
    className: 'minimize',
  },
};

const DirectionChip = ({ direction }) => {
  if (!direction || !directionConfig[direction]) return null;

  const config = directionConfig[direction];

  return (
    <span className={`criteria-direction-pill ${config.className}`}>
      <span className="criteria-direction-icon" aria-hidden="true">
        {config.icon}
      </span>
      <span>{config.label}</span>
    </span>
  );
};

export default DirectionChip;
