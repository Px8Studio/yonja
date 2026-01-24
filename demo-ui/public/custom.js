// Inject PWA manifest and register a minimal service worker.
(function registerPWA() {
  try {
    const existing = document.querySelector('link[rel="manifest"]');
    if (!existing) {
      const link = document.createElement('link');
      link.rel = 'manifest';
      link.href = '/public/manifest.json';
      document.head.appendChild(link);
    }

    const isLocalhost = Boolean(
      window.location.hostname === 'localhost' ||
        window.location.hostname === '127.0.0.1'
    );
    const isSecure = window.location.protocol === 'https:' || isLocalhost;

    if ('serviceWorker' in navigator && isSecure) {
      navigator.serviceWorker
        .register('/public/sw.js')
        .catch((err) => console.warn('PWA: service worker registration failed', err));
    }
  } catch (err) {
    console.warn('PWA bootstrap failed', err);
  }
})();

// Capture native Chainlit MCP connections (from localStorage)
(function captureMCPConnections() {
  try {
    // Wait for localStorage to be populated
    const checkInterval = setInterval(() => {
      // Chainlit stores MCP connections in localStorage under key like "mcp_servers" or similar
      const keys = Object.keys(localStorage);
      const mcpKeys = keys.filter(k => k.toLowerCase().includes('mcp'));

      if (mcpKeys.length > 0) {
        const connections = {};
        mcpKeys.forEach(key => {
          try {
            const value = localStorage.getItem(key);
            connections[key] = JSON.parse(value);
          } catch (e) {
            connections[key] = value;
          }
        });

        // Store in window for backend to access
        window.__yonca_mcp_connections__ = connections;

        console.log('MCP connections captured from localStorage:', connections);
        clearInterval(checkInterval);
      }
    }, 500);

    // Stop checking after 10 seconds
    setTimeout(() => clearInterval(checkInterval), 10000);
  } catch (err) {
    console.warn('MCP connection capture failed', err);
  }
})();

// MCP status badge (non-interactive indicator with hover tooltip)
(function mcpStatusBadge() {
  const ENDPOINT = '/ui/mcp/status?profile=agent';
  const REFRESH_MS = 30000;

  function createBadge() {
    const existing = document.querySelector('.yonca-mcp-badge');
    if (existing) return existing;

    const badge = document.createElement('div');
    badge.className = 'yonca-mcp-badge';
    badge.innerHTML = `
      <div class="yonca-mcp-dot"></div>
      <span class="yonca-mcp-label">MCP</span>
      <div class="yonca-mcp-tooltip">Loading MCP status…</div>
    `;

    // Attach near input container when available
    const attach = () => {
      const container = document.querySelector('.cl-input-container');
      if (container && !badge.isConnected) {
        container.appendChild(badge);
      }
    };
    attach();
    const observer = new MutationObserver(attach);
    observer.observe(document.body, { childList: true, subtree: true });

    // If the composer never appears, surface a console hint for debugging
    setTimeout(() => {
      if (!badge.isConnected) {
        console.warn('MCP badge: composer not found; badge not attached');
      }
    }, 2000);
    return badge;
  }

  async function fetchStatus() {
    try {
      const res = await fetch(ENDPOINT, { cache: 'no-store' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn('MCP badge status fetch failed', err);
      return { error: String(err) };
    }
  }

  function render(status) {
    const badge = createBadge();
    const dot = badge.querySelector('.yonca-mcp-dot');
    const tooltip = badge.querySelector('.yonca-mcp-tooltip');

    if (status.error) {
      dot.className = 'yonca-mcp-dot error';
      tooltip.textContent = `MCP error: ${status.error}`;
      return;
    }

    const servers = status.servers || {};
    const anyOffline = Object.values(servers).some((s) => s.status !== 'online');
    const hasConnectors = Boolean(status.connectors_enabled);

    dot.className = 'yonca-mcp-dot ' + (hasConnectors ? (anyOffline ? 'warn' : 'ok') : 'off');

    const lines = [];
    lines.push(`Profile: ${status.profile || 'agent'}`);
    if (!hasConnectors) {
      lines.push('Connectors disabled for this mode.');
    }

    Object.entries(servers).forEach(([name, info]) => {
      const icon = info.status === 'online' ? '🟢' : info.status === 'offline' ? '🔴' : '🟡';
      lines.push(`${icon} ${name} (${info.status})`);
    });

    if (status.tools && status.tools.length) {
      lines.push('Tools:');
      status.tools.slice(0, 5).forEach((t) => lines.push(`• ${t.name}`));
      if (status.tools.length > 5) {
        lines.push(`…+${status.tools.length - 5} more`);
      }
    }

    tooltip.innerHTML = lines.join('<br>');
  }

  async function tick() {
    const status = await fetchStatus();
    render(status);
  }

  // Initial and refresh
  setTimeout(tick, 1000);
  setInterval(tick, REFRESH_MS);
})();
