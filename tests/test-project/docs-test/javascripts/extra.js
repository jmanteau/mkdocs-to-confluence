/* ================================================================
   Airbus Design System Integration - Custom JavaScript
   ================================================================ */

// Wait for the document to be ready using Material for MkDocs observable
// This is important for instant loading compatibility
document$.subscribe(function() {
  console.log('Airbus Design System theme loaded');

  // Initialize custom functionality here
  initializeAirbusComponents();
});

/**
 * Initialize Airbus Design System components
 */
function initializeAirbusComponents() {
  // Add custom component initialization here
  // For example: tooltips, dropdowns, modals, etc.

  // Example: Add Airbus Design System classes to elements
  enhanceButtons();
  enhanceTables();
}

/**
 * Enhance buttons with Airbus Design System classes
 */
function enhanceButtons() {
  // Find all Material buttons and add Airbus styling
  const buttons = document.querySelectorAll('.md-button');
  buttons.forEach(button => {
    // Add Airbus Design System classes if needed
    // button.classList.add('ds-button');
  });
}

/**
 * Enhance tables with Airbus Design System classes
 */
function enhanceTables() {
  // Find all tables and add Airbus styling
  const tables = document.querySelectorAll('table');
  tables.forEach(table => {
    // Add Airbus Design System classes if needed
    // table.classList.add('ds-table');
  });
}

/**
 * Custom analytics or tracking (optional)
 */
function trackAirbusEvents() {
  // Add custom event tracking here if needed
  document.addEventListener('click', function(e) {
    if (e.target.matches('.md-button')) {
      console.log('Button clicked:', e.target.textContent);
    }
  });
}

// Initialize tracking if needed
// trackAirbusEvents();
