import React from "react";
import { tours } from "../data/mockData";
import { FolderIcon } from "@heroicons/react/24/outline";

/**
 * Page 1 — Tournées disponibles
 * Objectifs:
 * - Zone centrale avec fond sombre/neutre
 * - Bloc (cards + bouton) "surface" claire au-dessus (shadow/border)
 * - Un peu d'espace sous la ligne du header
 * - Moins d'espace entre cards et bouton
 * - Scroll horizontal uniquement sur les cards
 * - Pas de scrollbar verticale dans le cardContainer
 *
 * IMPORTANT:
 * - Pour éviter les scrolls parasites, le parent (MainLayout) ne doit pas ajouter
 *   padding:32px sur cette page (mainFullScreen conseillé).
 */
export default function TourSelection({ onStartOptimization }) {
  const hasTours = Array.isArray(tours) && tours.length > 0;

  return (
    <div style={page}>
      {/* ===== HEADER ===== */}
      <header style={header}>
        <h2 style={title}>Tournées disponibles</h2>
        <p style={subtitle}>Tournées prêtes à être optimisées avant impression</p>
      </header>

      {/* ===== ZONE CENTRALE (fond sombre) ===== */}
      <main style={mainArea}>
        {!hasTours ? (
          <div style={surface}>
            <div style={emptyState}>Aucune tournée disponible pour l’optimisation.</div>
          </div>
        ) : (
          <div style={surface}>
            <div style={contentBlock}>
              <div style={cardsContainer} aria-label="Liste des tournées disponibles">
                {tours.map((tour) => (
                  <div key={tour.id} style={card}>
                    <FolderIcon style={folderIcon} />
                    <div style={cardId}>{tour.id}</div>
                  </div>
                ))}
              </div>

              <button
                type="button"
                style={primaryButton}
                onClick={() => onStartOptimization(tours)}
              >
                Commencer l’optimisation
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

/* ======================================================
   STYLES (inline)
   ====================================================== */

const page = {
  height: "100svh",
  display: "flex",
  flexDirection: "column",
  background: "var(--bg)",
  overflow: "hidden",
  boxSizing: "border-box"
};

/* ===== Header ===== */
const header = {
  padding: "10px 16px 8px",
  background: "var(--bg)",
  borderBottom: "1px solid var(--border)",
  flex: "0 0 auto"
};

const title = {
  textAlign: "center",
  margin: "0 0 4px"
};

const subtitle = {
  textAlign: "center",
  fontSize: "12px",
  margin: 0,
  color: "var(--text)"
};

/* ===== Zone centrale (fond sombre/neutre) ===== */
const mainArea = {
  flex: "1 1 auto",
  display: "flex",
  justifyContent: "center",
  alignItems: "flex-start",
  paddingTop: 14,            // ✅ un peu d'espace après la ligne du header
  paddingLeft: 16,
  paddingRight: 16,
  background: "#f4f4f4",     // ✅ fond sombre / neutre derrière la surface
  overflow: "hidden"
};

/**
 * Surface claire "posée" sur le fond sombre
 * -> donne l'effet "au-dessus" et distingue le bloc cards/bouton du fond
 */
const surface = {
  background: "var(--bg)",
  borderRadius: 12,
  border: "1px solid var(--border)",
  boxShadow: "var(--shadow)",
  padding: "16px 20px 14px",
  maxWidth: "100%",
  display: "flex",
  justifyContent: "center"
};

/**
 * Bloc interne: cards + bouton
 * gap = espace entre cards et bouton (réduit)
 */
const contentBlock = {
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  gap: 8,          // ✅ réduit l'espace entre cards et bouton
  flexShrink: 0,
  maxWidth: "100%"
};

/* ===== Cards : scroll horizontal uniquement ===== */
const cardsContainer = {
  display: "flex",
  gap: 12,
  padding: 0,
  maxWidth: "100%",

  // ✅ hauteur contrôlée = pas de scrollbar verticale
  height: 110,
  maxHeight: 110,

  overflowX: "auto",
  overflowY: "hidden",
  WebkitOverflowScrolling: "touch",

  // ✅ évite les étirements verticaux et l'impression de "barre à droite"
  alignItems: "center",

  background: "transparent"
};

const card = {
  minWidth: 160,
  height: 110,
  background: "rgba(255,255,255,0.96)",
  borderRadius: 10,
  border: "1.5px solid var(--border)",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "center",
  flexShrink: 0
};

const folderIcon = {
  width: 30,
  height: 30,
  color: "var(--text-h)",
  opacity: 0.75,
  marginBottom: 6
};

const cardId = {
  fontSize: "14px",
  fontWeight: 600,
  color: "var(--text-h)"
};

/* ===== Empty state ===== */
const emptyState = {
  background: "transparent",
  color: "var(--text)",
  padding: 8
};

/* ===== Bouton ===== */
const primaryButton = {
  padding: "8px 16px",
  backgroundColor: "#1f2937",
  color: "#ffffff",
  border: "none",
  borderRadius: 8,
  cursor: "pointer",
  fontSize: "13px",
  lineHeight: "1",
  width: "auto",
  minWidth: "unset"
};
