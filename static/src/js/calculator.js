/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

const DEBOUNCE_MS = 400;

publicWidget.registry.UnionEnergyCalculator = publicWidget.Widget.extend({
    selector: ".o_union_energy_calculator",

    events: {
        "click .o_calculator_compute": "_onCalculate",
        "click .o_calculator_submit": "_onSubmit",
        "input .o_calc_range": "_onSliderInput",
        "change input[name='enquiry_type']": "_onEnquiryTypeChange",
        "change input[name='phase_type']": "_onPhaseTypeChange",
        "input .o_calc_input": "_onContactInput",
    },

    start() {
        this._debounceTimer = null;
        this._syncSlidersFromHidden();
        this._updateSegmentStyles();
        this._updatePillStyles();
        return this._super(...arguments).then(() => this._scheduleCalculate());
    },

    _getForm() {
        return this.el.querySelector("#union_energy_calculator_form");
    },

    _getFormValues() {
        const form = this._getForm();
        const formData = new FormData(form);
        return {
            rooftop_surface_m2: formData.get("rooftop_surface_m2"),
            monthly_electricity_bill: formData.get("monthly_electricity_bill"),
            phase_type: formData.get("phase_type"),
            enquiry_type: formData.get("enquiry_type"),
            contact_name: formData.get("contact_name"),
            email: formData.get("email"),
            phone: formData.get("phone"),
        };
    },

    _syncSlidersFromHidden() {
        const rooftopRange = this.el.querySelector("#rooftop_surface_m2_range");
        const rooftopHidden = this.el.querySelector("#rooftop_surface_m2");
        const billRange = this.el.querySelector("#monthly_electricity_bill_range");
        const billHidden = this.el.querySelector("#monthly_electricity_bill");
        rooftopRange.value = rooftopHidden.value;
        billRange.value = billHidden.value;
        this._updateSliderDisplays();
    },

    _updateSliderDisplays() {
        const rooftop = this.el.querySelector("#rooftop_surface_m2");
        const bill = this.el.querySelector("#monthly_electricity_bill");
        this.el.querySelector("#rooftop_surface_m2_display").textContent = rooftop.value;
        this.el.querySelector("#monthly_electricity_bill_display").textContent = Number(
            bill.value
        ).toLocaleString();
    },

    _onSliderInput(ev) {
        const range = ev.currentTarget;
        if (range.id === "rooftop_surface_m2_range") {
            this.el.querySelector("#rooftop_surface_m2").value = range.value;
        } else {
            this.el.querySelector("#monthly_electricity_bill").value = range.value;
        }
        this._updateSliderDisplays();
        this._scheduleCalculate();
    },

    _onEnquiryTypeChange() {
        this._updateSegmentStyles();
        this._scheduleCalculate();
    },

    _onPhaseTypeChange() {
        this._updatePillStyles();
        this._scheduleCalculate();
    },

    _onContactInput() {
        // No live recalc needed for contact fields.
    },

    _updateSegmentStyles() {
        for (const label of this.el.querySelectorAll(".o_calc_segment")) {
            const input = label.querySelector("input[type='radio']");
            label.classList.toggle("o_calc_segment--active", input.checked);
        }
    },

    _updatePillStyles() {
        for (const label of this.el.querySelectorAll(".o_calc_pill")) {
            const input = label.querySelector("input[type='radio']");
            label.classList.toggle("o_calc_pill--active", input.checked);
        }
    },

    _scheduleCalculate() {
        clearTimeout(this._debounceTimer);
        this._debounceTimer = setTimeout(() => this._calculate(), DEBOUNCE_MS);
    },

    _hideAlerts() {
        for (const alertEl of this.el.querySelectorAll(
            "#calculator_result, #calculator_success, #calculator_error"
        )) {
            alertEl.classList.add("d-none");
        }
    },

    _showError(message) {
        this._hideAlerts();
        const errorEl = this.el.querySelector("#calculator_error");
        errorEl.textContent = message;
        errorEl.classList.remove("d-none");
    },

    _showResult(result) {
        this.el.querySelector("#calculator_estimated_kwh").textContent =
            result.estimated_kwh.toFixed(1);
        this.el.querySelector("#calculator_cost_efficiency").textContent =
            result.cost_efficiency_pct.toFixed(1);
        this.el.querySelector("#calculator_monthly_savings").textContent =
            result.monthly_savings.toFixed(2);
        this.el.querySelector("#calculator_result").classList.remove("d-none");
        this.el.querySelector("#calculator_error").classList.add("d-none");
    },

    async _calculate() {
        try {
            const result = await rpc("/calculator/calculate", this._getFormValues());
            this._showResult(result);
        } catch (error) {
            // Silent on live preview — user may still be adjusting sliders.
        }
    },

    async _onCalculate(ev) {
        ev.preventDefault();
        await this._calculate();
    },

    async _onSubmit(ev) {
        ev.preventDefault();
        const form = this._getForm();
        if (!form.reportValidity()) {
            return;
        }

        try {
            const result = await rpc("/calculator/submit", this._getFormValues());
            this.el.querySelector("#calculator_error").classList.add("d-none");
            this._showResult(result);
            this.el.querySelector("#calculator_success").classList.remove("d-none");
            form.reset();
            this._syncSlidersFromHidden();
            this._updateSegmentStyles();
            this._updatePillStyles();
            this._scheduleCalculate();
        } catch (error) {
            this._showError(error.message || "Unable to submit enquiry.");
        }
    },
});

export default publicWidget.registry.UnionEnergyCalculator;
