<script setup lang="ts">
/**
 * CourtBaseLayer.vue — Static basketball court floor SVG.
 * Renders once, never re-renders on data changes.
 *
 * viewBox="0 0 1880 500"
 * Left basket at (150, 250), right basket at (1730, 250)
 *
 * Uses CSS variables from :root for all colors.
 */
</script>

<template>
  <svg
    id="court-base"
    viewBox="0 0 1880 1000"
    preserveAspectRatio="xMidYMid meet"
    xmlns="http://www.w3.org/2000/svg"
    class="court-base"
  >
    <!-- === Floor background === -->
    <rect
      x="0" y="0"
      width="1880" height="1000"
      fill="var(--bg-court-floor, #b87c3a)"
      rx="6"
    />

    <!-- === Court outline === -->
    <rect
      x="20" y="20"
      width="1840" height="960"
      fill="none"
      stroke="var(--court-line, rgba(255,255,255,0.25))"
      stroke-width="2"
    />

    <!-- === Center line === -->
    <line
      x1="940" y1="20"
      x2="940" y2="980"
      stroke="var(--court-line, rgba(255,255,255,0.25))"
      stroke-width="2"
    />

    <!-- === Center circle === -->
    <circle
      cx="940" cy="500"
      r="120"
      fill="none"
      stroke="var(--court-line, rgba(255,255,255,0.2))"
      stroke-width="1.5"
    />
    <circle cx="940" cy="500" r="3" fill="var(--court-line, rgba(255,255,255,0.3))" />

    <!-- === Left half: three-point arc === -->
    <path
      d="M 150,320 A 476,476 0 0,1 150,680"
      fill="none"
      stroke="var(--court-line, rgba(255,255,255,0.25))"
      stroke-width="1.5"
    />
    <!-- Left three-point line baseline extensions -->
    <line x1="20" y1="320" x2="150" y2="320" stroke="var(--court-line, rgba(255,255,255,0.25))" stroke-width="1.5" />
    <line x1="20" y1="680" x2="150" y2="680" stroke="var(--court-line, rgba(255,255,255,0.25))" stroke-width="1.5" />

    <!-- === Left half: restricted area / paint === -->
    <!-- Key (lane) rectangle -->
    <rect
      x="62" y="370"
      width="176" height="260"
      fill="none"
      stroke="var(--court-line, rgba(255,255,255,0.2))"
      stroke-width="1"
    />
    <!-- Restricted arc -->
    <path
      d="M 122,590 A 35,35 0 0,1 178,590"
      fill="none"
      stroke="var(--court-line, rgba(255,255,255,0.2))"
      stroke-width="1"
    />

    <!-- === Left basket === -->
    <circle cx="150" cy="500" r="8" fill="none" stroke="var(--semantic-rim, #e74c3c)" stroke-width="2.5" />
    <circle cx="150" cy="500" r="3" fill="var(--semantic-rim, #e74c3c)" />

    <!-- === Right half: three-point arc === -->
    <path
      d="M 1730,320 A 476,476 0 0,0 1730,680"
      fill="none"
      stroke="var(--court-line, rgba(255,255,255,0.25))"
      stroke-width="1.5"
    />
    <line x1="1860" y1="320" x2="1730" y2="320" stroke="var(--court-line, rgba(255,255,255,0.25))" stroke-width="1.5" />
    <line x1="1860" y1="680" x2="1730" y2="680" stroke="var(--court-line, rgba(255,255,255,0.25))" stroke-width="1.5" />

    <!-- === Right half: restricted area / paint === -->
    <rect
      x="1642" y="370"
      width="176" height="260"
      fill="none"
      stroke="var(--court-line, rgba(255,255,255,0.2))"
      stroke-width="1"
    />
    <path
      d="M 1702,590 A 35,35 0 0,0 1758,590"
      fill="none"
      stroke="var(--court-line, rgba(255,255,255,0.2))"
      stroke-width="1"
    />

    <!-- === Right basket === -->
    <circle cx="1730" cy="500" r="8" fill="none" stroke="var(--semantic-rim, #e74c3c)" stroke-width="2.5" />
    <circle cx="1730" cy="500" r="3" fill="var(--semantic-rim, #e74c3c)" />
  </svg>
</template>

<style scoped>
.court-base {
  width: 100%;
  height: auto;
  display: block;
}
</style>
