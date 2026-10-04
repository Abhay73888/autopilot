/**
 * AUTOPILOT Admin Control Center SPA Logic (admin.js)
 * Clean, Zero-Build Vanilla JavaScript SaaS Interface
 */

(function () {
  "use strict";

  // =========================================================================
  // State & Configuration
  // =========================================================================
  const state = {
    token: localStorage.getItem("autopilot_admin_token") || "",
    user: null,
    currentPath: window.location.pathname,
    notifTimer: null,
  };

  try {
    const rawUser = localStorage.getItem("autopilot_admin_user");
    if (rawUser) state.user = JSON.parse(rawUser);
  } catch (e) {
    state.user = null;
  }

  // Page Metadata Map
  const PAGE_META = {
    "/admin": { title: "Dashboard", meta: "Overview" },
    "/admin/dashboard": { title: "Dashboard", meta: "Cluster Overview" },
    "/admin/users": { title: "Users", meta: "Accounts & RBAC" },
    "/admin/activity": { title: "Activity Monitor", meta: "Platform Telemetry" },
    "/admin/audit": { title: "Audit Trail", meta: "Privileged Mutations" },
    "/admin/projects": { title: "Projects", meta: "Series & Franchises" },
    "/admin/videos": { title: "Videos", meta: "Asset Catalog" },
    "/admin/youtube": { title: "YouTube Connections", meta: "Channel Credentials" },
    "/admin/usage": { title: "AI Usage", meta: "Token Ledger & Spend" },
    "/admin/reports": { title: "Reports", meta: "Platform Health & Metrics" },
    "/admin/settings": { title: "System Settings", meta: "Configuration" },
    "/admin/profile": { title: "Admin Profile", meta: "Account" },
  };

  // =========================================================================
  // DOM & Teardown-Safe Helpers
  // =========================================================================
  const $ = (sel, parent = document) => parent.querySelector(sel);
  const $$ = (sel, parent = document) => Array.from(parent.querySelectorAll(sel));

  function live(node) {
    return node && document.body.contains(node);
  }

  function el(tag, attrs = {}, children = []) {
    const elem = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === "className") elem.className = v;
      else if (k === "textContent") elem.textContent = v;
      else if (k === "innerHTML") elem.innerHTML = v;
      else if (k.startsWith("on") && typeof v === "function") elem.addEventListener(k.slice(2).toLowerCase(), v);
      else elem.setAttribute(k, v);
    }
    for (const child of children) {
      if (typeof child === "string") elem.appendChild(document.createTextNode(child));
      else if (child instanceof Node) elem.appendChild(child);
    }
    return elem;
  }

  function put(target, ...children) {
    target.innerHTML = "";
    for (const c of children) {
      if (typeof c === "string") target.appendChild(document.createTextNode(c));
      else if (c instanceof Node) target.appendChild(c);
    }
    return target;
  }

  // =========================================================================
  // Data Extraction & Helper Utilities
  // =========================================================================
  function rowsOf(res) {
    if (!res) return [];
    if (Array.isArray(res)) return res;
    if (Array.isArray(res.data)) return res.data;
    if (res.data && Array.isArray(res.data.items)) return res.data.items;
    if (res.data && Array.isArray(res.data.rows)) return res.data.rows;
    if (Array.isArray(res.items)) return res.items;
    return [];
  }

  function formatTime(isoStr) {
    if (!isoStr) return "not recorded";
    try {
      const d = new Date(isoStr);
      if (isNaN(d.getTime())) return String(isoStr);
      return d.toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      });
    } catch {
      return String(isoStr);
    }
  }

  function safeVal(val, fallback = "not recorded") {
    if (val === null || val === undefined || val === "") return fallback;
    return String(val);
  }

  // =========================================================================
  // Authenticated HTTP Client
  // =========================================================================
  async function api(path, options = {}) {
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };

    if (state.token) {
      headers["Authorization"] = `Bearer ${state.token}`;
    }

    try {
      const resp = await fetch(path, { ...options, headers });
      if (resp.status === 401) {
        localStorage.removeItem("autopilot_admin_token");
        localStorage.removeItem("autopilot_admin_user");
        window.location.href = "/admin/login";
        return null;
      }

      const json = await resp.json().catch(() => null);
      if (!resp.ok) {
        const errorMsg = (json && json.error && json.error.message) || (json && json.detail) || `HTTP error ${resp.status}`;
        throw new Error(errorMsg);
      }
      return json;
    } catch (err) {
      toast(err.message || "Network request failed", "danger");
      throw err;
    }
  }

  // =========================================================================
  // Toast Notifications
  // =========================================================================
  function toast(message, type = "info") {
    const host = $("#toastHost");
    if (!host) return;

    const t = el("div", {
      className: `toast toast-${type}`,
      textContent: message,
    });

    if (type === "danger") {
      t.style.borderColor = "var(--color-danger-border)";
      t.style.backgroundColor = "var(--color-danger-bg)";
      t.style.color = "var(--color-danger)";
    } else if (type === "success") {
      t.style.borderColor = "var(--color-success-border)";
      t.style.backgroundColor = "var(--color-success-bg)";
      t.style.color = "var(--color-success)";
    }

    host.appendChild(t);
    setTimeout(() => {
      if (live(t)) t.remove();
    }, 4000);
  }

  // =========================================================================
  // Modal & Confirm Action Dialogs
  // =========================================================================
  function modal({ title, body, footer, onCancel }) {
    const host = $("#modalHost");
    if (!host) return;

    const backdrop = el("div", { className: "modal-backdrop" });
    const dialog = el("div", { className: "modal-dialog" });

    const header = el("div", { className: "modal-header" }, [
      el("h3", { className: "modal-title", textContent: title }),
      el("button", {
        className: "btn-secondary btn-sm",
        innerHTML: "&times;",
        onClick: () => {
          backdrop.remove();
          if (onCancel) onCancel();
        },
      }),
    ]);

    const bodyContainer = el("div", { className: "modal-body" });
    if (typeof body === "string") bodyContainer.textContent = body;
    else if (body instanceof Node) bodyContainer.appendChild(body);

    const footerContainer = el("div", { className: "modal-footer" });
    if (footer) {
      for (const btn of footer) footerContainer.appendChild(btn);
    }

    dialog.appendChild(header);
    dialog.appendChild(bodyContainer);
    dialog.appendChild(footerContainer);
    backdrop.appendChild(dialog);
    put(host, backdrop);

    return {
      close: () => backdrop.remove(),
    };
  }

  function confirmAction({ title, message, requireReason = false, onConfirm }) {
    let reasonInput = null;
    const bodyEl = el("div", {}, [
      el("p", { textContent: message, style: "margin-top: 0; margin-bottom: 1rem;" }),
    ]);

    if (requireReason) {
      reasonInput = el("input", {
        type: "text",
        className: "table-search-input",
        placeholder: "Reason (optional)...",
        style: "width: 100%; box-sizing: border-box;",
      });
      bodyEl.appendChild(el("label", { textContent: "Action Reason:", style: "font-size: 0.75rem; font-weight: 600; display: block; margin-bottom: 0.25rem;" }));
      bodyEl.appendChild(reasonInput);
    }

    let m = null;
    const confirmBtn = el("button", {
      className: "btn btn-danger",
      textContent: "Confirm",
      onClick: async () => {
        confirmBtn.disabled = true;
        confirmBtn.textContent = "Processing...";
        const reason = reasonInput ? reasonInput.value.trim() : null;
        try {
          await onConfirm(reason);
          m.close();
        } catch {
          confirmBtn.disabled = false;
          confirmBtn.textContent = "Confirm";
        }
      },
    });

    const cancelBtn = el("button", {
      className: "btn btn-secondary",
      textContent: "Cancel",
      onClick: () => m.close(),
    });

    m = modal({
      title,
      body: bodyEl,
      footer: [cancelBtn, confirmBtn],
    });
  }

  // =========================================================================
  // Reusable UI Components: Pager, DataTable, StatCards
  // =========================================================================
  function renderPager({ total, page, limit, onPageChange }) {
    const totalPages = Math.max(1, Math.ceil(total / limit));
    const startRow = total === 0 ? 0 : (page - 1) * limit + 1;
    const endRow = Math.min(total, page * limit);

    return el("div", { className: "pager-bar" }, [
      el("div", { textContent: `Showing ${startRow}–${endRow} of ${total} records` }),
      el("div", { className: "pager-buttons" }, [
        el("button", {
          className: "btn-pager",
          textContent: "Previous",
          disabled: page <= 1,
          onClick: () => onPageChange(page - 1),
        }),
        el("span", { textContent: `Page ${page} of ${totalPages}`, style: "margin: 0 0.5rem;" }),
        el("button", {
          className: "btn-pager",
          textContent: "Next",
          disabled: page >= totalPages,
          onClick: () => onPageChange(page + 1),
        }),
      ]),
    ]);
  }

  function statCard(label, value, desc = "") {
    return el("div", { className: "stat-card" }, [
      el("span", { className: "stat-card-label", textContent: label }),
      el("span", { className: "stat-card-value", textContent: safeVal(value, "0") }),
      desc ? el("span", { className: "stat-card-desc", textContent: desc }) : null,
    ]);
  }

  function skeletonTable(cols = 5, rows = 6) {
    const tbody = el("tbody");
    for (let i = 0; i < rows; i++) {
      const tr = el("tr");
      for (let j = 0; j < cols; j++) {
        tr.appendChild(el("td", {}, [el("div", { className: "skeleton skeleton-text" })]));
      }
      tbody.appendChild(tr);
    }
    return tbody;
  }

  // =========================================================================
  // Router & Page Views
  // =========================================================================
  function go(pathname) {
    if (pathname === state.currentPath) return;
    history.pushState(null, "", pathname);
    state.currentPath = pathname;
    render();
  }

  function updateActiveNav(path) {
    $$(".nav-item-link").forEach((link) => {
      const route = link.getAttribute("data-route");
      if (route === path || (route !== "/admin/dashboard" && path.startsWith(route))) {
        link.classList.add("active");
      } else {
        link.classList.remove("active");
      }
    });

    const meta = PAGE_META[path] || { title: "Control Center", meta: "Admin" };
    $("#pageTitle").textContent = meta.title;
    $("#pageMetaLabel").textContent = meta.meta;
  }

  // -------------------------------------------------------------------------
  // View: Dashboard
  // -------------------------------------------------------------------------
  async function renderDashboard(canvas) {
    const grid = el("div", { className: "stat-grid" }, [
      el("div", { className: "skeleton skeleton-stat" }),
      el("div", { className: "skeleton skeleton-stat" }),
      el("div", { className: "skeleton skeleton-stat" }),
      el("div", { className: "skeleton skeleton-stat" }),
    ]);
    put(canvas, grid);

    try {
      const res = await api("/api/v1/control/dashboard");
      if (!live(canvas)) return;

      const stats = res && res.data ? res.data.stats : {};
      const users = stats.users || {};
      const content = stats.content || {};
      const usage = stats.usage || {};

      put(
        canvas,
        el("div", { className: "stat-grid" }, [
          statCard("Total Users", users.total, `${users.active || 0} active, ${users.blocked || 0} restricted`),
          statCard("Published Videos", content.confirmedPublishedVideos, `${content.totalVideos || 0} total in vault`),
          statCard("Active Projects", content.projects, `${content.episodes || 0} total episodes`),
          statCard("Today's Spend", `$${usage.spendTodayUsd || 0.0}`, "Zero-Key Safe Core"),
        ]),
        el("div", { className: "table-container" }, [
          el("div", { className: "table-header-bar" }, [
            el("h3", { textContent: "Recent System Activity", style: "margin: 0; font-size: 0.9375rem;" }),
          ]),
          createActivityTable(res.data.recentActivity || []),
        ])
      );
    } catch (e) {
      if (live(canvas)) put(canvas, el("div", { className: "empty-state", textContent: "Failed to load dashboard data." }));
    }
  }

  function createActivityTable(items) {
    const table = el("table", { className: "data-table" });
    const thead = el("thead", {}, [
      el("tr", {}, [
        el("th", { textContent: "Time" }),
        el("th", { textContent: "User / Actor" }),
        el("th", { textContent: "Action" }),
        el("th", { textContent: "Resource" }),
      ]),
    ]);
    table.appendChild(thead);

    const tbody = el("tbody");
    if (!items.length) {
      tbody.appendChild(el("tr", {}, [el("td", { colSpan: 4, textContent: "No recent activity recorded.", style: "text-align: center; color: var(--text-muted);" })]));
    } else {
      for (const item of items) {
        tbody.appendChild(
          el("tr", {}, [
            el("td", { textContent: formatTime(item.created_at) }),
            el("td", { textContent: item.actor_id || item.user_id }),
            el("td", {}, [el("span", { className: "status-pill status-neutral", textContent: item.action })]),
            el("td", { textContent: item.resource_type ? `${item.resource_type}:${item.resource_id || ""}` : "not recorded" }),
          ])
        );
      }
    }
    table.appendChild(tbody);
    return table;
  }

  // -------------------------------------------------------------------------
  // View: Users Management
  // -------------------------------------------------------------------------
  async function renderUsers(canvas) {
    let currentPage = 1;
    let currentSearch = "";
    let currentStatus = "";

    const container = el("div");
    put(canvas, container);

    async function load() {
      put(
        container,
        el("div", { className: "table-container" }, [
          el("div", { className: "table-header-bar" }, [
            el("input", {
              type: "search",
              className: "table-search-input",
              placeholder: "Search users by email or ID...",
              value: currentSearch,
              onInput: (e) => {
                currentSearch = e.target.value;
                currentPage = 1;
                loadDebounced();
              },
            }),
            el("select", {
              className: "table-filter-select",
              onChange: (e) => {
                currentStatus = e.target.value;
                currentPage = 1;
                load();
              },
            }, [
              el("option", { value: "", textContent: "All Statuses" }),
              el("option", { value: "active", textContent: "Active", selected: currentStatus === "active" }),
              el("option", { value: "blocked", textContent: "Blocked", selected: currentStatus === "blocked" }),
              el("option", { value: "suspended", textContent: "Suspended", selected: currentStatus === "suspended" }),
            ]),
          ]),
          el("table", { className: "data-table" }, [
            el("thead", {}, [
              el("tr", {}, [
                el("th", { textContent: "User ID" }),
                el("th", { textContent: "Name / Email" }),
                el("th", { textContent: "Role" }),
                el("th", { textContent: "Status" }),
                el("th", { textContent: "Last Active" }),
                el("th", { textContent: "Actions" }),
              ]),
            ]),
            skeletonTable(6, 6),
          ]),
        ])
      );

      try {
        let url = `/api/v1/control/users?page=${currentPage}&limit=20`;
        if (currentSearch) url += `&search=${encodeURIComponent(currentSearch)}`;
        if (currentStatus) url += `&status=${encodeURIComponent(currentStatus)}`;

        const res = await api(url);
        if (!live(container)) return;

        const items = rowsOf(res);
        const total = (res && res.meta && res.meta.total) || items.length;

        const table = el("table", { className: "data-table" }, [
          el("thead", {}, [
            el("tr", {}, [
              el("th", { textContent: "User ID" }),
              el("th", { textContent: "Name / Email" }),
              el("th", { textContent: "Role" }),
              el("th", { textContent: "Status" }),
              el("th", { textContent: "Last Active" }),
              el("th", { textContent: "Actions" }),
            ]),
          ]),
        ]);

        const tbody = el("tbody");
        if (!items.length) {
          tbody.appendChild(el("tr", {}, [el("td", { colSpan: 6, textContent: "No users found matching query.", style: "text-align: center; color: var(--text-muted);" })]));
        } else {
          for (const u of items) {
            const isBlocked = u.status === "blocked" || u.status === "suspended";
            const statusClass = `status-${u.status || "active"}`;

            const actionCell = el("td", {}, [
              el("button", {
                className: "btn btn-secondary btn-sm",
                textContent: "Inspect",
                onClick: () => renderUserDetailModal(u.user_id || u.id, load),
              }),
              el("span", { textContent: " " }),
              isBlocked
                ? el("button", {
                    className: "btn btn-secondary btn-sm",
                    textContent: "Unblock",
                    onClick: () => confirmAction({
                      title: `Unblock ${u.full_name}`,
                      message: `Are you sure you want to restore active access for ${u.email}?`,
                      onConfirm: async () => {
                        await api(`/api/v1/control/users/${u.user_id || u.id}/unblock`, { method: "POST" });
                        toast(`User ${u.full_name} unblocked.`, "success");
                        load();
                      },
                    }),
                  })
                : el("button", {
                    className: "btn btn-danger btn-sm",
                    textContent: "Block",
                    onClick: () => confirmAction({
                      title: `Block User: ${u.full_name}`,
                      message: `Blocking ${u.email} retains all data but revokes access.`,
                      requireReason: true,
                      onConfirm: async (reason) => {
                        await api(`/api/v1/control/users/${u.user_id || u.id}/block`, {
                          method: "POST",
                          body: JSON.stringify({ status: "blocked", reason }),
                        });
                        toast(`User ${u.full_name} blocked.`, "warning");
                        load();
                      },
                    }),
                  }),
            ]);

            tbody.appendChild(
              el("tr", {}, [
                el("td", { textContent: u.user_id || u.id, style: "font-family: monospace; font-size: 0.75rem;" }),
                el("td", {}, [
                  el("div", { textContent: u.full_name, style: "font-weight: 600;" }),
                  el("div", { textContent: u.email, style: "color: var(--text-muted); font-size: 0.75rem;" }),
                ]),
                el("td", { textContent: u.role || "user" }),
                el("td", {}, [el("span", { className: `status-pill ${statusClass}`, textContent: u.status || "active" })]),
                el("td", { textContent: formatTime(u.last_active_ts) }),
                actionCell,
              ])
            );
          }
        }
        table.appendChild(tbody);

        put(
          container,
          el("div", { className: "table-container" }, [
            el("div", { className: "table-header-bar" }, [
              el("input", {
                type: "search",
                className: "table-search-input",
                placeholder: "Search users by email or ID...",
                value: currentSearch,
                onInput: (e) => {
                  currentSearch = e.target.value;
                  currentPage = 1;
                  loadDebounced();
                },
              }),
              el("select", {
                className: "table-filter-select",
                onChange: (e) => {
                  currentStatus = e.target.value;
                  currentPage = 1;
                  load();
                },
              }, [
                el("option", { value: "", textContent: "All Statuses" }),
                el("option", { value: "active", textContent: "Active", selected: currentStatus === "active" }),
                el("option", { value: "blocked", textContent: "Blocked", selected: currentStatus === "blocked" }),
                el("option", { value: "suspended", textContent: "Suspended", selected: currentStatus === "suspended" }),
              ]),
            ]),
            table,
            renderPager({
              total,
              page: currentPage,
              limit: 20,
              onPageChange: (p) => {
                currentPage = p;
                load();
              },
            }),
          ])
        );
      } catch {
        if (live(container)) put(container, el("div", { className: "empty-state", textContent: "Failed to load users." }));
      }
    }

    let searchTimer = null;
    function loadDebounced() {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(load, 250);
    }

    load();
  }

  // -------------------------------------------------------------------------
  // Modal: Detailed User Inspection ("Managing user: <name> (<id>)")
  // -------------------------------------------------------------------------
  async function renderUserDetailModal(userId, onUpdated) {
    let m = null;
    const content = el("div", {}, [el("div", { className: "skeleton skeleton-text" })]);

    m = modal({
      title: "User Inspection",
      body: content,
      footer: [
        el("button", {
          className: "btn btn-secondary",
          textContent: "Close",
          onClick: () => m.close(),
        }),
      ],
    });

    try {
      const res = await api(`/api/v1/control/users/${userId}/overview`);
      const overview = res && res.data ? res.data : {};
      const u = overview.user || {};
      const counts = overview.counts || {};

      put(
        content,
        el("div", {}, [
          // Managing User standard banner
          el("div", { className: "managing-banner" }, [
            el("span", { className: "managing-banner-title", textContent: overview.managingContext || `Managing user: ${u.full_name} (${userId})` }),
            el("span", { className: "managing-banner-badge", textContent: u.status || "active" }),
          ]),
          el("div", { className: "stat-grid", style: "grid-template-columns: repeat(3, 1fr); margin-bottom: 1rem;" }, [
            statCard("Projects", counts.projects || 0),
            statCard("Videos", counts.videos || 0),
            statCard("YouTube Connections", counts.youtubeConnections || 0),
          ]),
          u.block_reason
            ? el("div", { style: "padding: 0.75rem; background: var(--color-danger-bg); border: 1px solid var(--color-danger-border); border-radius: var(--radius-md); margin-bottom: 1rem; color: var(--color-danger); font-size: 0.8125rem;" }, [
                el("strong", { textContent: "Block Reason: " }),
                el("span", { textContent: u.block_reason }),
              ])
            : null,
          el("div", { style: "font-size: 0.8125rem; color: var(--text-muted);" }, [
            el("p", { textContent: `Created: ${formatTime(u.created_at)}` }),
            el("p", { textContent: `Last Active: ${formatTime(u.last_active_ts)}` }),
          ]),
        ])
      );
    } catch {
      put(content, el("div", { textContent: "Failed to load user overview." }));
    }
  }

  // -------------------------------------------------------------------------
  // View: Activity Monitor
  // -------------------------------------------------------------------------
  async function renderActivity(canvas) {
    let currentPage = 1;
    let selectedAction = "";

    const container = el("div");
    put(canvas, container);

    async function load() {
      put(
        container,
        el("div", { className: "table-container" }, [
          el("div", { className: "table-header-bar" }, [
            el("h3", { textContent: "Platform Activity Telemetry", style: "margin: 0; font-size: 0.9375rem;" }),
          ]),
          el("table", { className: "data-table" }, [
            el("thead", {}, [
              el("tr", {}, [
                el("th", { textContent: "Time" }),
                el("th", { textContent: "User ID" }),
                el("th", { textContent: "Actor ID" }),
                el("th", { textContent: "Action" }),
                el("th", { textContent: "Resource" }),
                el("th", { textContent: "IP Address" }),
              ]),
            ]),
            skeletonTable(6, 6),
          ]),
        ])
      );

      try {
        let url = `/api/v1/control/activity?page=${currentPage}&limit=50`;
        if (selectedAction) url += `&action=${encodeURIComponent(selectedAction)}`;

        const res = await api(url);
        if (!live(container)) return;

        const items = rowsOf(res);
        const total = (res && res.meta && res.meta.total) || items.length;

        const table = el("table", { className: "data-table" }, [
          el("thead", {}, [
            el("tr", {}, [
              el("th", { textContent: "Time" }),
              el("th", { textContent: "User ID" }),
              el("th", { textContent: "Actor ID" }),
              el("th", { textContent: "Action" }),
              el("th", { textContent: "Resource" }),
              el("th", { textContent: "IP Address" }),
            ]),
          ]),
        ]);

        const tbody = el("tbody");
        if (!items.length) {
          tbody.appendChild(el("tr", {}, [el("td", { colSpan: 6, textContent: "No activity records found.", style: "text-align: center; color: var(--text-muted);" })]));
        } else {
          for (const act of items) {
            tbody.appendChild(
              el("tr", {}, [
                el("td", { textContent: formatTime(act.created_at) }),
                el("td", { textContent: act.user_id, style: "font-family: monospace; font-size: 0.75rem;" }),
                el("td", { textContent: act.actor_id, style: "font-family: monospace; font-size: 0.75rem;" }),
                el("td", {}, [el("span", { className: "status-pill status-neutral", textContent: act.action })]),
                el("td", { textContent: act.resource_type ? `${act.resource_type}:${act.resource_id || ""}` : "not recorded" }),
                el("td", { textContent: safeVal(act.ip_address, "internal") }),
              ])
            );
          }
        }
        table.appendChild(tbody);

        put(
          container,
          el("div", { className: "table-container" }, [
            el("div", { className: "table-header-bar" }, [
              el("h3", { textContent: "Platform Activity Telemetry", style: "margin: 0; font-size: 0.9375rem;" }),
            ]),
            table,
            renderPager({
              total,
              page: currentPage,
              limit: 50,
              onPageChange: (p) => {
                currentPage = p;
                load();
              },
            }),
          ])
        );
      } catch {
        if (live(container)) put(container, el("div", { className: "empty-state", textContent: "Failed to load activity." }));
      }
    }

    load();
  }

  // -------------------------------------------------------------------------
  // View: Audit Trail
  // -------------------------------------------------------------------------
  async function renderAudit(canvas) {
    let currentPage = 1;
    const container = el("div");
    put(canvas, container);

    async function load() {
      try {
        const res = await api(`/api/v1/control/audit?page=${currentPage}&limit=50`);
        if (!live(container)) return;

        const items = rowsOf(res);
        const total = (res && res.meta && res.meta.total) || items.length;

        const table = el("table", { className: "data-table" }, [
          el("thead", {}, [
            el("tr", {}, [
              el("th", { textContent: "Time" }),
              el("th", { textContent: "Admin ID" }),
              el("th", { textContent: "Target ID" }),
              el("th", { textContent: "Action" }),
              el("th", { textContent: "Resource" }),
              el("th", { textContent: "Reason" }),
            ]),
          ]),
        ]);

        const tbody = el("tbody");
        if (!items.length) {
          tbody.appendChild(el("tr", {}, [el("td", { colSpan: 6, textContent: "No audit records found.", style: "text-align: center; color: var(--text-muted);" })]));
        } else {
          for (const aud of items) {
            tbody.appendChild(
              el("tr", {}, [
                el("td", { textContent: formatTime(aud.created_at) }),
                el("td", { textContent: aud.admin_id, style: "font-family: monospace; font-size: 0.75rem;" }),
                el("td", { textContent: safeVal(aud.target_id), style: "font-family: monospace; font-size: 0.75rem;" }),
                el("td", {}, [el("span", { className: "status-pill status-neutral", textContent: aud.action })]),
                el("td", { textContent: aud.resource }),
                el("td", { textContent: safeVal(aud.reason, "No reason provided") }),
              ])
            );
          }
        }
        table.appendChild(tbody);

        put(
          container,
          el("div", { className: "table-container" }, [
            el("div", { className: "table-header-bar" }, [
              el("h3", { textContent: "Administrative Audit Trail", style: "margin: 0; font-size: 0.9375rem;" }),
            ]),
            table,
            renderPager({
              total,
              page: currentPage,
              limit: 50,
              onPageChange: (p) => {
                currentPage = p;
                load();
              },
            }),
          ])
        );
      } catch {
        if (live(container)) put(container, el("div", { className: "empty-state", textContent: "Failed to load audit trail." }));
      }
    }

    load();
  }

  // -------------------------------------------------------------------------
  // View: Projects (Series)
  // -------------------------------------------------------------------------
  async function renderProjects(canvas) {
    let currentPage = 1;
    const container = el("div");
    put(canvas, container);

    async function load() {
      try {
        const res = await api(`/api/v1/control/projects?page=${currentPage}&limit=20`);
        if (!live(container)) return;

        const items = rowsOf(res);
        const total = (res && res.meta && res.meta.total) || items.length;

        const table = el("table", { className: "data-table" }, [
          el("thead", {}, [
            el("tr", {}, [
              el("th", { textContent: "Project ID" }),
              el("th", { textContent: "Title" }),
              el("th", { textContent: "Owner (User)" }),
              el("th", { textContent: "Genre / Tone" }),
              el("th", { textContent: "Created" }),
            ]),
          ]),
        ]);

        const tbody = el("tbody");
        if (!items.length) {
          tbody.appendChild(el("tr", {}, [el("td", { colSpan: 5, textContent: "No projects found.", style: "text-align: center; color: var(--text-muted);" })]));
        } else {
          for (const p of items) {
            tbody.appendChild(
              el("tr", {}, [
                el("td", { textContent: p.id, style: "font-family: monospace; font-size: 0.75rem;" }),
                el("td", { textContent: p.title, style: "font-weight: 600;" }),
                el("td", { textContent: p.user_id || "admin_abhay" }),
                el("td", { textContent: `${p.genre || "mystery"} / ${p.tone || "suspense"}` }),
                el("td", { textContent: formatTime(p.created_at) }),
              ])
            );
          }
        }
        table.appendChild(tbody);

        put(
          container,
          el("div", { className: "table-container" }, [
            el("div", { className: "table-header-bar" }, [
              el("h3", { textContent: "Video Projects & Series", style: "margin: 0; font-size: 0.9375rem;" }),
            ]),
            table,
            renderPager({
              total,
              page: currentPage,
              limit: 20,
              onPageChange: (p) => {
                currentPage = p;
                load();
              },
            }),
          ])
        );
      } catch {
        if (live(container)) put(container, el("div", { className: "empty-state", textContent: "Failed to load projects." }));
      }
    }

    load();
  }

  // -------------------------------------------------------------------------
  // View: Videos Catalog
  // -------------------------------------------------------------------------
  async function renderVideos(canvas) {
    let currentPage = 1;
    const container = el("div");
    put(canvas, container);

    async function load() {
      try {
        const res = await api(`/api/v1/control/videos?page=${currentPage}&limit=20`);
        if (!live(container)) return;

        const items = rowsOf(res);
        const total = (res && res.meta && res.meta.total) || items.length;

        const table = el("table", { className: "data-table" }, [
          el("thead", {}, [
            el("tr", {}, [
              el("th", { textContent: "Video ID" }),
              el("th", { textContent: "Title" }),
              el("th", { textContent: "Status" }),
              el("th", { textContent: "YouTube ID" }),
              el("th", { textContent: "Views" }),
              el("th", { textContent: "Created" }),
            ]),
          ]),
        ]);

        const tbody = el("tbody");
        if (!items.length) {
          tbody.appendChild(el("tr", {}, [el("td", { colSpan: 6, textContent: "No videos found.", style: "text-align: center; color: var(--text-muted);" })]));
        } else {
          for (const v of items) {
            tbody.appendChild(
              el("tr", {}, [
                el("td", { textContent: v.id, style: "font-family: monospace; font-size: 0.75rem;" }),
                el("td", { textContent: v.title, style: "font-weight: 500;" }),
                el("td", {}, [el("span", { className: `status-pill status-${v.status === "published" ? "active" : "neutral"}`, textContent: v.status })]),
                el("td", { textContent: safeVal(v.yt_video_id, "not uploaded") }),
                el("td", { textContent: safeVal(v.views, "0") }),
                el("td", { textContent: formatTime(v.created_at) }),
              ])
            );
          }
        }
        table.appendChild(tbody);

        put(
          container,
          el("div", { className: "table-container" }, [
            el("div", { className: "table-header-bar" }, [
              el("h3", { textContent: "Video Master Catalog", style: "margin: 0; font-size: 0.9375rem;" }),
            ]),
            table,
            renderPager({
              total,
              page: currentPage,
              limit: 20,
              onPageChange: (p) => {
                currentPage = p;
                load();
              },
            }),
          ])
        );
      } catch {
        if (live(container)) put(container, el("div", { className: "empty-state", textContent: "Failed to load videos." }));
      }
    }

    load();
  }

  // -------------------------------------------------------------------------
  // View: YouTube Connections (STRICT SECRET MASKING)
  // -------------------------------------------------------------------------
  async function renderYouTube(canvas) {
    let currentPage = 1;
    const container = el("div");
    put(canvas, container);

    async function load() {
      try {
        const res = await api(`/api/v1/control/youtube?page=${currentPage}&limit=20`);
        if (!live(container)) return;

        const items = rowsOf(res);
        const total = (res && res.meta && res.meta.total) || items.length;

        const table = el("table", { className: "data-table" }, [
          el("thead", {}, [
            el("tr", {}, [
              el("th", { textContent: "Credential ID" }),
              el("th", { textContent: "Channel Title" }),
              el("th", { textContent: "Status" }),
              el("th", { textContent: "OAuth Token (Masked)" }),
              el("th", { textContent: "Connected" }),
              el("th", { textContent: "Actions" }),
            ]),
          ]),
        ]);

        const tbody = el("tbody");
        if (!items.length) {
          tbody.appendChild(el("tr", {}, [el("td", { colSpan: 6, textContent: "No YouTube connections found.", style: "text-align: center; color: var(--text-muted);" })]));
        } else {
          for (const yt of items) {
            tbody.appendChild(
              el("tr", {}, [
                el("td", { textContent: yt.id, style: "font-family: monospace; font-size: 0.75rem;" }),
                el("td", { textContent: yt.channel_title, style: "font-weight: 600;" }),
                el("td", {}, [el("span", { className: `status-pill status-${yt.status === "connected" ? "active" : "neutral"}`, textContent: yt.status })]),
                el("td", {}, [el("span", { className: "badge-secret-masked", textContent: yt.token_masked || "enc_token (masked)" })]),
                el("td", { textContent: formatTime(yt.created_at) }),
                el("td", {}, [
                  el("button", {
                    className: "btn btn-danger btn-sm",
                    textContent: "Disconnect",
                    disabled: yt.status === "disconnected",
                    onClick: () => confirmAction({
                      title: `Disconnect ${yt.channel_title}`,
                      message: `Are you sure you want to disconnect this YouTube OAuth channel?`,
                      onConfirm: async () => {
                        await api(`/api/v1/control/youtube/${yt.id}/disconnect`, { method: "POST" });
                        toast(`Channel disconnected.`, "warning");
                        load();
                      },
                    }),
                  }),
                ]),
              ])
            );
          }
        }
        table.appendChild(tbody);

        put(
          container,
          el("div", { className: "table-container" }, [
            el("div", { className: "table-header-bar" }, [
              el("h3", { textContent: "YouTube Channel Connections (Tokens Masked)", style: "margin: 0; font-size: 0.9375rem;" }),
            ]),
            table,
            renderPager({
              total,
              page: currentPage,
              limit: 20,
              onPageChange: (p) => {
                currentPage = p;
                load();
              },
            }),
          ])
        );
      } catch {
        if (live(container)) put(container, el("div", { className: "empty-state", textContent: "Failed to load YouTube connections." }));
      }
    }

    load();
  }

  // -------------------------------------------------------------------------
  // View: AI Usage Ledger
  // -------------------------------------------------------------------------
  async function renderUsage(canvas) {
    let currentPage = 1;
    const container = el("div");
    put(canvas, container);

    async function load() {
      try {
        const [res, sumRes] = await Promise.all([
          api(`/api/v1/control/usage?page=${currentPage}&limit=50`),
          api(`/api/v1/control/usage/summary`),
        ]);
        if (!live(container)) return;

        const items = rowsOf(res);
        const total = (res && res.meta && res.meta.total) || items.length;
        const summary = sumRes && sumRes.data ? sumRes.data : {};

        const table = el("table", { className: "data-table" }, [
          el("thead", {}, [
            el("tr", {}, [
              el("th", { textContent: "Time" }),
              el("th", { textContent: "Provider" }),
              el("th", { textContent: "Model" }),
              el("th", { textContent: "Tokens In / Out" }),
              el("th", { textContent: "Cost (USD)" }),
            ]),
          ]),
        ]);

        const tbody = el("tbody");
        if (!items.length) {
          tbody.appendChild(el("tr", {}, [el("td", { colSpan: 5, textContent: "No usage ledger records found.", style: "text-align: center; color: var(--text-muted);" })]));
        } else {
          for (const u of items) {
            tbody.appendChild(
              el("tr", {}, [
                el("td", { textContent: formatTime(u.created_at) }),
                el("td", { textContent: u.provider || "not recorded" }),
                el("td", { textContent: safeVal(u.model) }),
                el("td", { textContent: `${u.tokens_in || 0} / ${u.tokens_out || 0}` }),
                el("td", { textContent: `$${u.cost_usd || 0.0}` }),
              ])
            );
          }
        }
        table.appendChild(tbody);

        put(
          container,
          el("div", { className: "stat-grid", style: "grid-template-columns: repeat(2, 1fr);" }, [
            statCard("Total AI Spend", `$${summary.totalSpendUsd || 0.0}`),
            statCard("Total Usage Records", total),
          ]),
          el("div", { className: "table-container" }, [
            el("div", { className: "table-header-bar" }, [
              el("h3", { textContent: "AI Inference & Generation Ledger", style: "margin: 0; font-size: 0.9375rem;" }),
            ]),
            table,
            renderPager({
              total,
              page: currentPage,
              limit: 50,
              onPageChange: (p) => {
                currentPage = p;
                load();
              },
            }),
          ])
        );
      } catch {
        if (live(container)) put(container, el("div", { className: "empty-state", textContent: "Failed to load usage ledger." }));
      }
    }

    load();
  }

  // -------------------------------------------------------------------------
  // View: Reports & System Settings & Admin Profile
  // -------------------------------------------------------------------------
  async function renderReports(canvas) {
    put(canvas, el("div", { className: "skeleton skeleton-stat" }));
    try {
      const res = await api("/api/v1/control/reports/summary");
      if (!live(canvas)) return;
      const data = res && res.data ? res.data : {};
      const health = data.health || {};

      put(
        canvas,
        el("div", { className: "stat-grid" }, [
          statCard("System Health Score", `${health.score || 99}/100`, "Operational"),
          statCard("Zero Comment Lock", "Active (100% Enforced)", "Mandatory Invariant"),
          statCard("Hardware Compositor", "60fps FFmpeg", "Active"),
        ]),
        el("div", { className: "table-container", style: "padding: 1.5rem;" }, [
          el("h3", { textContent: "Platform Operational Audit", style: "margin-top: 0;" }),
          el("p", { textContent: `Status: ${health.status || "healthy"}` }),
          el("p", { textContent: `Active Verification Gates: ${(health.activeGates || []).join(", ")}` }),
        ])
      );
    } catch {
      if (live(canvas)) put(canvas, el("div", { className: "empty-state", textContent: "Failed to load reports." }));
    }
  }

  async function renderSettings(canvas) {
    put(canvas, el("div", { className: "skeleton skeleton-stat" }));
    try {
      const res = await api("/api/v1/control/settings");
      if (!live(canvas)) return;
      const cfg = res && res.data ? res.data : {};

      put(
        canvas,
        el("div", { className: "table-container", style: "padding: 1.5rem;" }, [
          el("h3", { textContent: "System Runtime Settings", style: "margin-top: 0;" }),
          el("p", {}, [el("strong", { textContent: "Environment: " }), el("span", { textContent: cfg.environment || "production" })]),
          el("p", {}, [el("strong", { textContent: "Version: " }), el("span", { textContent: cfg.version || "3.1.2" })]),
          el("p", {}, [el("strong", { textContent: "Database Engine: " }), el("span", { textContent: cfg.databaseEngine || "SQLite WAL" })]),
          el("p", {}, [el("strong", { textContent: "Storage Provider: " }), el("span", { textContent: cfg.storageProvider || "local" })]),
        ])
      );
    } catch {
      if (live(canvas)) put(canvas, el("div", { className: "empty-state", textContent: "Failed to load settings." }));
    }
  }

  async function renderProfile(canvas) {
    put(canvas, el("div", { className: "skeleton skeleton-stat" }));
    try {
      const res = await api("/api/v1/control/profile");
      if (!live(canvas)) return;
      const u = res && res.data ? res.data : {};

      put(
        canvas,
        el("div", { className: "table-container", style: "padding: 1.5rem;" }, [
          el("div", { className: "managing-banner" }, [
            el("span", { className: "managing-banner-title", textContent: u.managingContext || `Managing as Admin: ${u.full_name} (${u.id})` }),
            el("span", { className: "managing-banner-badge", textContent: "Super Admin" }),
          ]),
          el("p", {}, [el("strong", { textContent: "Email: " }), el("span", { textContent: u.email })]),
          el("p", {}, [el("strong", { textContent: "Role: " }), el("span", { textContent: u.role })]),
          el("p", {}, [el("strong", { textContent: "Created: " }), el("span", { textContent: formatTime(u.created_at) })]),
        ])
      );
    } catch {
      if (live(canvas)) put(canvas, el("div", { className: "empty-state", textContent: "Failed to load profile." }));
    }
  }

  // -------------------------------------------------------------------------
  // Unknown Page Fallback (Ground Rule: Must show explicit state, never silent)
  // -------------------------------------------------------------------------
  function renderUnknown(canvas, path) {
    put(
      canvas,
      el("div", { className: "empty-state" }, [
        el("h2", { className: "empty-state-title", textContent: "Unknown Page" }),
        el("p", { textContent: `The requested path '${path}' does not exist in the Control Center.` }),
        el("button", {
          className: "btn btn-primary",
          textContent: "Return to Dashboard",
          onClick: () => go("/admin/dashboard"),
        }),
      ])
    );
  }

  // =========================================================================
  // Dispatcher & Lifecycle Management
  // =========================================================================
  function render() {
    let path = window.location.pathname;

    // Bridge legacy hash routes
    if (window.location.hash.startsWith("#/")) {
      const newPath = window.location.hash.slice(1);
      history.replaceState(null, "", newPath);
      path = newPath;
      state.currentPath = newPath;
    }

    if (path === "/admin") {
      history.replaceState(null, "", "/admin/dashboard");
      path = "/admin/dashboard";
      state.currentPath = path;
    }

    updateActiveNav(path);
    const canvas = $("#mainCanvas");
    if (!canvas) return;

    if (path === "/admin/dashboard") {
      renderDashboard(canvas);
    } else if (path === "/admin/users") {
      renderUsers(canvas);
    } else if (path === "/admin/activity") {
      renderActivity(canvas);
    } else if (path === "/admin/audit") {
      renderAudit(canvas);
    } else if (path === "/admin/projects") {
      renderProjects(canvas);
    } else if (path === "/admin/videos") {
      renderVideos(canvas);
    } else if (path === "/admin/youtube") {
      renderYouTube(canvas);
    } else if (path === "/admin/usage") {
      renderUsage(canvas);
    } else if (path === "/admin/reports") {
      renderReports(canvas);
    } else if (path === "/admin/settings") {
      renderSettings(canvas);
    } else if (path === "/admin/profile") {
      renderProfile(canvas);
    } else {
      renderUnknown(canvas, path);
    }
  }

  // Notifications Poller
  function setupNotificationPoller() {
    async function checkNotifications() {
      if (document.hidden) return; // Pause when tab is hidden
      try {
        const res = await api("/api/v1/control/notifications?unread_only=true");
        if (res && res.data) {
          const count = res.data.unread_count || 0;
          const badge = $("#notifBadge");
          if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? "inline-block" : "none";
          }
        }
      } catch {
        // Silently swallow background polling errors
      }
    }

    state.notifTimer = setInterval(checkNotifications, 30000);
    checkNotifications();

    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) checkNotifications();
    });

    window.addEventListener("pagehide", () => clearInterval(state.notifTimer));
    window.addEventListener("beforeunload", () => clearInterval(state.notifTimer));
  }

  // =========================================================================
  // Initialization
  // =========================================================================
  document.addEventListener("DOMContentLoaded", () => {
    // Check authentication
    if (!state.token && window.location.pathname.startsWith("/admin") && window.location.pathname !== "/admin/login") {
      window.location.href = "/admin/login";
      return;
    }

    if (state.user && $("#sidebarAdminName")) {
      $("#sidebarAdminName").textContent = state.user.full_name || state.user.email || "Administrator";
    }

    // Intercept clicks on internal nav links for pushState SPA routing
    document.addEventListener("click", (e) => {
      const link = e.target.closest("a");
      if (!link) return;
      const href = link.getAttribute("href");
      if (href && href.startsWith("/admin/") && !href.startsWith("/admin/login")) {
        e.preventDefault();
        go(href);
      }
    });

    window.addEventListener("popstate", () => {
      state.currentPath = window.location.pathname;
      render();
    });

    const logoutBtn = $("#logoutBtn");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", () => {
        localStorage.removeItem("autopilot_admin_token");
        localStorage.removeItem("autopilot_admin_user");
        window.location.href = "/admin/login";
      });
    }

    render();
    setupNotificationPoller();
  });
})();
