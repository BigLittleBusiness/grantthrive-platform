# GrantThrive Style Guide

**Version 1.0** | **Last Updated:** 2026-03-02

---

This document establishes the official design system and style guide for the GrantThrive platform. Its purpose is to ensure brand consistency, unify the user experience, and provide a single source of truth for all developers and designers.

All future development must adhere to these guidelines. Any deviation requires explicit approval and a corresponding update to this guide.

## 1. Colour Palette

The GrantThrive colour system is built on a primary brand green, a set of semantic colours for user feedback, and a neutral grayscale for text and backgrounds. Colours are defined as CSS custom properties (variables) in both the marketing site (`style.css`) and the React platform (`MarketingApp.css`, `AdminApp.css`).

### 1.1. Primary Brand Colour

**GrantThrive Green** is the sole primary colour. It is used for all primary call-to-action buttons, interactive element focus states, and key navigational components.

| Name | Hex | OKLCH | CSS Variable |
| :--- | :--- | :--- | :--- |
| GrantThrive Green | `#15803d` | `oklch(0.45 0.15 145)` | `--primary` |
| GrantThrive Green (Darker) | `#166534` | `oklch(0.35 0.12 145)` | `--green-dark` |

### 1.2. Semantic Palette

Semantic colours provide visual feedback to users for status, success, warnings, and errors. They are used consistently across alerts, badges, and validation states.

| Intent | Colour | Hex | Usage |
| :--- | :--- | :--- | :--- |
| **Success** | Green | `#4CAF50` | Form success messages, "Active" status, validation checkmarks |
| **Warning** | Amber | `#FF9800` | Confirmation modals, non-critical alerts, pending status |
| **Error** | Red | `#F44336` | Form errors, validation failures, "Inactive" status, destructive actions |
| **Info** | Teal | `#00ACC1` | Informational banners, new feature highlights |
| **Neutral** | Gray | `#757575` | Secondary text, disabled states, borders |

### 1.3. Grayscale & Tints

A neutral grayscale is used for text, backgrounds, and UI chrome. The React platform uses a numeric scale (e.g., `bg-gray-100`), while the marketing site uses named variables.

**Light Theme (Portal)**

| Usage | Hex | Tailwind Class |
| :--- | :--- | :--- |
| Page Background | `#FAFAFA` | `bg-gray-50` |
| Card/Paper Background | `#FFFFFF` | `bg-white` |
| Primary Text | `#212121` | `text-gray-900` |
| Secondary Text | `#757575` | `text-gray-600` |
| Borders & Dividers | `#E0E0E0` | `border-gray-200` |

**Dark Theme (Admin)**

| Usage | Hex | Tailwind Class |
| :--- | :--- | :--- |
| Page Background | `#111827` | `bg-gray-950` |
| Card/Paper Background | `#1F2937` | `bg-gray-900` |
| Primary Text | `#F9FAFB` | `text-gray-100` |
| Secondary Text | `#9CA3AF` | `text-gray-400` |
| Borders & Dividers | `#374151` | `border-gray-700` |

## 2. Typography

The GrantThrive brand uses a single primary font family, **Inter**, for all marketing and product interfaces. **Roboto** is used as a fallback for MUI components where Inter may not be available.

### 2.1. Font Families

- **Primary:** Inter (sans-serif)
- **Fallback:** Roboto, Segoe UI, system-ui

Inter is loaded from Google Fonts in the main `index.html` of both the marketing site and the React platform.

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
```

### 2.2. Typographic Scale

A consistent typographic scale is used to maintain visual hierarchy. The React platform uses Tailwind CSS utility classes, while the marketing site uses direct CSS.

| Element | Font Size | Font Weight | Tailwind Class |
| :--- | :--- | :--- | :--- |
| **Hero Title** | `clamp(2.2rem, 4.5vw, 3.4rem)` | 800 (ExtraBold) | `text-5xl font-extrabold` |
| **Page Title (h1)** | `2.25rem` (36px) | 700 (Bold) | `text-4xl font-bold` |
| **Section Title (h2)** | `1.875rem` (30px) | 700 (Bold) | `text-3xl font-bold` |
| **Card Title (h3)** | `1.5rem` (24px) | 600 (SemiBold) | `text-2xl font-semibold` |
| **Subtitle** | `1.25rem` (20px) | 500 (Medium) | `text-xl font-medium` |
| **Body** | `1rem` (16px) | 400 (Regular) | `text-base` |
| **Small/Caption** | `0.875rem` (14px) | 400 (Regular) | `text-sm` |

## 3. UI Components

Component styles are defined by a combination of MUI theme overrides (`theme.js`) and Tailwind CSS utility classes.

### 3.1. Buttons

Buttons have a consistent style across the platform.

- **Primary CTA:** Solid GrantThrive Green background (`bg-green-700`), white text, subtle hover effect (`hover:bg-green-800`).
- **Secondary:** White background, dark text, gray border (`border-gray-300`), subtle gray hover (`hover:bg-gray-50`).
- **Destructive:** Red background (`bg-red-600`), white text, subtle hover effect (`hover:bg-red-700`).
- **Padding:** `px-4 py-2` (medium), `px-6 py-3` (large).
- **Border Radius:** `8px` (`rounded-lg`).

### 3.2. Badges

Badges are used to indicate status or category. They use a consistent light-tint background with a darker corresponding text colour.

| Status | Background Class | Text Class |
| :--- | :--- | :--- |
| **Active/Success** | `bg-green-100` | `text-green-700` |
| **Inactive/Error** | `bg-red-100` | `text-red-700` |
| **Pending/Warning** | `bg-yellow-100` | `text-yellow-800` |
| **Professional Plan** | `bg-blue-100` | `text-blue-700` |
| **Enterprise Plan** | `bg-purple-100` | `text-purple-700` |
| **Default/Starter** | `bg-gray-100` | `text-gray-700` |

### 3.3. Forms & Inputs

Input fields share a common style:

- **Background:** White (`bg-white`) or light gray (`bg-gray-50`).
- **Border:** `1px solid #D1D5DB` (`border-gray-300`).
- **Border Radius:** `8px` (`rounded-lg`).
- **Focus State:** The border colour changes to GrantThrive Green (`focus:border-green-600`) with a matching subtle ring (`focus:ring-1 focus:ring-green-600`).

## 4. Spacing & Layout

The platform uses a consistent 4-point grid system for spacing, padding, and margins. Tailwind CSS utilities are used to apply this scale (e.g., `p-4` = 16px, `gap-2` = 8px).

- **Base Unit:** `4px`
- **Standard Padding:** `16px` (`p-4`), `24px` (`p-6`), `32px` (`p-8`).
- **Standard Gaps:** `8px` (`gap-2`), `16px` (`gap-4`), `24px` (`gap-6`).

## 5. Design Principles

1.  **Consistency is Key:** A user should never be surprised by how a component behaves or looks. Re-use existing components and styles wherever possible.
2.  **Clarity Over Clutter:** Prioritise clear information hierarchy. Use whitespace, typography, and colour to guide the user's attention, not to decorate.
3.  **Accessibility First:** All components must be accessible. This includes sufficient colour contrast, proper ARIA attributes, keyboard navigability, and focus management.
4.  **Mobile Responsive:** All layouts must be fully responsive and provide an excellent experience on screen sizes from mobile phones to large desktops.
5.  **Performance Matters:** Keep assets optimised and dependencies minimal. A fast, responsive interface is a core feature.
