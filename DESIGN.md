# DESIGN.md — CoffeeMind GT

Dirección visual y tokens del frontend React. Fuente única para colores, tipografía, espaciados y patrones de componente. Acompaña a [GUIDE.md](GUIDE.md) (plan funcional); este archivo cubre solo lo visual.

Referencia de inspiración: landing de Brainfish (capturada 2026-05-24). Se toma de ahí la energía *playful + profesional*, el sistema de tarjetas con ilustración, y la estratificación de fondos por sección. Se adapta a contexto cafetalero guatemalteco (altiplano, grano, finca) reemplazando el motivo marino por uno de altura.

---

## 1. Principios

| # | Principio | Aplicación |
|---|-----------|------------|
| 1 | **Claridad sobre decoración** | Cada tarjeta o gráfico debe responder una pregunta del caficultor; ilustración acompaña, no compite. |
| 2 | **Energía cálida, no sterile** | Paleta saturada moderada, no la frialdad SaaS estándar; refleja contexto agrícola guatemalteco. |
| 3 | **Stratificación por sección** | Fondos de color delimitan dominios (CSP, Bayesiana, ML, MDP); el usuario siempre sabe en qué módulo está. |
| 4 | **Datos legibles primero** | Tipografía generosa, contraste AA mínimo, números tabulares para tablas/métricas. |

---

## 2. Paleta

### 2.1 Tokens base

| Token | Hex | Uso |
|---|---|---|
| `--cm-sky` | `#BEE3F2` | Fondo de hero y sección Knowledge / CSP |
| `--cm-sky-deep` | `#3F7BB8` | Fondo de sección ML (transición a profundidad) |
| `--cm-teal-deep` | `#1B4A6B` | Fondo de footer y sección MDP (mayor "depth") |
| `--cm-cream` | `#FFF6D6` | Tarjetas destacadas, callouts |
| `--cm-mint` | `#CDE9C9` | Sección Distribution / Bayesian, fondo de paso intermedio |
| `--cm-coral` | `#FF8A6B` | CTA primario, acento de alerta positiva |
| `--cm-coffee` | `#5C3A1E` | Texto sobre fondos claros, ilustración (grano) |
| `--cm-coffee-soft` | `#8A6648` | Texto secundario |
| `--cm-leaf` | `#3F8A3E` | Tag de variedad, "OK" en métricas |
| `--cm-rust` | `#C84A2E` | Riesgo alto de roya, errores |
| `--cm-bg` | `#FAF7F0` | Fondo neutro de aplicación |
| `--cm-ink` | `#13212E` | Texto principal de alto contraste |

### 2.2 Mapeo semántico por módulo

| Módulo | Fondo de sección | Acento |
|---|---|---|
| CSP (asignación variedades) | `--cm-sky` | `--cm-leaf` |
| Bayesian (riesgo roya) | `--cm-mint` | `--cm-rust` |
| ML (predicción cultivo) | `--cm-sky-deep` | `--cm-cream` |
| MDP (política mensual) | `--cm-teal-deep` | `--cm-coral` |

Regla: ningún componente arrastra el color de un módulo a otro. Si una tarjeta de CSP aparece en la página de MDP, usa el fondo del módulo anfitrión.

---

## 3. Tipografía

| Rol | Familia | Tamaño | Peso | Tracking |
|---|---|---|---|---|
| Display (H1 hero) | Inter | 56–72 px (clamp) | 800 | -0.02em |
| Section title (H2) | Inter | 36–44 px | 700 | -0.015em |
| Subtitle (H3) | Inter | 22–26 px | 600 | -0.01em |
| Body | Inter | 16 px | 400 | 0 |
| Caption / chip | Inter | 13 px | 500 | 0.02em |
| Mono (números, JSON) | JetBrains Mono | 14 px | 500 | 0 |

Reglas:
- Tabular nums (`font-variant-numeric: tabular-nums`) obligatorio en columnas numéricas, métricas y tablas.
- Línea base de cuerpo: `line-height: 1.55`. Títulos: `1.15`.
- Una sola familia sans (Inter) en toda la app; sin display fonts decorativas.

---

## 4. Espaciado, radios, sombras

### 4.1 Escala de espaciado (rem, base 16 px)

`0.25 — 0.5 — 0.75 — 1 — 1.5 — 2 — 3 — 4 — 6 — 8`

Sección a sección: padding vertical mínimo `4rem` (mobile) / `6rem` (desktop).

### 4.2 Radios

| Token | Valor | Uso |
|---|---|---|
| `--r-sm` | 8 px | Chips, inputs |
| `--r-md` | 16 px | Botones, tarjetas pequeñas |
| `--r-lg` | 24 px | Tarjetas de contenido, módulos |
| `--r-xl` | 32 px | Hero panels, callouts grandes |

### 4.3 Sombras

| Token | Valor |
|---|---|
| `--shadow-card` | `0 1px 2px rgba(19,33,46,.06), 0 8px 24px rgba(19,33,46,.08)` |
| `--shadow-pop` | `0 2px 6px rgba(19,33,46,.10), 0 16px 40px rgba(19,33,46,.14)` |

Sombra siempre con tinte `--cm-ink`, nunca negro puro.

---

## 5. Componentes

### 5.1 Tarjeta de módulo

```
┌──────────────────────────────┐
│  [icono]  Título del módulo  │   radius: --r-lg
│  Subtítulo breve             │   bg: blanco sobre fondo de sección
│                              │   shadow: --shadow-card
│  Contenido / gráfico         │   padding: 1.5rem 2rem
│                              │
│  [chip] [chip] [chip]        │
└──────────────────────────────┘
```

### 5.2 Botón primario

- Fondo `--cm-coral`, texto `--cm-ink`, radio `--r-md`, padding `0.75rem 1.5rem`.
- Hover: oscurece 8 %, levanta sombra a `--shadow-pop`.
- Sin gradientes, sin bordes.

### 5.3 Botón secundario

- Fondo transparente, borde 1.5 px `--cm-ink`, texto `--cm-ink`. Mismo radio y padding.

### 5.4 Chip / tag

- Fondo pastel del módulo (sky / mint / cream), texto `--cm-coffee`, radio `--r-sm`, padding `0.25rem 0.75rem`, peso 500.
- Variantes semánticas: `chip--ok` (`--cm-leaf`), `chip--warn` (`--cm-cream`), `chip--risk` (`--cm-rust`).

### 5.5 Métrica destacada

```
+275%        ← display weight, color --cm-leaf o --cm-rust según signo
Resolución roya
en sombra 70 %  ← caption, --cm-coffee-soft
```

### 5.6 Sección con fondo

- Full-bleed (`100vw`), padding vertical de escala (§4.1).
- Contenido centrado en contenedor `max-width: 1120px`.
- Transiciones entre secciones: borde superior con curva SVG suave (onda de altiplano) — *sin* degradados duros.

---

## 6. Layout

- Grid de página: 12 columnas, gutter `1.5rem`, margen lateral `1.5rem` (mobile) / `2.5rem` (≥1024 px).
- Breakpoints: `sm 640` · `md 768` · `lg 1024` · `xl 1280`.
- Hero: una columna centrada, ancho máximo `720px` para el texto.
- Tarjetas de módulo en `lg+`: 2 columnas. En `md`: stack vertical.

---

## 7. Ilustración e iconografía

- Mascota: **grano de café antropomorfo** (reemplaza al pez de la referencia). Mismo lenguaje: 2D flat, contorno suave, ojos expresivos, paleta de la app.
- Decoración de fondo: hojas de cafeto, montañas estilizadas, nubes — todo en SVG, opacidad 30–60 %.
- Iconos UI: line-icons 1.5 px stroke, color `--cm-ink` o `--cm-coffee`. Familia única (sugerido: Lucide).
- Prohibido: emoji decorativo, iconos 3D, sombras drop en iconos.

---

## 8. Accesibilidad

- Contraste mínimo AA (4.5:1) para texto de cuerpo; AAA (7:1) deseable para métricas.
- Pares verificados:
  - `--cm-ink` sobre `--cm-sky` → 8.9:1 ✓
  - `--cm-ink` sobre `--cm-cream` → 13.4:1 ✓
  - `--cm-cream` sobre `--cm-sky-deep` → 6.1:1 ✓
  - `--cm-coffee` sobre `--cm-mint` → 7.2:1 ✓
- Estado de foco: outline 2 px `--cm-coral` con offset 2 px.
- Color nunca es el único canal de información (los riesgos llevan icono + texto, no solo rojo).

---

## 9. Anti-patrones

- No usar fondos diagonales o degradados ruidosos entre secciones.
- No mezclar `--cm-rust` con `--cm-coral` en la misma vista (se leen como el mismo color).
- No usar sombras negras puras.
- No introducir una segunda familia tipográfica decorativa.
- No animar gráficos de datos al primer render (los caficultores escanean cifras, no esperan transiciones).

---

## 10. Implementación

Tokens viven en [frontend/src/styles.css](frontend/src/styles.css) como variables CSS (`:root { --cm-sky: …; }`). Componentes React consumen vía clases utilitarias o `style` inline solo cuando el valor es dinámico (color por módulo). Sin librería UI externa por ahora — patrón a mano sobre Vite + React.
