# 50 — Frontend Framework Landscape

## 1. The 2026 frontend framework market

| Framework | Share | Notable |
|---|---|---|
| **React** | ~40% (still dominant) | React 19 RSC; meta-frameworks: Next.js, Remix |
| **Vue** | ~12% | Vue 3 only (Vue 2 EOL); Nuxt for SSR |
| **Angular** | ~10% (mostly legacy + enterprise) | v18+ with signals + standalone components |
| **Svelte** | ~8% (growing) | Svelte 5 with runes; SvelteKit |
| **Solid** | ~3% (small but loved) | Fine-grained reactivity; SolidStart |
| **Qwik** | ~2% (niche) | Resumability concept; meta-framework Qwik City |
| **HTMX + Alpine** | rising | Server-rendered + small JS |
| **Lit / Web Components** | <5% | Standards-based |

## 2. The mental model differences

| Framework | Reactivity model |
|---|---|
| **React** | Re-render component on state change; VDOM diff |
| **Vue** | Reactive refs; templated; small VDOM |
| **Angular** | Zone.js change detection (legacy) → Signals (modern) |
| **Svelte** | Compile away — no runtime VDOM |
| **Solid** | Fine-grained — only the DOM nodes that depend on changed state re-render |

The 2026 trend: **fine-grained reactivity** (Solid, Svelte runes, Vue Composition API + Vapor mode, Angular signals) — fewer wasted renders.

## 3. React in 2026

- **React 19** (Dec 2024) — actions, useOptimistic, useFormStatus, RSC stable
- **Next.js 15** (Oct 2024) — App Router + RSC + Turbopack default
- **Remix → React Router 7** (Nov 2024) — merged
- **Vite-based React** — for SPAs without SSR

Server Components (RSC): components run server-side; only client components hydrate; smaller JS bundle. Game-changer for data-heavy apps.

## 4. Vue in 2026 — preview

Vue 3 only (Vue 2 EOL Dec 2023). Defaults:
- **Composition API** (`setup()` / `<script setup>`)
- **Pinia** for state (replaced Vuex)
- **Vue Router 4**
- **Nuxt 3 / 4** for SSR meta-framework
- **Vapor Mode** — Vue 3.x emerging; compile-to-no-VDOM like Svelte

See Module 51 for the deep dive.

## 5. Svelte 5 (2024) — runes

```svelte
<script>
  let count = $state(0);
  let doubled = $derived(count * 2);
  $effect(() => {
    console.log(`count is ${count}`);
  });
</script>

<button onclick={() => count++}>+</button>
<p>{count} → {doubled}</p>
```

Runes (`$state`, `$derived`, `$effect`) are explicit reactivity — replaces Svelte 4's implicit assignment-based reactivity.

## 6. Angular (Google) — what changed

Angular 18+ (2024) modernized:
- **Standalone components** — no NgModule
- **Signals** — fine-grained reactivity (replacing Zone.js)
- **Built-in control flow** (`@if`, `@for`)
- **Hydration** improvements

Mostly used in enterprise (Capital One frontend has Angular pockets).

## 7. The meta-framework era

| Meta-framework | Wraps | Adds |
|---|---|---|
| **Next.js** | React | SSR, RSC, routing, image opt |
| **Remix / React Router 7** | React | SSR, data loaders/actions |
| **Nuxt** | Vue | SSR, file-routing |
| **SvelteKit** | Svelte | SSR, file-routing |
| **SolidStart** | Solid | SSR, file-routing |
| **Astro** | Any (islands) | MPA-first, Markdown content |
| **Qwik City** | Qwik | Resumability |

Astro deserves special mention — uses any framework, but only ships the framework's JS for interactive islands. Massive perf win for content sites.

## 8. Build tools (the 2026 reality)

- **Vite** dominant for dev + SPAs
- **Turbopack** (Next.js bundled; Rust)
- **Rspack** (Webpack-compatible, Rust)
- **esbuild** (Go) — Vite's underlying minifier
- **swc** (Rust) — Babel replacement
- **Webpack** — legacy maintenance mode
- **Rollup** — library bundling
- **Bun** — JS runtime + bundler in one

Vite + esbuild + swc handle ~90% of new projects.

## 9. State management

| Tool | Framework |
|---|---|
| **Zustand, Jotai** | React |
| **Redux Toolkit** | React (legacy-pattern but still used) |
| **TanStack Query** | All |
| **SWR** | React |
| **Pinia** | Vue |
| **NgRx, NGXS, Signal Store** | Angular |
| **XState** | Any (state machines) |
| **Nanostores** | Any |

The 2026 default: **TanStack Query for server state**, **Zustand / Jotai / Pinia for client state**. Redux is legacy.

## 10. Pick a framework — decision frame

| Goal | Pick |
|---|---|
| **Career safety + hiring pool** | React (Next.js) |
| **Most enjoyable DX (subjective)** | Svelte or Vue |
| **Enterprise / Google ecosystem** | Angular |
| **Performance ceiling** | Solid or Qwik |
| **Content-heavy (blog, docs, marketing)** | Astro |
| **Minimal JS server-rendered** | HTMX + tiny Alpine.js |

For Vatsal: if you ever need a side project, **Next.js (React)** for safest career signal + AI tools (Cursor, Claude Code) work best with it.

## 11. Quick self-check

1. What are React Server Components and what problem do they solve?
2. What's "fine-grained reactivity" and which frameworks implement it?
3. What's Vue 3's preferred state management library?
4. What's Astro's island architecture?
5. Why is Webpack in maintenance mode?

(Answers: components run server-side and stream HTML, only client components hydrate — smaller JS bundle, faster TTI for data-heavy apps; only DOM nodes that depend on changed state re-render, vs whole-component re-render — Solid, Svelte 5, Vue Vapor, Angular signals; Pinia replaced Vuex; only ships JS for interactive components, rest is static HTML — massive perf win for content sites; Vite + esbuild + swc are ~10x faster and Webpack's perf can't catch up.)
