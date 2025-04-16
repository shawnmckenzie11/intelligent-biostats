# Cursor Project Rules

This document outlines the Cursor rules for consistent development across devices.

## Setup Instructions

1. Install Cursor IDE
2. Clone the repository
3. Open the project in Cursor
4. Verify that `.cursor/rules` directory is present
5. Check that `.cursor-config.json` is loaded

## Available Rules

### UI Formatting Rules
- Location: `.cursor/rules/ui-formatting-rules.mdc`
- Purpose: Maintains consistent UI styling
- Auto-apply: Yes
- Scope: All UI components and styles
- Settings:
  - Color Scheme: #2c3e50 (primary), #3498db (secondary)
  - Typography: Inter font family
  - Layout: Clean, modern, responsive
  - Components: Consistent styling
  - Interactive Elements: Smooth transitions

### Library and Route Awareness
- Location: `.cursor/rules/library-and-route-awareness.mdc`
- Purpose: Maintains context for dependencies and routing
- Auto-apply: Yes
- Scope: All backend routes and library usage
- Features:
  - Dependency tracking
  - Library awareness
  - Architecture context

## Rule Validation

The system automatically validates rules when:
1. Opening the project
2. Switching branches
3. Pulling updates
4. Creating new files

## Troubleshooting

If rules aren't being applied:
1. Verify `.cursor-config.json` is present
2. Check `.cursor/rules` directory exists
3. Restart Cursor IDE
4. Run `cursor rules --validate` in terminal

## Important Note

These rules are for development consistency only and do not affect the webapp's functionality. They help maintain consistent styling and development practices across different devices. 