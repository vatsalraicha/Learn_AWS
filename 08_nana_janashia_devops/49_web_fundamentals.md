# 49 — Web Fundamentals — HTML / CSS / JS in 2026

> Skim module. Vatsal isn't pivoting to frontend, but knowing modern HTML/CSS/JS basics fills a context gap when reviewing frontend PRs from team members.

## 1. How the web works (the 30-second model)

```
Browser → DNS → resolves domain → IP
         → TCP/TLS handshake → connection
         → HTTP/2 or HTTP/3 → request
         → server response (HTML + assets)
         → browser parses + renders
         → JS executes → can fetch more data
```

Key protocols:
- **HTTP/1.1** — text-based, one request per connection
- **HTTP/2** (2015) — binary, multiplexed, server push
- **HTTP/3** (2022) — over QUIC (UDP), no head-of-line blocking
- **WebSockets** — bidirectional persistent connection
- **Server-Sent Events** — one-way streaming from server
- **WebTransport** (emerging) — HTTP/3-based, replaces WebSockets in some use cases

## 2. HTML5 semantic elements

Use semantic tags, not div soup:
```html
<header>, <nav>, <main>, <article>, <aside>, <footer>
<section>, <figure>, <figcaption>, <details>, <summary>
<dialog> for modals
```

Accessibility:
- ARIA roles + labels
- WCAG 2.2 (2023) — current accessibility standard
- Screen readers parse semantic HTML naturally

## 3. Modern CSS (massive evolution since 2020)

### Layout
- **Flexbox** — 1D layouts
- **Grid** — 2D layouts; replaces Bootstrap-style grid frameworks
- **Container queries** (2023) — responsive based on parent size, not viewport
- **Subgrid** (2023) — grid children inherit grid lines

### Features
- **`:has()`** — parent selector (2023 GA in all browsers)
- **CSS Nesting** — like SCSS, native
- **Cascade Layers** (`@layer`) — explicit specificity buckets
- **`@scope`** — limit selectors to a subtree
- **CSS Custom Properties (variables)** — `--main-color: blue;`
- **`color-mix()`** + `color()` — advanced color math
- **`clamp()`, `min()`, `max()`** — fluid sizing

### Why this matters
2026 CSS can do 80% of what required JS in 2015. The "no-JS-needed" frontier keeps expanding.

## 4. JavaScript ES2024+

Recent additions:
- `Array.prototype.toSorted/toReversed/toSpliced` — immutable variants (2023)
- `Object.groupBy` (2024)
- `Promise.withResolvers` (2024)
- `Set` set operations (`union`, `intersection`) (2024-2025)
- `Iterator helpers` (2024-2025)
- **Decorators** — finally stable (2023+)
- **Records & Tuples** — immutable primitives (proposal stage)
- **Pipeline operator** (`|>`) — still proposal

## 5. TypeScript dominance

TypeScript ~90% of new web projects (2026). Why:
- Catches type errors at compile time
- IDE autocomplete is dramatically better
- Documentation via types
- Ecosystem libraries ship `.d.ts` automatically

Modern alternatives:
- **JSDoc with type checking** (`@ts-check`) — gradual TS without rewrite
- **Deno's built-in TS support**
- **Bun's built-in TS support**

## 6. Variables, conditionals, loops (the basics)

```javascript
const name = "world";  // immutable binding
let count = 0;          // mutable
var unused = 1;          // legacy — don't use

// Conditionals
if (x === y) { /* ... */ } else if (x > y) { /* ... */ }
const result = x > 0 ? "pos" : "neg";

// Loops
for (const item of items) { /* ... */ }
for (const [i, item] of items.entries()) { /* ... */ }
items.forEach((item, i) => { /* ... */ });
const doubled = items.map(x => x * 2);
const evens = items.filter(x => x % 2 === 0);
const sum = items.reduce((acc, x) => acc + x, 0);
```

## 7. Objects + arrays + destructuring

```javascript
const user = { name: "Alice", age: 30 };
const { name, age } = user;
const updated = { ...user, age: 31 };

const arr = [1, 2, 3, 4];
const [first, ...rest] = arr;
const doubled = arr.map(x => x * 2);
```

## 8. Functions

```javascript
// Function declaration
function add(a, b) { return a + b; }

// Arrow functions (most common)
const add = (a, b) => a + b;

// Default + rest params
const greet = (name = "world", ...others) => `Hello ${name}, ${others.join(", ")}`;

// Async/await
const fetchUser = async (id) => {
  const r = await fetch(`/api/users/${id}`);
  return await r.json();
};
```

## 9. Built-in functions

```javascript
JSON.parse(str);
JSON.stringify(obj);
Object.keys(obj);
Object.values(obj);
Object.entries(obj);
Array.from(iter);
Array.isArray(x);
parseInt(str, 10);
parseFloat(str);
Number.isNaN(x);
fetch(url, options).then(r => r.json());
```

## 10. Browser DevTools (the muscle memory)

Open: F12 / Cmd+Option+I. Key tabs:
- **Elements** — DOM + CSS inspection
- **Console** — JS REPL + logs
- **Sources** — debugger, breakpoints
- **Network** — HTTP requests, timing
- **Performance** — flame charts
- **Lighthouse** — performance + a11y + SEO audit
- **Application** — storage, cookies, service workers

`document.querySelector('button')` to grab elements in Console.

## 11. Quick self-check

1. What's the difference between HTTP/2 and HTTP/3 at protocol level?
2. What's `:has()` and why is it useful?
3. What's the difference between `let` and `const`?
4. What's TypeScript adoption percentage in new web projects in 2026?
5. Why is `Array.prototype.toSorted()` an improvement over `sort()`?

(Answers: HTTP/2 over TCP with multiplexing, HTTP/3 over QUIC (UDP) eliminating head-of-line blocking; parent selector — can style based on what a child contains; let is mutable binding, const is immutable binding; ~90%; toSorted returns a new array (immutable), sort mutates in place — toSorted matches functional programming style + avoids subtle bugs.)
