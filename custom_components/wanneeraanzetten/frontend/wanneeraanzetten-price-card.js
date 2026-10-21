const CARD_TAG = "wanneeraanzetten-price-card";
const SETTINGS_URL = "https://wanneeraanzetten.nl/?view=settings";
const BRAND = "#34e374";

const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
})[char]);

class WanneerAanzettenPriceCard extends HTMLElement {
  setConfig(config) {
    this.config = { ...config };
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    if (!this.config?.entity) {
      const discovered = Object.entries(hass.states).find(([entityId, state]) =>
        entityId.startsWith("sensor.") && state.attributes?.tariff_settings_url === SETTINGS_URL
      );
      if (discovered) this.config = { ...(this.config || {}), entity: discovered[0] };
    }
    this.render();
  }

  getCardSize() { return 4; }
  static getConfigElement() { return document.createElement(`${CARD_TAG}-editor`); }
  static getStubConfig() { return {}; }

  render() {
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    const english = this._hass?.locale?.language?.startsWith("en") === true;
    const copy = english ? {
      setup: "Choose the Wanneer Aanzetten price sensor in the card settings.",
      title: "Electricity price", allIn: "Estimated all-in price", spot: "Spot price",
      included: "Includes VAT, energy tax and the saved supplier markup.",
      needsTariff: "Showing spot prices. Add your contract tariff for an all-in estimate.",
      missing: "Price forecast is not available yet", wait: "Waiting for price data",
      unavailable: "Part of this period has no published price data. Missing periods are not treated as zero.",
      settings: "Manage tariff settings", setTariff: "Set your tariff at wanneeraanzetten.nl",
      fixed: "Estimate · fixed fees excluded", excluded: "Spot price · excludes VAT and supplier markup",
      chart: "Estimated all-in", notReady: "The price forecast is temporarily unavailable. Your sensor and automations will resume when prices return.",
    } : {
      setup: "Kies de Wanneer Aanzetten-prijssensor in de kaartinstellingen.",
      title: "Stroomprijs", allIn: "Geschatte all-in prijs", spot: "Spotprijs",
      included: "Inclusief btw, energiebelasting en ingestelde leveranciersopslag.",
      needsTariff: "Je ziet de spotprijs. Stel je contracttarief in voor een all-in schatting.",
      missing: "Prijsprognose nog niet beschikbaar", wait: "Wachten op nieuwe prijsdata",
      unavailable: "Prijsdata voor een deel van deze periode ontbreekt. Ontbrekende perioden zijn niet als nul meegerekend.",
      settings: "Tariefinstellingen beheren", setTariff: "Stel je tarief in op wanneeraanzetten.nl",
      fixed: "Schatting · vaste kosten niet inbegrepen", excluded: "Spotprijs · excl. btw en leveranciersopslag",
      chart: "Geschatte all-in", notReady: "De prijsprognose is tijdelijk niet beschikbaar. De huidige sensor en automations blijven bruikbaar zodra er nieuwe prijzen zijn.",
    };
    const entity = this._hass?.states?.[this.config?.entity];
    if (!entity) {
      this.shadowRoot.innerHTML = `<ha-card><div class="notice">${copy.setup}</div></ha-card>${this.styles()}`;
      return;
    }
    const attrs = entity.attributes || {};
    const prices = Array.isArray(attrs.prices) ? attrs.prices.filter((item) => Number.isFinite(item.spot)).slice(0, 96) : [];
    const allIn = attrs.tariff_configured === true && prices.some((item) => Number.isFinite(item.estimated_all_in));
    const now = Date.now();
    const rows = prices.map((item) => ({
      ...item,
      startMs: Date.parse(item.start),
      value: allIn ? item.estimated_all_in : item.spot,
    })).filter((item) => Number.isFinite(item.startMs));
    const chart = this.makeChart(rows, now);
    const current = Number.isFinite(Number(entity.state)) ? Number(entity.state) : null;
    const currentText = current === null ? (english ? "No price available" : "Geen prijs beschikbaar") : `${current.toLocaleString(undefined, { minimumFractionDigits: 3, maximumFractionDigits: 5 })} €/kWh`;
    const status = attrs.tariff_configured ? copy.included : copy.needsTariff;
    const title = allIn ? copy.allIn : copy.title;
    const span = rows.length ? `${new Date(rows[0].startMs).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} – ${new Date(rows.at(-1).startMs).toLocaleDateString([], { weekday: "short", day: "numeric", month: "short" })}` : copy.missing;
    const missingDays = Array.isArray(attrs.unavailable_days) && attrs.unavailable_days.length > 0;

    this.shadowRoot.innerHTML = `${this.styles()}
      <ha-card>
        <header>
          <svg class="mark" viewBox="0 0 44 44" role="img" aria-label="Wanneer Aanzetten-logo"><circle cx="22" cy="22" r="20" fill="${BRAND}" opacity=".14"/><path d="M24.5 5 11 25h9l-1.5 14L33 18h-9.5z" fill="${BRAND}"/><path d="M8 33c6 3 22 3 28-4" fill="none" stroke="${BRAND}" stroke-width="2.5" stroke-linecap="round" opacity=".75"/></svg>
          <div class="heading"><div class="brand">Wanneer Aanzetten</div><h2>${title}</h2></div>
          <div class="current">${escapeHtml(currentText)}</div>
        </header>
        <p class="sub">${escapeHtml(status)}</p>
        <div class="chart" role="img" aria-label="${allIn ? copy.chart : copy.spot} electricity prices for the next 24 hours">${chart}</div>
        <div class="axis"><span>${escapeHtml(span)}</span><span>${escapeHtml(attrs.country || "")}</span></div>
        ${rows.length ? "" : `<p class="notice">${copy.notReady}</p>`}
        ${missingDays ? `<p class="notice">${copy.unavailable}</p>` : ""}
        <footer><a href="${SETTINGS_URL}" target="_blank" rel="noopener noreferrer">${allIn ? copy.settings : copy.setTariff}<span aria-hidden="true"> ↗</span></a><span class="definition">${allIn ? copy.fixed : copy.excluded}</span></footer>
      </ha-card>`;
  }

  makeChart(rows, now) {
    if (!rows.length) return `<div class="empty">Wachten op nieuwe prijsdata</div>`;
    const width = 720, height = 196, left = 8, right = 8, top = 12, bottom = 24;
    const plotWidth = width - left - right, plotHeight = height - top - bottom;
    const values = rows.map((item) => item.value);
    const low = Math.min(0, ...values), high = Math.max(0, ...values);
    const span = Math.max(high - low, 0.01);
    const y = (value) => top + (high - value) / span * plotHeight;
    const zero = y(0);
    const step = plotWidth / rows.length;
    const barWidth = Math.max(1, step - Math.max(1, step * 0.16));
    const bars = rows.map((item, index) => {
      const x = left + index * step + (step - barWidth) / 2;
      const valueY = y(item.value);
      const barY = Math.min(zero, valueY);
      const barHeight = Math.max(1.5, Math.abs(valueY - zero));
      const isCurrent = now >= item.startMs && now < Date.parse(item.end);
      const label = `${new Date(item.startMs).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}: ${item.value.toLocaleString(undefined, { maximumFractionDigits: 4 })} €/kWh`;
      return `<rect x="${x.toFixed(2)}" y="${barY.toFixed(2)}" width="${barWidth.toFixed(2)}" height="${barHeight.toFixed(2)}" rx="${Math.min(3, barWidth / 2).toFixed(1)}" fill="${isCurrent ? "var(--primary-color, #03a9f4)" : item.value < 0 ? "#56b4e9" : BRAND}" opacity="${isCurrent ? 1 : 0.76}"><title>${escapeHtml(label)}</title></rect>`;
    }).join("");
    const zeroLine = `<line x1="${left}" y1="${zero.toFixed(2)}" x2="${width - right}" y2="${zero.toFixed(2)}" stroke="var(--divider-color, #777)" stroke-opacity=".5" stroke-width="1"/>`;
    const labels = rows.map((item, index) => ({ item, index })).filter(({ index }) => index % Math.max(1, Math.ceil(rows.length / 6)) === 0).map(({ item, index }) => {
      const x = left + index * step;
      return `<text x="${x.toFixed(2)}" y="${height - 5}" fill="var(--secondary-text-color, #999)" font-size="11">${escapeHtml(new Date(item.startMs).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }))}</text>`;
    }).join("");
    return `<svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" focusable="false" aria-hidden="true">${zeroLine}${bars}${labels}</svg>`;
  }

  styles() {
    return `<style>
      :host{display:block;color:var(--primary-text-color);font-family:var(--paper-font-body1_-_font-family,inherit)}
      ha-card{overflow:hidden;padding:20px 22px 16px;background:var(--ha-card-background,var(--card-background-color));color:inherit}
      header{display:flex;align-items:center;gap:12px;min-width:0}
      .mark{width:42px;height:42px;flex:0 0 auto}
      .heading{min-width:0;flex:1}.brand{font-size:12px;letter-spacing:.02em;color:var(--secondary-text-color);font-weight:600}
      h2{font-size:17px;line-height:1.25;margin:3px 0 0;font-weight:650}
      .current{font-variant-numeric:tabular-nums;font-size:clamp(16px,3vw,22px);font-weight:700;white-space:nowrap}
      .sub{margin:12px 0 0;color:var(--secondary-text-color);font-size:13px;line-height:1.45}
      .chart{height:190px;margin:8px -4px 0}.chart svg{width:100%;height:100%;overflow:visible}.empty{height:100%;display:grid;place-items:center;color:var(--secondary-text-color);font-size:14px}
      .axis{display:flex;justify-content:space-between;color:var(--secondary-text-color);font-size:12px;font-variant-numeric:tabular-nums;padding:0 2px 12px;border-bottom:1px solid var(--divider-color)}
      footer{display:flex;justify-content:space-between;align-items:center;gap:12px;padding-top:14px;flex-wrap:wrap}
      a{color:var(--primary-color,#34e374);font-size:14px;font-weight:650;text-decoration:none;text-underline-offset:3px}a:hover{text-decoration:underline}
      a:focus-visible{outline:2px solid var(--primary-color,#34e374);outline-offset:3px;border-radius:2px}
      .definition{font-size:11px;color:var(--secondary-text-color);text-align:right}.notice{margin:10px 0 0;color:var(--secondary-text-color);font-size:13px;line-height:1.45}
      @media(max-width:480px){ha-card{padding:16px}.mark{width:36px;height:36px}.chart{height:160px}.current{font-size:16px}.definition{width:100%;text-align:left}}
      @media(prefers-reduced-motion:no-preference){a{transition:color 140ms ease-out}}
    </style>`;
  }
}

class WanneerAanzettenPriceCardEditor extends HTMLElement {
  setConfig(config) { this.config = config || {}; this.render(); }
  set hass(hass) {
    this._hass = hass;
    this.render();
  }
  render() {
    if (!this._hass) return;
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `<div style="padding:12px 0"><ha-entity-picker label="Price sensor"></ha-entity-picker><p style="color:var(--secondary-text-color)">Choose the Wanneer Aanzetten sensor to show its price timeline and estimated all-in price.</p></div>`;
    const picker = this.shadowRoot.querySelector("ha-entity-picker");
    picker.hass = this._hass;
    picker.includeDomains = ["sensor"];
    picker.allowCustomEntity = false;
    picker.value = this.config.entity || "";
    picker.addEventListener("value-changed", (event) => {
      if (!event.detail?.value) return;
      this.config = { ...this.config, entity: event.detail.value };
      this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this.config }, bubbles: true, composed: true }));
    });
  }
}

if (!customElements.get(CARD_TAG)) customElements.define(CARD_TAG, WanneerAanzettenPriceCard);
if (!customElements.get(`${CARD_TAG}-editor`)) customElements.define(`${CARD_TAG}-editor`, WanneerAanzettenPriceCardEditor);
window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === CARD_TAG)) {
  window.customCards.push({
    type: CARD_TAG,
    name: "Wanneer Aanzetten · Prijsgrafiek",
    description: "Branded stroomprijs graph with tariff-aware estimates and a direct settings link.",
    preview: true,
  });
}
