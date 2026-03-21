// vite.config.ts
import { defineConfig } from "file:///C:/Users/tjdql/wnsrlf/advanced-harness-main/extension/node_modules/.pnpm/vite@5.4.21/node_modules/vite/dist/node/index.js";
import react from "file:///C:/Users/tjdql/wnsrlf/advanced-harness-main/extension/node_modules/.pnpm/@vitejs+plugin-react@4.7.0_vite@5.4.21/node_modules/@vitejs/plugin-react/dist/index.js";
import { crx } from "file:///C:/Users/tjdql/wnsrlf/advanced-harness-main/extension/node_modules/.pnpm/@crxjs+vite-plugin@2.4.0_vite@5.4.21/node_modules/@crxjs/vite-plugin/dist/index.mjs";

// manifest.json
var manifest_default = {
  manifest_version: 3,
  name: "\uC18C\uC2F1 \uC5B4\uC2DC\uC2A4\uD134\uD2B8",
  version: "1.0.0",
  description: "\uBB34\uC7AC\uACE0 \uAD6C\uB9E4\uB300\uD589 \uC0C1\uD488 \uC218\uC9D1 \uC775\uC2A4\uD150\uC158",
  permissions: ["alarms", "storage", "notifications", "tabs"],
  host_permissions: [
    "https://*.musinsa.com/*",
    "https://api.musinsa.com/*",
    "http://localhost:28080/*",
    "http://localhost:28081/*",
    "https://sell.smartstore.naver.com/*"
  ],
  background: {
    service_worker: "src/background/index.ts",
    type: "module"
  },
  content_scripts: [
    {
      matches: [
        "https://www.musinsa.com/app/goods/*",
        "https://www.musinsa.com/products/*"
      ],
      js: ["src/content/musinsa-fetch-interceptor.ts"],
      run_at: "document_start",
      world: "MAIN"
    },
    {
      matches: [
        "https://www.musinsa.com/app/goods/*",
        "https://www.musinsa.com/products/*"
      ],
      js: ["src/content/musinsa-interceptor.ts"],
      run_at: "document_start"
    },
    {
      matches: [
        "https://www.musinsa.com/app/goods/*",
        "https://www.musinsa.com/products/*"
      ],
      js: ["src/content/musinsa-product.tsx"],
      run_at: "document_idle"
    },
    {
      matches: ["https://sell.smartstore.naver.com/*"],
      js: ["src/content/naver-seo-autofill.ts"],
      run_at: "document_idle"
    }
  ],
  action: {
    default_popup: "src/popup/index.html"
  }
};

// vite.config.ts
var vite_config_default = defineConfig({
  plugins: [
    react(),
    crx({ manifest: manifest_default })
  ]
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiLCAibWFuaWZlc3QuanNvbiJdLAogICJzb3VyY2VzQ29udGVudCI6IFsiY29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2Rpcm5hbWUgPSBcIkM6XFxcXFVzZXJzXFxcXHRqZHFsXFxcXHduc3JsZlxcXFxhZHZhbmNlZC1oYXJuZXNzLW1haW5cXFxcZXh0ZW5zaW9uXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ZpbGVuYW1lID0gXCJDOlxcXFxVc2Vyc1xcXFx0amRxbFxcXFx3bnNybGZcXFxcYWR2YW5jZWQtaGFybmVzcy1tYWluXFxcXGV4dGVuc2lvblxcXFx2aXRlLmNvbmZpZy50c1wiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9pbXBvcnRfbWV0YV91cmwgPSBcImZpbGU6Ly8vQzovVXNlcnMvdGpkcWwvd25zcmxmL2FkdmFuY2VkLWhhcm5lc3MtbWFpbi9leHRlbnNpb24vdml0ZS5jb25maWcudHNcIjsvLyBleHRlbnNpb24vdml0ZS5jb25maWcudHNcbmltcG9ydCB7IGRlZmluZUNvbmZpZyB9IGZyb20gXCJ2aXRlXCJcbmltcG9ydCByZWFjdCBmcm9tIFwiQHZpdGVqcy9wbHVnaW4tcmVhY3RcIlxuaW1wb3J0IHsgY3J4IH0gZnJvbSBcIkBjcnhqcy92aXRlLXBsdWdpblwiXG5pbXBvcnQgbWFuaWZlc3QgZnJvbSBcIi4vbWFuaWZlc3QuanNvblwiXG5cbmV4cG9ydCBkZWZhdWx0IGRlZmluZUNvbmZpZyh7XG4gIHBsdWdpbnM6IFtcbiAgICByZWFjdCgpLFxuICAgIGNyeCh7IG1hbmlmZXN0IH0pLFxuICBdLFxufSlcbiIsICJ7XG4gIFwibWFuaWZlc3RfdmVyc2lvblwiOiAzLFxuICBcIm5hbWVcIjogXCJcdUMxOENcdUMyRjEgXHVDNUI0XHVDMkRDXHVDMkE0XHVEMTM0XHVEMkI4XCIsXG4gIFwidmVyc2lvblwiOiBcIjEuMC4wXCIsXG4gIFwiZGVzY3JpcHRpb25cIjogXCJcdUJCMzRcdUM3QUNcdUFDRTAgXHVBRDZDXHVCOUU0XHVCMzAwXHVENTg5IFx1QzBDMVx1RDQ4OCBcdUMyMThcdUM5RDEgXHVDNzc1XHVDMkE0XHVEMTUwXHVDMTU4XCIsXG4gIFwicGVybWlzc2lvbnNcIjogW1wiYWxhcm1zXCIsIFwic3RvcmFnZVwiLCBcIm5vdGlmaWNhdGlvbnNcIiwgXCJ0YWJzXCJdLFxuICBcImhvc3RfcGVybWlzc2lvbnNcIjogW1xuICAgIFwiaHR0cHM6Ly8qLm11c2luc2EuY29tLypcIixcbiAgICBcImh0dHBzOi8vYXBpLm11c2luc2EuY29tLypcIixcbiAgICBcImh0dHA6Ly9sb2NhbGhvc3Q6MjgwODAvKlwiLFxuICAgIFwiaHR0cDovL2xvY2FsaG9zdDoyODA4MS8qXCIsXG4gICAgXCJodHRwczovL3NlbGwuc21hcnRzdG9yZS5uYXZlci5jb20vKlwiXG4gIF0sXG4gIFwiYmFja2dyb3VuZFwiOiB7XG4gICAgXCJzZXJ2aWNlX3dvcmtlclwiOiBcInNyYy9iYWNrZ3JvdW5kL2luZGV4LnRzXCIsXG4gICAgXCJ0eXBlXCI6IFwibW9kdWxlXCJcbiAgfSxcbiAgXCJjb250ZW50X3NjcmlwdHNcIjogW1xuICAgIHtcbiAgICAgIFwibWF0Y2hlc1wiOiBbXG4gICAgICAgIFwiaHR0cHM6Ly93d3cubXVzaW5zYS5jb20vYXBwL2dvb2RzLypcIixcbiAgICAgICAgXCJodHRwczovL3d3dy5tdXNpbnNhLmNvbS9wcm9kdWN0cy8qXCJcbiAgICAgIF0sXG4gICAgICBcImpzXCI6IFtcInNyYy9jb250ZW50L211c2luc2EtZmV0Y2gtaW50ZXJjZXB0b3IudHNcIl0sXG4gICAgICBcInJ1bl9hdFwiOiBcImRvY3VtZW50X3N0YXJ0XCIsXG4gICAgICBcIndvcmxkXCI6IFwiTUFJTlwiXG4gICAgfSxcbiAgICB7XG4gICAgICBcIm1hdGNoZXNcIjogW1xuICAgICAgICBcImh0dHBzOi8vd3d3Lm11c2luc2EuY29tL2FwcC9nb29kcy8qXCIsXG4gICAgICAgIFwiaHR0cHM6Ly93d3cubXVzaW5zYS5jb20vcHJvZHVjdHMvKlwiXG4gICAgICBdLFxuICAgICAgXCJqc1wiOiBbXCJzcmMvY29udGVudC9tdXNpbnNhLWludGVyY2VwdG9yLnRzXCJdLFxuICAgICAgXCJydW5fYXRcIjogXCJkb2N1bWVudF9zdGFydFwiXG4gICAgfSxcbiAgICB7XG4gICAgICBcIm1hdGNoZXNcIjogW1xuICAgICAgICBcImh0dHBzOi8vd3d3Lm11c2luc2EuY29tL2FwcC9nb29kcy8qXCIsXG4gICAgICAgIFwiaHR0cHM6Ly93d3cubXVzaW5zYS5jb20vcHJvZHVjdHMvKlwiXG4gICAgICBdLFxuICAgICAgXCJqc1wiOiBbXCJzcmMvY29udGVudC9tdXNpbnNhLXByb2R1Y3QudHN4XCJdLFxuICAgICAgXCJydW5fYXRcIjogXCJkb2N1bWVudF9pZGxlXCJcbiAgICB9LFxuICAgIHtcbiAgICAgIFwibWF0Y2hlc1wiOiBbXCJodHRwczovL3NlbGwuc21hcnRzdG9yZS5uYXZlci5jb20vKlwiXSxcbiAgICAgIFwianNcIjogW1wic3JjL2NvbnRlbnQvbmF2ZXItc2VvLWF1dG9maWxsLnRzXCJdLFxuICAgICAgXCJydW5fYXRcIjogXCJkb2N1bWVudF9pZGxlXCJcbiAgICB9XG4gIF0sXG4gIFwiYWN0aW9uXCI6IHtcbiAgICBcImRlZmF1bHRfcG9wdXBcIjogXCJzcmMvcG9wdXAvaW5kZXguaHRtbFwiXG4gIH1cbn1cbiJdLAogICJtYXBwaW5ncyI6ICI7QUFDQSxTQUFTLG9CQUFvQjtBQUM3QixPQUFPLFdBQVc7QUFDbEIsU0FBUyxXQUFXOzs7QUNIcEI7QUFBQSxFQUNFLGtCQUFvQjtBQUFBLEVBQ3BCLE1BQVE7QUFBQSxFQUNSLFNBQVc7QUFBQSxFQUNYLGFBQWU7QUFBQSxFQUNmLGFBQWUsQ0FBQyxVQUFVLFdBQVcsaUJBQWlCLE1BQU07QUFBQSxFQUM1RCxrQkFBb0I7QUFBQSxJQUNsQjtBQUFBLElBQ0E7QUFBQSxJQUNBO0FBQUEsSUFDQTtBQUFBLElBQ0E7QUFBQSxFQUNGO0FBQUEsRUFDQSxZQUFjO0FBQUEsSUFDWixnQkFBa0I7QUFBQSxJQUNsQixNQUFRO0FBQUEsRUFDVjtBQUFBLEVBQ0EsaUJBQW1CO0FBQUEsSUFDakI7QUFBQSxNQUNFLFNBQVc7QUFBQSxRQUNUO0FBQUEsUUFDQTtBQUFBLE1BQ0Y7QUFBQSxNQUNBLElBQU0sQ0FBQywwQ0FBMEM7QUFBQSxNQUNqRCxRQUFVO0FBQUEsTUFDVixPQUFTO0FBQUEsSUFDWDtBQUFBLElBQ0E7QUFBQSxNQUNFLFNBQVc7QUFBQSxRQUNUO0FBQUEsUUFDQTtBQUFBLE1BQ0Y7QUFBQSxNQUNBLElBQU0sQ0FBQyxvQ0FBb0M7QUFBQSxNQUMzQyxRQUFVO0FBQUEsSUFDWjtBQUFBLElBQ0E7QUFBQSxNQUNFLFNBQVc7QUFBQSxRQUNUO0FBQUEsUUFDQTtBQUFBLE1BQ0Y7QUFBQSxNQUNBLElBQU0sQ0FBQyxpQ0FBaUM7QUFBQSxNQUN4QyxRQUFVO0FBQUEsSUFDWjtBQUFBLElBQ0E7QUFBQSxNQUNFLFNBQVcsQ0FBQyxxQ0FBcUM7QUFBQSxNQUNqRCxJQUFNLENBQUMsbUNBQW1DO0FBQUEsTUFDMUMsUUFBVTtBQUFBLElBQ1o7QUFBQSxFQUNGO0FBQUEsRUFDQSxRQUFVO0FBQUEsSUFDUixlQUFpQjtBQUFBLEVBQ25CO0FBQ0Y7OztBRDlDQSxJQUFPLHNCQUFRLGFBQWE7QUFBQSxFQUMxQixTQUFTO0FBQUEsSUFDUCxNQUFNO0FBQUEsSUFDTixJQUFJLEVBQUUsMkJBQVMsQ0FBQztBQUFBLEVBQ2xCO0FBQ0YsQ0FBQzsiLAogICJuYW1lcyI6IFtdCn0K
