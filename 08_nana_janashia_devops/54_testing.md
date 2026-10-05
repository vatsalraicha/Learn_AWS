# 54 — Test Automation — Jest + Vitest + Playwright

## 1. The test pyramid (and its critics)

```
        /\
       /  \    E2E (slow, fragile)        ← 5-10%
      /────\
     /      \  Integration (medium)        ← 20-30%
    /────────\
   /          \ Unit tests (fast, many)    ← 60-70%
  /────────────\
```

Modern critique (Kent C. Dodds: **Testing Trophy**):
```
   Static (TS, eslint)
   ─────────────────
   Unit
   ─────────────────
   Integration   ← most value
   ─────────────────
   E2E
```

The lesson: lots of unit + heavy on integration + a few E2E + lean on static analysis.

## 2. JavaScript testing landscape

| Tool | Use |
|---|---|
| **Jest** | Most-installed; mature; slow startup |
| **Vitest** | Vite-aligned; faster; Jest-compatible API; **dominant for new projects 2026** |
| **Mocha + Chai** | Legacy + composable |
| **Node's built-in `node:test`** | Zero-dep; for simple needs |
| **Bun's built-in test** | Fast; Bun projects only |
| **Playwright** | E2E browser automation |
| **Cypress** | E2E (Playwright is winning the war in 2026) |
| **Testing Library** | DOM testing helpers (works with Jest/Vitest) |
| **MSW** (Mock Service Worker) | HTTP mocking for tests |

## 3. Jest essentials

```javascript
// math.test.js
import { add, multiply } from './math'

describe('add', () => {
  test('adds two numbers', () => {
    expect(add(2, 3)).toBe(5)
  })

  test('handles negatives', () => {
    expect(add(-1, 1)).toBe(0)
  })
})

describe('multiply', () => {
  test.each([
    [2, 3, 6],
    [0, 5, 0],
    [-2, 3, -6],
  ])('multiply(%i, %i) = %i', (a, b, expected) => {
    expect(multiply(a, b)).toBe(expected)
  })
})
```

```bash
npx jest
npx jest --coverage
npx jest --watch
```

## 4. Vitest — the modern Jest

```typescript
// math.test.ts
import { describe, test, expect } from 'vitest'
import { add } from './math'

describe('add', () => {
  test('adds two numbers', () => {
    expect(add(2, 3)).toBe(5)
  })
})
```

```bash
npx vitest
npx vitest --coverage
npx vitest --watch    # default — watch mode is the default!
```

Vitest perks:
- Native ESM + TypeScript (no Babel/SWC setup)
- Reuses Vite config (same plugins)
- Browser mode (run tests in real browser)
- UI mode (`vitest --ui`)
- ~2-5x faster than Jest

## 5. Integration tests example (Express + Supertest)

```javascript
import request from 'supertest'
import { describe, test, expect, beforeAll, afterAll } from 'vitest'
import { app, startServer, stopServer } from './app'

describe('GET /api/users', () => {
  beforeAll(() => startServer())
  afterAll(() => stopServer())

  test('returns users list', async () => {
    const res = await request(app).get('/api/users')
    expect(res.status).toBe(200)
    expect(res.body.users).toBeInstanceOf(Array)
  })
})
```

## 6. Mocking HTTP with MSW

```javascript
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { beforeAll, afterAll, afterEach, test, expect } from 'vitest'

const server = setupServer(
  http.get('https://api.example.com/users', () => {
    return HttpResponse.json([{ id: 1, name: 'Alice' }])
  }),
  http.post('https://api.example.com/users', async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json({ id: 2, ...body }, { status: 201 })
  })
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

test('fetches users', async () => {
  const r = await fetch('https://api.example.com/users')
  const users = await r.json()
  expect(users).toHaveLength(1)
})
```

## 7. E2E with Playwright

```typescript
import { test, expect } from '@playwright/test'

test('user can log in', async ({ page }) => {
  await page.goto('http://localhost:3000/login')
  await page.getByLabel('Email').fill('alice@example.com')
  await page.getByLabel('Password').fill('password')
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page).toHaveURL('/dashboard')
  await expect(page.getByText('Welcome, Alice')).toBeVisible()
})
```

```bash
npx playwright test
npx playwright test --ui          # interactive
npx playwright test --headed      # show browser
npx playwright codegen            # record interactions to generate test
```

Playwright supports Chromium, Firefox, WebKit. Cross-browser by default.

## 8. Component testing (React/Vue)

```typescript
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { test, expect } from 'vitest'
import Counter from './Counter'

test('increments on click', async () => {
  render(<Counter />)
  const button = screen.getByRole('button', { name: '+' })
  await userEvent.click(button)
  await userEvent.click(button)
  expect(screen.getByText('Count: 2')).toBeInTheDocument()
})
```

Testing Library philosophy: test as a user would (find by role/text, not by class name).

## 9. Coverage — meaningful numbers

```bash
npx vitest --coverage
```

Output:
```
File         | % Stmts | % Branch | % Funcs | % Lines
-------------|---------|----------|---------|--------
src/math.ts  |   95.45 |    83.33 |   100.0 |   95.45
src/auth.ts  |   72.00 |    66.67 |   75.00 |   72.00
```

**70-80% is the sweet spot.** Below 60% = inadequate. Above 90% = diminishing returns and brittle tests. Don't chase 100% — it leads to testing implementation details.

## 10. Snapshot testing — caution

```javascript
test('renders correctly', () => {
  const tree = renderer.create(<MyComponent />).toJSON()
  expect(tree).toMatchSnapshot()
})
```

Anti-pattern when overused: snapshots become a wall of un-reviewed text. Use for:
- Stable API responses
- Generated config files
- Visual regression sparingly

Don't use for whole component trees — review fatigue → blind "update snapshots" without reading.

## 11. Property-based testing

```javascript
import { fc, test } from '@fast-check/vitest'

test.prop([fc.integer(), fc.integer()])('add is commutative', (a, b) => {
  expect(add(a, b)).toBe(add(b, a))
})
```

`fast-check` (JS) / `Hypothesis` (Python) — generate random inputs that satisfy a property. Finds edge cases humans miss.

## 12. Quick self-check

1. What's the "Testing Trophy" and how does it differ from the test pyramid?
2. Why is Vitest displacing Jest in 2026?
3. What does MSW do?
4. Why is 100% coverage usually a bad goal?
5. What does property-based testing find that example-based doesn't?

(Answers: heavy on integration + static analysis, lighter on unit/E2E than the pyramid suggests; native ESM + TS, faster, reuses Vite config, browser mode, watch by default; mocks HTTP at the service-worker layer — your fetch calls hit the mock without code changes; leads to testing implementation details and brittle tests with diminishing returns; edge cases generated by random inputs that humans wouldn't have written as examples.)
