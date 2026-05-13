/**
 * ScamGuard — Self-hosted Bootstrap 5 Modal & Utility Polyfill
 * Implements: Modal.getOrCreateInstance(), modal.show(), modal.hide()
 *             data-bs-dismiss="modal", aria management, keyboard (Esc)
 *             Tab-trap focus management, backdrop click-to-close.
 *
 * Drop-in replacement for bootstrap.bundle.min.js Modal functionality.
 * No CDN. No tracking. Served from /static/ by FastAPI.
 * ~5KB. Works in Edge, Chrome, Firefox, Safari.
 */
(function (global) {
  "use strict";

  /* ── Shared backdrop ───────────────────────────────────────────────────── */
  let _backdrop = null;
  let _openCount = 0;

  function getBackdrop() {
    if (!_backdrop) {
      _backdrop = document.createElement("div");
      _backdrop.className = "modal-backdrop fade";
      _backdrop.style.cssText = [
        "position:fixed", "inset:0", "z-index:1040",
        "background:rgba(0,0,0,.65)", "opacity:0",
        "transition:opacity .15s linear", "backdrop-filter:blur(4px)",
      ].join(";");
      document.body.appendChild(_backdrop);
    }
    return _backdrop;
  }

  /* ── Modal class ────────────────────────────────────────────────────────── */
  class Modal {
    constructor(element) {
      this._el       = typeof element === "string" ? document.querySelector(element) : element;
      this._dialog   = this._el?.querySelector(".modal-dialog");
      this._isShown  = false;
      this._lastFocus = null;

      // Wire data-bs-dismiss inside this modal
      this._el?.querySelectorAll("[data-bs-dismiss='modal']").forEach(btn => {
        btn.addEventListener("click", () => this.hide());
      });

      // Close on backdrop click
      this._el?.addEventListener("click", (e) => {
        if (e.target === this._el) this.hide();
      });
    }

    show() {
      if (this._isShown) return;
      this._isShown = true;
      this._lastFocus = document.activeElement;

      // Body class
      _openCount++;
      document.body.classList.add("modal-open");
      document.body.style.overflow = "hidden";

      // Backdrop
      const bd = getBackdrop();
      bd.style.display = "block";
      requestAnimationFrame(() => { bd.style.opacity = "1"; });

      // Show modal element
      this._el.style.display = "block";
      this._el.removeAttribute("aria-hidden");
      this._el.setAttribute("aria-modal", "true");
      this._el.setAttribute("role", "dialog");

      requestAnimationFrame(() => {
        this._el.classList.add("show");
        // Focus first focusable element
        const focusable = this._el.querySelectorAll(
          "input:not([disabled]), button:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex='-1'])"
        );
        if (focusable.length) focusable[0].focus();
      });

      // Keyboard: Esc to close, Tab trap
      this._keyHandler = (e) => {
        if (e.key === "Escape") { this.hide(); return; }
        if (e.key === "Tab") { this._trapFocus(e); }
      };
      document.addEventListener("keydown", this._keyHandler);

      // Dispatch Bootstrap-compatible event
      this._el.dispatchEvent(new CustomEvent("shown.bs.modal", { bubbles: true }));
    }

    hide() {
      if (!this._isShown) return;
      this._isShown = false;

      this._el.classList.remove("show");
      this._el.setAttribute("aria-hidden", "true");
      this._el.removeAttribute("aria-modal");

      // Remove event listener
      if (this._keyHandler) {
        document.removeEventListener("keydown", this._keyHandler);
        this._keyHandler = null;
      }

      setTimeout(() => {
        this._el.style.display = "none";

        _openCount = Math.max(0, _openCount - 1);
        if (_openCount === 0) {
          document.body.classList.remove("modal-open");
          document.body.style.overflow = "";
          const bd = getBackdrop();
          bd.style.opacity = "0";
          setTimeout(() => { if (_openCount === 0) bd.style.display = "none"; }, 160);
        }

        // Restore focus
        if (this._lastFocus?.focus) this._lastFocus.focus();

        this._el.dispatchEvent(new CustomEvent("hidden.bs.modal", { bubbles: true }));
      }, 150);
    }

    _trapFocus(e) {
      const focusable = Array.from(this._el.querySelectorAll(
        "a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex='-1'])"
      )).filter(el => el.offsetParent !== null);
      if (!focusable.length) return;
      const first = focusable[0];
      const last  = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault(); last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault(); first.focus();
      }
    }

    // Static: prevent duplicate instances
    static getOrCreateInstance(element) {
      const el = typeof element === "string" ? document.querySelector(element) : element;
      if (!el) return null;
      if (el._bsModal) return el._bsModal;
      el._bsModal = new Modal(el);
      return el._bsModal;
    }

    static getInstance(element) {
      const el = typeof element === "string" ? document.querySelector(element) : element;
      return el?._bsModal || null;
    }
  }

  /* ── Collapse (minimal — for navbar toggler) ────────────────────────────── */
  class Collapse {
    constructor(element, options = {}) {
      this._el     = typeof element === "string" ? document.querySelector(element) : element;
      this._toggle = options.toggle !== false;
      if (this._toggle) this.toggle();
    }
    show()   { if (!this._el) return; this._el.classList.add("show"); this._el.style.height = "auto"; }
    hide()   { if (!this._el) return; this._el.classList.remove("show"); }
    toggle() { if (!this._el) return; this._el.classList.contains("show") ? this.hide() : this.show(); }
    static getOrCreateInstance(el) { return el._bsCollapse || (el._bsCollapse = new Collapse(el, { toggle: false })); }
  }

  /* ── Expose as global `bootstrap` namespace ─────────────────────────────── */
  global.bootstrap = { Modal, Collapse };

  /* ── Auto-wire data-bs-toggle="collapse" ────────────────────────────────── */
  document.addEventListener("DOMContentLoaded", () => {
    document.addEventListener("click", (e) => {
      const toggler = e.target.closest("[data-bs-toggle='collapse']");
      if (!toggler) return;
      const target = document.querySelector(toggler.getAttribute("data-bs-target"));
      if (target) Collapse.getOrCreateInstance(target).toggle();
    });
  });

})(window);
