# 51 — VueJS 3 Deep

> Nana's IT Fundamentals course uses Vue 3 for the demo "Teamable" frontend. Vue 2 has been EOL since Dec 2023; everything here is Vue 3.

## 1. The Vue 3 mental model

```
<template> — declarative HTML with directives + bindings
<script setup> — reactive state + functions
<style scoped> — CSS scoped to this component
```

Vue is **template-first**; React is **JS-first**. Vue compiles templates to render functions.

## 2. The minimal Vue 3 component

```vue
<script setup>
import { ref, computed, onMounted } from 'vue'

const count = ref(0)
const doubled = computed(() => count.value * 2)

function increment() {
  count.value++
}

onMounted(() => {
  console.log('mounted; count is', count.value)
})
</script>

<template>
  <button @click="increment">Click me</button>
  <p>Count: {{ count }}, Doubled: {{ doubled }}</p>
</template>

<style scoped>
button { background: blue; color: white; }
</style>
```

`ref` creates a reactive value. Inside `<script>`, access via `.value`. Inside `<template>`, just use the name (Vue unwraps).

## 3. Composition API vs Options API

### Composition API (`<script setup>`) — modern, preferred
```vue
<script setup>
import { ref, computed } from 'vue'
const count = ref(0)
const doubled = computed(() => count.value * 2)
</script>
```

### Options API — legacy but still works
```vue
<script>
export default {
  data() { return { count: 0 } },
  computed: { doubled() { return this.count * 2 } },
}
</script>
```

**Use Composition API for new code.** Composition handles complex logic better (reusability via composables; better TypeScript).

## 4. Reactivity primitives

```javascript
import { ref, reactive, computed, watch, watchEffect } from 'vue'

// ref — wraps any value
const count = ref(0)
count.value = 1   // .value to access

// reactive — for objects/arrays (proxy-based)
const user = reactive({ name: 'Alice', age: 30 })
user.age = 31    // no .value

// computed — derived value, cached
const fullName = computed(() => `${user.name} (${user.age})`)

// watch — react to specific changes
watch(count, (newVal, oldVal) => {
  console.log(`count: ${oldVal} → ${newVal}`)
})

// watchEffect — runs immediately + tracks deps automatically
watchEffect(() => {
  console.log('count is', count.value)
})
```

## 5. Directives

```vue
<template>
  <!-- text -->
  <p>{{ message }}</p>
  <p v-text="message"></p>

  <!-- HTML (sanitize first!) -->
  <p v-html="trustedHTML"></p>

  <!-- attribute binding -->
  <img :src="imageUrl" :alt="caption" />

  <!-- event handlers -->
  <button @click="handleClick">Click</button>
  <input @input="onInput" />

  <!-- two-way binding -->
  <input v-model="searchText" />

  <!-- conditional -->
  <p v-if="loggedIn">Welcome</p>
  <p v-else-if="loading">Loading...</p>
  <p v-else>Please log in</p>

  <!-- list rendering -->
  <ul>
    <li v-for="(item, i) in items" :key="item.id">{{ i }} - {{ item.name }}</li>
  </ul>

  <!-- show/hide (toggle display) -->
  <div v-show="visible">...</div>
</template>
```

`v-if` removes/adds to DOM; `v-show` toggles CSS `display`. Use `v-show` when toggling frequently.

## 6. Props + Emits (parent → child → parent)

```vue
<!-- Child.vue -->
<script setup>
const props = defineProps({
  message: { type: String, required: true },
  count: { type: Number, default: 0 },
})

const emit = defineEmits(['update', 'close'])

function handle() {
  emit('update', { newValue: 42 })
}
</script>

<template>
  <p>{{ message }} - {{ count }}</p>
  <button @click="handle">Update</button>
  <button @click="emit('close')">Close</button>
</template>
```

```vue
<!-- Parent.vue -->
<Child :message="hello" :count="5" @update="onUpdate" @close="onClose" />
```

## 7. Slots (component composition)

```vue
<!-- Card.vue -->
<template>
  <div class="card">
    <header><slot name="header" /></header>
    <main><slot /></main>
    <footer><slot name="footer" /></footer>
  </div>
</template>

<!-- Parent -->
<Card>
  <template #header><h2>Title</h2></template>
  <p>Main content</p>
  <template #footer><button>OK</button></template>
</Card>
```

## 8. Composables (the React-hooks equivalent)

```javascript
// composables/useFetch.js
import { ref, onMounted } from 'vue'

export function useFetch(url) {
  const data = ref(null)
  const loading = ref(true)
  const error = ref(null)

  onMounted(async () => {
    try {
      const r = await fetch(url)
      data.value = await r.json()
    } catch (e) {
      error.value = e
    } finally {
      loading.value = false
    }
  })

  return { data, loading, error }
}
```

```vue
<script setup>
import { useFetch } from '@/composables/useFetch'
const { data, loading, error } = useFetch('/api/users')
</script>
```

## 9. Pinia — state management

```javascript
// stores/counter.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useCounterStore = defineStore('counter', () => {
  const count = ref(0)
  const doubled = computed(() => count.value * 2)
  function increment() { count.value++ }
  return { count, doubled, increment }
})
```

```vue
<script setup>
import { useCounterStore } from '@/stores/counter'
const counter = useCounterStore()
</script>

<template>
  <p>{{ counter.count }} (doubled: {{ counter.doubled }})</p>
  <button @click="counter.increment">+</button>
</template>
```

Pinia replaced Vuex as official state management in 2022.

## 10. Vue Router 4

```javascript
// router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: HomeView },
    { path: '/users/:id', component: () => import('@/views/UserView.vue') },
  ],
})
export default router
```

```vue
<template>
  <RouterLink to="/">Home</RouterLink>
  <RouterView />
</template>
```

## 11. Nuxt 3 / Nuxt 4 (SSR + meta-framework)

Nuxt is to Vue what Next.js is to React. File-based routing, SSR, auto-imports, modules:

```bash
npx nuxi@latest init my-app
cd my-app
npm install
npm run dev
```

`pages/` directory becomes routes. `composables/` auto-imported. `server/api/` for backend endpoints.

## 12. Quick self-check

1. What's the difference between `ref` and `reactive` in Vue 3?
2. When use `v-if` vs `v-show`?
3. What does `<script setup>` give you over a regular `<script>`?
4. What replaced Vuex as official state management?
5. What does Nuxt add over plain Vue?

(Answers: ref wraps any value (use .value), reactive is proxy-based for objects/arrays (direct access); v-if adds/removes from DOM (use for rare toggles), v-show toggles CSS display (use for frequent toggles); concise syntax, no `return`, auto-exposes top-level bindings to template, better TypeScript; Pinia (official since 2022); SSR, file-based routing, auto-imports, server API, module system.)
