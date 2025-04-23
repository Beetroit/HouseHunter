# Plan: Frontend UI Overhaul (Revamp First)

This plan outlines the steps to modernize the frontend UI of the HouseHunter application, prioritizing the overall aesthetic revamp before addressing specific image sizing issues.

## Phase 1: Modern UI Revamp

1.  **Define Aesthetic:**
    *   **Theme:** Establish a consistent color palette (e.g., modern light/dark theme with accent colors). Consider a subtle gradient background for the main body or key sections.
    *   **Style:** Incorporate modern UI techniques:
        *   **Glass Morphism:** Apply `backdrop-filter: blur(Xpx);` and `background-color: rgba(R, G, B, A);` to elements like the navbar, listing cards, modals, and potentially the footer. Adjust transparency and blur for the desired effect. Add subtle borders.
        *   **Gradients & Shadows:** Use soft gradients for backgrounds or accents. Refine box shadows for depth (softer, multi-layered).
        *   **Typography:** Select clean, modern web fonts (e.g., from Google Fonts) and establish a clear type scale.
        *   **Spacing & Layout:** Optimize whitespace, padding, and margins. Ensure consistent alignment using Flexbox/Grid.
        *   **Interactivity:** Add subtle transitions for hover effects.
2.  **Implementation:**
    *   **CSS Variables:** Define theme values (colors, fonts, spacing, border-radius, blur amount) in `:root` within `frontend/src/index.css`.
    *   **Global Styles (`index.css`, `App.css`):** Apply base styles, body background, font settings. Style the main layout (`.App`, `nav`, `main`, `footer`) incorporating the chosen techniques (e.g., glass morphism navbar).
    *   **Component Styles:**
        *   `ListingStyles.css`: Revamp `.listing-card` (glass morphism, shadows, typography, spacing). Style pagination. *Note: Image styling will be deferred.*
        *   `FormStyles.css`: Modernize inputs, labels, buttons.
        *   `ChatStyles.css`: Apply theme to chat interface.
        *   Other Components: Ensure consistency.
    *   **Review & Refine:** Check all pages for visual consistency and responsiveness.

## Phase 2: Fix Property Image Display

1.  **Target Files:** `frontend/src/pages/ListingStyles.css`.
2.  **Action:** Add specific CSS rules for the image container (`.listing-card-image-container`) and the image itself (`.listing-card-image`).
    *   Ensure images scale correctly within their cards (e.g., `max-width: 100%`, `height: auto`).
    *   Define container dimensions or aspect ratio for consistency (e.g., `height: 200px`, `overflow: hidden`).
    *   Use `object-fit: cover` to prevent image distortion while filling the container.

## Visual Plan (Mermaid)

```mermaid
graph TD
    A[Start: Revamp UI & Fix Image] --> C[Define Modern Aesthetic (Theme, Glassmorphism, Fonts, Spacing)];
    C --> D[Set up CSS Variables in index.css];
    D --> E[Apply Global Styles (Body, Layout, Nav, Footer) in index.css/App.css];
    E --> F[Revamp Component Styles (Listing Cards, Forms, Chat, etc.)];
    F --> G[Ensure Consistency & Responsiveness Across All Pages];
    G --> B[Add CSS for Property Images in ListingStyles.css];
    B --> H[End: Sleek, Modern UI with Correctly Sized Images];