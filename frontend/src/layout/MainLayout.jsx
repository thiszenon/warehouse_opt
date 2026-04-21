import React from "react";

export default function MainLayout({ children }) {
  // Détection du composant enfant pour adapter le layout
  const childType = children?.type;
  const childName = childType?.displayName || childType?.name || "";

  // ✅ Pages "plein écran" (sans padding / sans maxWidth)
  // Ajoute ici d’autres pages full-screen si besoin
  const isFullScreenPage = childName === "TourSelection";

  return (
    <div style={shell}>
      {/* Header global */}
      <header style={appHeader}>
        <span style={brand}>Picking Optimizer</span>

        <span style={modeTag}>
          Mode POC
        </span>
      </header>

      {/* Contenu */}
      <main style={isFullScreenPage ? mainFullScreen : mainDefault}>
        {children}
      </main>
    </div>
  );
}

/* =========================
   Styles
   ========================= */

const shell = {
  minHeight: "100svh",
  backgroundColor: "#f4f4f4",
  fontFamily: "Arial, sans-serif",
  display: "flex",
  flexDirection: "column",
  overflow: "hidden" // empêche le scroll sur le shell
};

const appHeader = {
  backgroundColor: "#ffffff",
  borderBottom: "1px solid #ddd",
  padding: "16px 24px",
  display: "flex",
  alignItems: "center",
  flex: "0 0 auto"
};

const brand = {
  fontSize: 16,
  fontWeight: 600,
  color: "#222"
};

const modeTag = {
  marginLeft: 12,
  fontSize: 13,
  color: "#666"
};

// Layout normal (la plupart des pages)
const mainDefault = {
  //flex: "1 1 auto",
  padding: 32,
  maxWidth: 900,
  margin: "0 auto",
  width: "100%",
  boxSizing: "border-box",
  flexShrink:0,
  overflow: "visible" // pages classiques peuvent scroller si besoin
};

// Layout plein écran (TourSelection)
const mainFullScreen = {
  //flex: "1 1 auto",
  padding: 0,         // ✅ plus de +64px
  maxWidth: "none",   // ✅ pas de contrainte 900px
  margin: 0,
  width: "100%",
  boxSizing: "border-box",
  overflow: "hidden"  // ✅ pas de scroll vertical dans le conteneur
};