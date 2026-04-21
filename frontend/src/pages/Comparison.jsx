import React, { useEffect, useState } from "react";
import { comparisonData } from "../data/comparisonData";

export default function Comparison({ onValidate, onCancel }) {
  const { tour, summary, orders } = comparisonData;

  /* ================= ÉTATS ================= */
  const metricsOrder = ["orders", "items", "time", "distance"];
  const [loadedMetrics, setLoadedMetrics] = useState([]);
  const [showOrders, setShowOrders] = useState(false);

  /* ================= SIMULATION DU CALCUL ================= */
  useEffect(() => {
    const interval = setInterval(() => {
      setLoadedMetrics(prev => {
        if (prev.length >= metricsOrder.length) {
          clearInterval(interval);
          return prev;
        }
        return [...prev, metricsOrder[prev.length]];
      });
    }, 400);

    return () => clearInterval(interval);
  }, []);

  const allLoaded = loadedMetrics.length === metricsOrder.length;

  return (
    <div style={page}>

      {/* ===== EN-TÊTE ===== */}
      <header style={header}>
        <h2 style={title}>
          Comparaison des parcours – Tournée {tour.id}
        </h2>
        <div style={subtitle}>Date : {tour.date}</div>

        <div style={status}>
          {!allLoaded ? (
            <>
              <Spinner />
              <span>Optimisation en cours…</span>
            </>
          ) : (
            <>
              <Check />
              <span>Parcours optimisé avec succès</span>
            </>
          )}
        </div>
      </header>

      {/* ===== SYNTHÈSE ===== */}
      <Section title="Synthèse de la tournée">
        <table style={table}>
          <tbody>
            <MetricRow
              label="Commandes"
              value={tour.totalOrders}
              loaded={loadedMetrics.includes("orders")}
            />
            <MetricRow
              label="Articles"
              value={tour.totalItems}
              loaded={loadedMetrics.includes("items")}
            />
            <MetricRow
              label="Temps estimé"
              value={`${summary.timeMin} min`}
              loaded={loadedMetrics.includes("time")}
            />
            <MetricRow
              label="Distance estimée"
              value={`${summary.distanceKm} km`}
              loaded={loadedMetrics.includes("distance")}
            />
          </tbody>
        </table>
      </Section>

      {/* ===== COMMANDES ===== */}
      <Section
        title={
          <div style={sectionHeader}>
            <span>Commandes de la tournée</span>
            <button
              onClick={() => setShowOrders(!showOrders)}
              style={detailsLink}
            >
              {showOrders ? "Masquer les détails" : "Afficher les détails"}
            </button>
          </div>
        }
      >
        {showOrders && (
          <div style={ordersScroll}>
            <table style={table}>
              <thead>
                <tr>
                  <th style={th}>Commande</th>
                  <th style={th}>Articles</th>
                  <th style={th}>Temps estimé</th>
                  <th style={th}>Distance estimée</th>
                </tr>
              </thead>
              <tbody>
                {orders.map(order => (
                  <tr key={order.orderId}>
                    <td style={td}>{order.orderId}</td>
                    <td style={td}>{order.items}</td>
                    <td style={td}>{order.timeMin} min</td>
                    <td style={td}>{order.distanceKm} km</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      {/* ===== ACTIONS ===== */}
      <footer style={actions}>
        <button style={primary} onClick={onValidate}>
          Appliquer l’ordre op
          timisé
        </button>
        <button style={secondary} onClick={onCancel}>
          Conserver l’organisation actuelle
        </button>
      </footer>

    </div>
  );
}

/* ================= COMPOSANTS ================= */

function MetricRow({ label, value, loaded }) {
  return (
    <tr>
      <td style={td}>{label}</td>
      <td style={metricCell}>
        <span style={iconSlot}>
          {!loaded ? <Spinner /> : <Check />}
        </span>
        <span style={metricValue}>{value}</span>
      </td>
    </tr>
  );
}

function Section({ title, children }) {
  return (
    <section style={section}>
      <div style={bar} />
      <div style={sectionTitle}>{title}</div>
      {children}
    </section>
  );
}

function Spinner() {
  return <div style={spinner} />;
}

function Check() {
  return <div style={check}>✓</div>;
}

/* ================= STYLES ================= */

const page = {
  height: "100vh",
  display: 10,
  padding: 12,
  overflow: "hidden",
  flexDirection: "column",
};



const header = {
  position: "sticky",
  top: 0,
  zIndex: 10,
  background: "#f4f4f4", // même fond que la page
  paddingBottom: 8
};

const actions = {
  display: "flex",
  gap:12,
  marginTop: 8
};

const title = {
  fontSize: "clamp(18px, 2vw, 22px)",
  fontWeight: 600
};

const subtitle = {
  fontSize: "clamp(12px, 1.4vw, 14px)",
  color: "#6b7280"
};

const status = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  fontSize: "clamp(12px, 1.3vw, 14px)",
  color: "#374151"
};

const section = {
  background: "#fff",
  padding: 14,
  position: "relative",
  boxShadow: "0 1px 3px rgba(0,0,0,0.1)"
};

const bar = {
  position: "absolute",
  left: 0,
  top: 0,
  bottom: 0,
  width: 4,
  background: "#1f2937"
};

const sectionTitle = {
  fontSize: "clamp(13px, 1.4vw, 15px)",
  fontWeight: 600,
  marginBottom: 8
};

const sectionHeader = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center"
};

const table = {
  width: "100%",
  borderCollapse: "collapse",
  tableLayout: "fixed"
};

const th = {
  textAlign: "left",
  fontWeight: 600,
  fontSize: "clamp(12px, 1.2vw, 13px)"
};

const td = {
  fontSize: "clamp(12px, 1.2vw, 13px)",
  padding: "4px 0"
};

const metricCell = {
  display: "flex",
  alignItems: "center",
  gap: 8
};

const iconSlot = {
  width: 18,
  display: "flex",
  justifyContent: "center"
};

const metricValue = {
  fontWeight: 600,
  fontVariantNumeric: "tabular-nums"
};

const ordersScroll = {
  maxHeight: "30vh",
  overflowY: "auto",
  borderTop: "1px solid #e5e7eb",
  marginTop: 8
};

const detailsLink = {
  background: "none",
  border: "none",
  fontSize: "clamp(11px, 1.1vw, 13px)",
  cursor: "pointer",
  textDecoration: "underline",
  color: "#374151"
};

const primary = {
  padding: "8px 14px",
  backgroundColor: "#1f2937",
  color: "#fff",
  border: "none",
  borderRadius: 3,
  cursor: "pointer"
};

const secondary = {
  padding: "8px 14px",
  backgroundColor: "#e5e7eb",
  border: "none",
  borderRadius: 3,
  cursor: "pointer"
};

const spinner = {
  width: 14,
  height: 14,
  border: "2px solid #e5e7eb",
  borderTop: "2px solid #1f2937",
  borderRadius: "50%",
  animation: "spin 1s linear infinite"
};

const check = {
  width: 16,
  height: 16,
  borderRadius: "50%",
  background: "#16a34a",
  color: "#fff",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontSize: 11
};
