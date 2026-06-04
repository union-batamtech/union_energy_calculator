/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

const TOTAL_STEPS = 4;

publicWidget.registry.UnionEnergyCalculator = publicWidget.Widget.extend({
    selector: ".o_union_energy_calculator",

    events: {
        "click .o_calc_step_next": "_onStepNext",
        "click .o_calc_step_back": "_onStepBack",
        "click .o_calculator_submit": "_onSubmit",
        "click .o_calc_restart": "_onRestart",
        "input .o_calc_range": "_onSliderInput",
        "change input[name='enquiry_type']": "_onEnquiryTypeChange",
        "change input[name='phase_type']": "_onPhaseTypeChange",
    },

    start() {
        this._currentStep = 1;
        this._isSubmitting = false;
        this._syncSlidersFromHidden();
        this._updateSegmentStyles();
        this._updatePillStyles();
        return this._super(...arguments).then(() => this._goToStep(1));
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
        if (!rooftopRange || !billRange) {
            return;
        }
        rooftopRange.value = rooftopHidden.value;
        billRange.value = billHidden.value;
        this._updateSliderDisplays();
    },

    _updateSliderDisplays() {
        const rooftop = this.el.querySelector("#rooftop_surface_m2");
        const bill = this.el.querySelector("#monthly_electricity_bill");
        if (!rooftop || !bill) {
            return;
        }
        this.el.querySelector("#rooftop_surface_m2_display").textContent = rooftop.value;
        this.el.querySelector("#monthly_electricity_bill_display").textContent = Number(
            bill.value
        ).toLocaleString();
        const rooftopRange = this.el.querySelector("#rooftop_surface_m2_range");
        const billRange = this.el.querySelector("#monthly_electricity_bill_range");
        rooftopRange.setAttribute("aria-valuenow", rooftop.value);
        billRange.setAttribute("aria-valuenow", bill.value);
    },

    _onSliderInput(ev) {
        const range = ev.currentTarget;
        if (range.id === "rooftop_surface_m2_range") {
            this.el.querySelector("#rooftop_surface_m2").value = range.value;
        } else {
            this.el.querySelector("#monthly_electricity_bill").value = range.value;
        }
        this._updateSliderDisplays();
    },

    _onEnquiryTypeChange() {
        this._updateSegmentStyles();
    },

    _onPhaseTypeChange() {
        this._updatePillStyles();
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

    _goToStep(step) {
        this._currentStep = step;
        this._hideError();
        for (const stepEl of this.el.querySelectorAll(".o_calc_step")) {
            const n = Number(stepEl.dataset.step);
            stepEl.classList.toggle("d-none", n !== step);
        }
        for (const progressEl of this.el.querySelectorAll(".o_calc_progress__step")) {
            const n = Number(progressEl.dataset.progressStep);
            progressEl.classList.remove(
                "o_calc_progress__step--active",
                "o_calc_progress__step--done"
            );
            if (n < step) {
                progressEl.classList.add("o_calc_progress__step--done");
            } else if (n === step) {
                progressEl.classList.add("o_calc_progress__step--active");
            }
        }
        const backBtn = this.el.querySelector(".o_calc_step_back");
        const nextBtn = this.el.querySelector(".o_calc_step_next");
        const submitBtn = this.el.querySelector(".o_calculator_submit");
        backBtn.classList.toggle("d-none", step === 1);
        nextBtn.classList.toggle("d-none", step === TOTAL_STEPS);
        submitBtn.classList.toggle("d-none", step !== TOTAL_STEPS);
    },

    _validateStep(step) {
        if (step === 1) {
            return !!this.el.querySelector("input[name='enquiry_type']:checked");
        }
        if (step === 2) {
            const rooftop = parseFloat(
                this.el.querySelector("#rooftop_surface_m2").value,
                10
            );
            const bill = parseFloat(
                this.el.querySelector("#monthly_electricity_bill").value,
                10
            );
            return rooftop > 0 && bill >= 0;
        }
        if (step === 3) {
            return !!this.el.querySelector("input[name='phase_type']:checked");
        }
        if (step === 4) {
            const form = this._getForm();
            const fields = ["contact_name", "email", "phone"];
            for (const id of fields) {
                const input = form.querySelector(`#${id}`);
                if (!input.reportValidity()) {
                    return false;
                }
            }
            return true;
        }
        return true;
    },

    _onStepNext(ev) {
        ev.preventDefault();
        if (!this._validateStep(this._currentStep)) {
            return;
        }
        if (this._currentStep < TOTAL_STEPS) {
            this._goToStep(this._currentStep + 1);
        }
    },

    _onStepBack(ev) {
        ev.preventDefault();
        if (this._currentStep > 1) {
            this._goToStep(this._currentStep - 1);
        }
    },

    _setSubmitLoading(loading) {
        this._isSubmitting = loading;
        const submitBtn = this.el.querySelector(".o_calculator_submit");
        const label = submitBtn.querySelector(".o_calculator_submit__label");
        submitBtn.disabled = loading;
        label.textContent = loading ? "Submitting…" : "Submit Enquiry";
    },

    _hideError() {
        const errorEl = this.el.querySelector("#calculator_error");
        if (errorEl) {
            errorEl.classList.add("d-none");
            errorEl.textContent = "";
        }
    },

    _showError(message) {
        this.el.querySelector("#calculator_wizard").classList.remove("d-none");
        this.el.querySelector("#calculator_outcome").classList.add("d-none");
        const errorEl = this.el.querySelector("#calculator_error");
        errorEl.textContent = message;
        errorEl.classList.remove("d-none");
        this._goToStep(TOTAL_STEPS);
        errorEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
    },

    _showPricing(result) {
        const symbol =
            result.currency_symbol ||
            this.el.querySelector(".o_calc_currency_symbol")?.textContent?.trim() ||
            "";
        this.el.querySelector("#calculator_estimated_kwh").textContent =
            result.estimated_kwh.toFixed(1);
        this.el.querySelector("#calculator_cost_efficiency").textContent =
            result.cost_efficiency_pct.toFixed(1);
        this.el.querySelector("#calculator_monthly_savings").textContent =
            result.monthly_savings.toFixed(2);
        const annual = result.monthly_savings * 12;
        this.el.querySelector("#calculator_annual_savings").textContent =
            annual.toFixed(2);
        const solarYield = result.solar_yield_kwh;
        this.el.querySelector("#calculator_solar_yield_kwh").textContent =
            solarYield !== undefined ? solarYield.toFixed(1) : "—";
        for (const symEl of this.el.querySelectorAll(
            "#calculator_outcome .o_calc_currency_symbol"
        )) {
            if (symbol) {
                symEl.textContent = symbol;
            }
        }
    },

    _showOutcome() {
        this.el.querySelector("#calculator_wizard").classList.add("d-none");
        const outcome = this.el.querySelector("#calculator_outcome");
        outcome.classList.remove("d-none");
        this._hideError();
        outcome.scrollIntoView({ behavior: "smooth", block: "start" });
    },

    async _onSubmit(ev) {
        ev.preventDefault();
        if (this._isSubmitting) {
            return;
        }
        if (!this._validateStep(TOTAL_STEPS)) {
            return;
        }

        this._setSubmitLoading(true);
        try {
            const result = await rpc("/calculator/submit", this._getFormValues());
            this._showPricing(result);
            this._showOutcome();
        } catch (error) {
            this._showError(error.message || "Unable to submit enquiry.");
        } finally {
            this._setSubmitLoading(false);
        }
    },

    _resetFormDefaults() {
        const form = this._getForm();
        form.reset();
        this.el.querySelector("#rooftop_surface_m2").value = "80";
        this.el.querySelector("#rooftop_surface_m2_range").value = "80";
        this.el.querySelector("#monthly_electricity_bill").value = "200";
        this.el.querySelector("#monthly_electricity_bill_range").value = "200";
        const residential = form.querySelector(
            "input[name='enquiry_type'][value='residential']"
        );
        if (residential) {
            residential.checked = true;
        }
        const single = form.querySelector("input[name='phase_type'][value='single']");
        if (single) {
            single.checked = true;
        }
        this._syncSlidersFromHidden();
        this._updateSegmentStyles();
        this._updatePillStyles();
    },

    _onRestart(ev) {
        ev.preventDefault();
        this._resetFormDefaults();
        this.el.querySelector("#calculator_outcome").classList.add("d-none");
        this.el.querySelector("#calculator_wizard").classList.remove("d-none");
        this._hideError();
        this._goToStep(1);
        this.el.querySelector("#calculator_wizard").scrollIntoView({
            behavior: "smooth",
            block: "start",
        });
    },
});

export default publicWidget.registry.UnionEnergyCalculator;
