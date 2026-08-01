---
name: spendly-ui-designer
description: Generates modern, production-ready Jinja2/HTML + vanilla CSS UI for Spendly, a personal expense tracker (Flask/Jinja2/vanilla CSS stack, github.com/Basantakatuwal/Spendly). Use this skill whenever the user asks to design, create, build, redesign, improve, or restyle any page or component for Spendly — e.g. "design the dashboard page", "create UI for the add-expense form", "build a component for category breakdown", "redesign the transactions list". Also use it for any general Spendly frontend/UI work even if phrased casually ("make this page look better", "the expense card looks dated"). Produces a clean modern fintech-style design (card layout, soft shadows, rounded corners, 8px spacing grid, meaningful icons) consistent with Spendly's established design tokens — do not hand-roll one-off styles for Spendly UI without consulting this skill first.
---

# Spendly Frontend UI Designer

Generates modern, consistent UI for Spendly (Flask + Jinja2 + vanilla CSS).
This skill's job is visual/structural design of pages and components —
not backend logic, routes, or database wiring.

## Workflow

### 1. Get the essentials

You need at minimum: **which page/component** (e.g. "dashboard", "add
expense form", "expense card", "category breakdown chart"). If that's
already clear from the user's message, don't ask — proceed.

Optionally useful, ask only if it would meaningfully change the output and
isn't already obvious from context:
- Any constraints (fields required, specific data shown, layout preference)
- Whether this fits into an existing base template/layout the user can
  share, or reference screenshots of the current look

If the user has uploaded files or screenshots, or references an existing
template/CSS file, read them first — see "Consistency rule" below. Don't
block on asking for screenshots if none are readily available; fall back
to the default design system instead of stalling the request.

### 2. Load the design system

Before writing any code:
- Read `assets/design-tokens.css` — this is Spendly's base token set
  (colors, spacing, radius, shadow, typography) and base primitive classes
  (`.sp-card`, `.sp-btn`, `.sp-badge`, etc). Reuse these; don't invent
  parallel ones.
- Read `references/design-guide.md` — the full rule set for visual style,
  icon strategy, file conventions, and what to avoid.

If the user has shared their actual project files (existing templates or
CSS), prefer matching what's already there over the bundled defaults —
see the Consistency rule in the design guide. If this is the first
component ever generated for the project, the bundled tokens become the
new baseline; treat them as established from that point on for the rest
of the conversation.

### 3. Generate the output

Produce, in this order:

1. **UI structure (brief).** A few sentences to a short list: the layout
   approach, key UX decisions, and why (e.g. "expenses grouped by day
   with sticky date headers so long lists stay scannable"). Keep this
   tight — it's a rationale, not a spec document.
2. **Code.**
   - The Jinja2 template file, using semantic HTML, `sp-` prefixed
     classes from the token system, mock data via Jinja2 loops/vars
     (clearly fake but realistic — real category names, plausible
     amounts/dates, not "Lorem ipsum" or "Item 1/2/3").
   - The CSS additions (new component-specific rules only — don't
     re-emit the whole token file every time; reference it as already
     present, or include it verbatim the first time it's needed in the
     conversation).
   - Follow the file/output conventions in `references/design-guide.md`
     exactly (file names, where CSS goes, Jinja2 conventions).
3. **Design quality check (brief).** Confirm in a line or two how the
   output satisfies: modern SaaS/fintech look, spacing/hierarchy, card
   layout, subtle color/shadow use — don't belabor this, it's a sanity
   confirmation, not a repeat of the structure section.
4. **Icons used.** Note which icons were used and why that delivery
   method (inline SVG vs Lucide CDN) was chosen for this case, per the
   icon guidance in the design guide.

### 4. Delivering files

Use `create_file` to write the actual template/CSS files (don't just show
code in prose — Spendly is a real codebase the user is building) and
`present_files` so the user can grab them. If the user pasted an existing
file to edit in place, use `str_replace` on it instead of creating a new
one.

## Hard rules (see design-guide.md for full detail)

- 8px spacing grid, rounded corners, soft shadows, card-based grouping —
  no exceptions without the user explicitly asking for a different style.
- No generic/dated admin-template look; no unstructured code dumps.
- Icons must be real (inline SVG or Lucide CDN), never emoji or empty
  placeholder icon slots.
- This skill outputs UI + mock data only — no Flask route/view logic,
  no real DB queries. If the user also wants backend wiring, do the UI
  per this skill and flag that the logic is a separate step.