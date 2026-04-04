const selectedBarColor = {
  background: 'rgba(37, 99, 235, 0.9)',
  border: 'rgba(29, 78, 216, 1)',
};

export const getBarColors = (areas, selectedAreaName, baseColor) => ({
  backgroundColor: areas.map((area) =>
    area.planning_area === selectedAreaName
      ? selectedBarColor.background
      : baseColor.background,
  ),
  borderColor: areas.map((area) =>
    area.planning_area === selectedAreaName
      ? selectedBarColor.border
      : baseColor.border,
  ),
});
