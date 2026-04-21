
export const tours = [
  {
    id: "RA1",
    date: "12/06/2026",
    warehouse: "Carglass",
    orders: 14,
    items: 186
  },
  {
    id: "RA2",
    date: "12/06/2026",
    warehouse: "Carglass",
    orders: 10,
    items: 143
  }
];

export const comparisonData = {
  before: {
    distanceKm: 3.2,
    time: "1h45",
    picks: [
      "AB 12",
      "D 04",
      "C29",
      "H35",
      "AB 12",
      "D 04",
      "C29",
      "H35",
      "AB 12",
      "D 04",
      "C29",
      "H35"
    ]
  },
  after: {
    distanceKm: 2.5,
    time: "1h20",
    gainPercent: 22,
    picks: [
      "AB 12",
      "D 04",
      "C29",
      "H35",
      "AB 12",
      "D 04",
      "C29",
      "H35",
      "AB 12",
      "D 04",
      "C29",
      "H35",
      "AB 12",
      "D 04",
      "C29",
      "H35"
    ]
  }
};
