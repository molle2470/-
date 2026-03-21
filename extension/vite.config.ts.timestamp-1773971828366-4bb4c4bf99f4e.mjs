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
    "https://sell.smartstore.naver.com/*"
  ],
  background: {
    service_worker: "src/background/index.ts",
    type: "module"
  },
  content_scripts: [
    {
      matches: ["https://www.musinsa.com/app/goods/*"],
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
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiLCAibWFuaWZlc3QuanNvbiJdLAogICJzb3VyY2VzQ29udGVudCI6IFsiY29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2Rpcm5hbWUgPSBcIkM6XFxcXFVzZXJzXFxcXHRqZHFsXFxcXHduc3JsZlxcXFxhZHZhbmNlZC1oYXJuZXNzLW1haW5cXFxcZXh0ZW5zaW9uXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ZpbGVuYW1lID0gXCJDOlxcXFxVc2Vyc1xcXFx0amRxbFxcXFx3bnNybGZcXFxcYWR2YW5jZWQtaGFybmVzcy1tYWluXFxcXGV4dGVuc2lvblxcXFx2aXRlLmNvbmZpZy50c1wiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9pbXBvcnRfbWV0YV91cmwgPSBcImZpbGU6Ly8vQzovVXNlcnMvdGpkcWwvd25zcmxmL2FkdmFuY2VkLWhhcm5lc3MtbWFpbi9leHRlbnNpb24vdml0ZS5jb25maWcudHNcIjsvLyBleHRlbnNpb24vdml0ZS5jb25maWcudHNcbmltcG9ydCB7IGRlZmluZUNvbmZpZyB9IGZyb20gXCJ2aXRlXCJcbmltcG9ydCByZWFjdCBmcm9tIFwiQHZpdGVqcy9wbHVnaW4tcmVhY3RcIlxuaW1wb3J0IHsgY3J4IH0gZnJvbSBcIkBjcnhqcy92aXRlLXBsdWdpblwiXG5pbXBvcnQgbWFuaWZlc3QgZnJvbSBcIi4vbWFuaWZlc3QuanNvblwiXG5cbmV4cG9ydCBkZWZhdWx0IGRlZmluZUNvbmZpZyh7XG4gIHBsdWdpbnM6IFtcbiAgICByZWFjdCgpLFxuICAgIGNyeCh7IG1hbmlmZXN0IH0pLFxuICBdLFxufSlcbiIsICJ7XG4gIFwibWFuaWZlc3RfdmVyc2lvblwiOiAzLFxuICBcIm5hbWVcIjogXCJcdUMxOENcdUMyRjEgXHVDNUI0XHVDMkRDXHVDMkE0XHVEMTM0XHVEMkI4XCIsXG4gIFwidmVyc2lvblwiOiBcIjEuMC4wXCIsXG4gIFwiZGVzY3JpcHRpb25cIjogXCJcdUJCMzRcdUM3QUNcdUFDRTAgXHVBRDZDXHVCOUU0XHVCMzAwXHVENTg5IFx1QzBDMVx1RDQ4OCBcdUMyMThcdUM5RDEgXHVDNzc1XHVDMkE0XHVEMTUwXHVDMTU4XCIsXG4gIFwicGVybWlzc2lvbnNcIjogW1wiYWxhcm1zXCIsIFwic3RvcmFnZVwiLCBcIm5vdGlmaWNhdGlvbnNcIiwgXCJ0YWJzXCJdLFxuICBcImhvc3RfcGVybWlzc2lvbnNcIjogW1xuICAgIFwiaHR0cHM6Ly8qLm11c2luc2EuY29tLypcIixcbiAgICBcImh0dHBzOi8vYXBpLm11c2luc2EuY29tLypcIixcbiAgICBcImh0dHA6Ly9sb2NhbGhvc3Q6MjgwODAvKlwiLFxuICAgIFwiaHR0cHM6Ly9zZWxsLnNtYXJ0c3RvcmUubmF2ZXIuY29tLypcIlxuICBdLFxuICBcImJhY2tncm91bmRcIjoge1xuICAgIFwic2VydmljZV93b3JrZXJcIjogXCJzcmMvYmFja2dyb3VuZC9pbmRleC50c1wiLFxuICAgIFwidHlwZVwiOiBcIm1vZHVsZVwiXG4gIH0sXG4gIFwiY29udGVudF9zY3JpcHRzXCI6IFtcbiAgICB7XG4gICAgICBcIm1hdGNoZXNcIjogW1wiaHR0cHM6Ly93d3cubXVzaW5zYS5jb20vYXBwL2dvb2RzLypcIl0sXG4gICAgICBcImpzXCI6IFtcInNyYy9jb250ZW50L211c2luc2EtaW50ZXJjZXB0b3IudHNcIl0sXG4gICAgICBcInJ1bl9hdFwiOiBcImRvY3VtZW50X3N0YXJ0XCJcbiAgICB9LFxuICAgIHtcbiAgICAgIFwibWF0Y2hlc1wiOiBbXG4gICAgICAgIFwiaHR0cHM6Ly93d3cubXVzaW5zYS5jb20vYXBwL2dvb2RzLypcIixcbiAgICAgICAgXCJodHRwczovL3d3dy5tdXNpbnNhLmNvbS9wcm9kdWN0cy8qXCJcbiAgICAgIF0sXG4gICAgICBcImpzXCI6IFtcInNyYy9jb250ZW50L211c2luc2EtcHJvZHVjdC50c3hcIl0sXG4gICAgICBcInJ1bl9hdFwiOiBcImRvY3VtZW50X2lkbGVcIlxuICAgIH0sXG4gICAge1xuICAgICAgXCJtYXRjaGVzXCI6IFtcImh0dHBzOi8vc2VsbC5zbWFydHN0b3JlLm5hdmVyLmNvbS8qXCJdLFxuICAgICAgXCJqc1wiOiBbXCJzcmMvY29udGVudC9uYXZlci1zZW8tYXV0b2ZpbGwudHNcIl0sXG4gICAgICBcInJ1bl9hdFwiOiBcImRvY3VtZW50X2lkbGVcIlxuICAgIH1cbiAgXSxcbiAgXCJhY3Rpb25cIjoge1xuICAgIFwiZGVmYXVsdF9wb3B1cFwiOiBcInNyYy9wb3B1cC9pbmRleC5odG1sXCJcbiAgfVxufVxuIl0sCiAgIm1hcHBpbmdzIjogIjtBQUNBLFNBQVMsb0JBQW9CO0FBQzdCLE9BQU8sV0FBVztBQUNsQixTQUFTLFdBQVc7OztBQ0hwQjtBQUFBLEVBQ0Usa0JBQW9CO0FBQUEsRUFDcEIsTUFBUTtBQUFBLEVBQ1IsU0FBVztBQUFBLEVBQ1gsYUFBZTtBQUFBLEVBQ2YsYUFBZSxDQUFDLFVBQVUsV0FBVyxpQkFBaUIsTUFBTTtBQUFBLEVBQzVELGtCQUFvQjtBQUFBLElBQ2xCO0FBQUEsSUFDQTtBQUFBLElBQ0E7QUFBQSxJQUNBO0FBQUEsRUFDRjtBQUFBLEVBQ0EsWUFBYztBQUFBLElBQ1osZ0JBQWtCO0FBQUEsSUFDbEIsTUFBUTtBQUFBLEVBQ1Y7QUFBQSxFQUNBLGlCQUFtQjtBQUFBLElBQ2pCO0FBQUEsTUFDRSxTQUFXLENBQUMscUNBQXFDO0FBQUEsTUFDakQsSUFBTSxDQUFDLG9DQUFvQztBQUFBLE1BQzNDLFFBQVU7QUFBQSxJQUNaO0FBQUEsSUFDQTtBQUFBLE1BQ0UsU0FBVztBQUFBLFFBQ1Q7QUFBQSxRQUNBO0FBQUEsTUFDRjtBQUFBLE1BQ0EsSUFBTSxDQUFDLGlDQUFpQztBQUFBLE1BQ3hDLFFBQVU7QUFBQSxJQUNaO0FBQUEsSUFDQTtBQUFBLE1BQ0UsU0FBVyxDQUFDLHFDQUFxQztBQUFBLE1BQ2pELElBQU0sQ0FBQyxtQ0FBbUM7QUFBQSxNQUMxQyxRQUFVO0FBQUEsSUFDWjtBQUFBLEVBQ0Y7QUFBQSxFQUNBLFFBQVU7QUFBQSxJQUNSLGVBQWlCO0FBQUEsRUFDbkI7QUFDRjs7O0FEakNBLElBQU8sc0JBQVEsYUFBYTtBQUFBLEVBQzFCLFNBQVM7QUFBQSxJQUNQLE1BQU07QUFBQSxJQUNOLElBQUksRUFBRSwyQkFBUyxDQUFDO0FBQUEsRUFDbEI7QUFDRixDQUFDOyIsCiAgIm5hbWVzIjogW10KfQo=
