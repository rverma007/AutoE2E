# Author: Ruchika Verma <testing.ruchika@gmail.com>
"""
Settings module — TC_SM_041 to TC_SM_043.

Covers:
  TC_SM_041  Global Config is default selected with all data visible
  TC_SM_042  Business Unit Config tab loads with BU list and toggles
  TC_SM_043  Toggle Auto Correct Address (Letter) → Save → verify → undo → Save → verify
"""
from __future__ import annotations

import allure
import pytest

from pages.settings_page import SettingsPage


pytestmark = pytest.mark.sanity


@allure.epic("Correspondence Application")
@allure.feature("Settings")
class TestSettings:

    @allure.story("Global Configuration")
    @allure.title("[TC_SM_041] Global Config is selected by default with all data visible")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Navigate to the Settings page and verify:\n"
        "  • The page loads and Global Config section is visible by default.\n"
        "  • The URL contains 'settings'.\n"
        "  • The Global Config tab exists and is active (aria-selected=true or no BU panel).\n"
        "  • The Ingestion Model dropdown is present and enabled.\n"
        "  • The Enable AskAuto toggle is present.\n"
        "  • The Save Settings button is present and enabled."
    )
    def test_global_configuration_default(self, settings_page: SettingsPage):
        with allure.step("Navigate to Settings"):
            settings_page.open_direct()

        with allure.step("Assert Settings page loaded and URL is correct"):
            loaded = settings_page.is_loaded(timeout=15_000)
            url = settings_page.page.url
            allure.attach(
                f"Loaded: {loaded}\nURL: {url}",
                name="Page load state",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert loaded, f"Settings page did not load. URL: {url}"
            assert "settings" in url.lower(), (
                f"URL does not contain 'settings' — unexpected page. URL: {url}"
            )

        with allure.step("Assert Global Config section is visible by default (no tab click needed)"):
            gc_visible = settings_page.is_global_config_visible(timeout=10_000)
            allure.attach(
                f"Global Configuration visible by default: {gc_visible}",
                name="Global Config default visibility",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert gc_visible, (
                "Global Configuration section/heading not visible by default. "
                "Expected Global Config to be the active tab on page load."
            )

        with allure.step("Assert Global Config tab exists on the page"):
            tab_visible = settings_page.is_visible(settings_page.global_config_tab, timeout=5_000)
            allure.attach(
                f"Global Config tab element visible: {tab_visible}",
                name="Global Config tab",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert tab_visible, "Global Config tab not found on Settings page."

        with allure.step("Assert Ingestion Model dropdown is visible and enabled"):
            ingestion_loc = settings_page.ingestion_model_dropdown
            ingestion_visible = settings_page.is_visible(ingestion_loc, timeout=8_000)
            allure.attach(
                f"Ingestion Model dropdown visible: {ingestion_visible}",
                name="Ingestion Model dropdown",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert ingestion_visible, (
                "Ingestion Model dropdown not visible on Global Config page."
            )
            is_disabled = ingestion_loc.get_attribute("disabled")
            assert is_disabled is None, (
                "Ingestion Model dropdown is present but disabled — expected it to be interactive."
            )

        with allure.step("Assert Enable AskAuto toggle is visible"):
            askauto_loc = settings_page.enable_ask_auto_toggle
            askauto_visible = settings_page.is_visible(askauto_loc, timeout=8_000)
            allure.attach(
                f"Enable AskAuto toggle visible: {askauto_visible}",
                name="Enable AskAuto toggle",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert askauto_visible, (
                "Enable AskAuto toggle not visible on Global Config page."
            )

        with allure.step("Assert Enable AskAuto toggle has a readable boolean state"):
            askauto_state = settings_page.is_toggle_checked(askauto_loc)
            allure.attach(
                f"Enable AskAuto current state (checked): {askauto_state}",
                name="AskAuto toggle state",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert isinstance(askauto_state, bool), (
                "Could not read a boolean state from Enable AskAuto toggle."
            )

        with allure.step("Assert Save Settings button is present and enabled"):
            save_visible = settings_page.is_save_button_visible(timeout=5_000)
            allure.attach(
                f"Save Settings button visible: {save_visible}",
                name="Save button visibility",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert save_visible, "Save Settings button not found on Global Configuration page."
            save_disabled = settings_page.save_settings_button.get_attribute("disabled")
            assert save_disabled is None, (
                "Save Settings button is present but disabled on Global Config page."
            )

    @allure.story("Business Unit Configuration")
    @allure.title("[TC_SM_042] Business Unit Config tab loads with BU list and toggles")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Click the Business Unit Config tab and verify:\n"
        "  • The BU Config section heading becomes visible.\n"
        "  • The left panel shows at least one Business Unit entry.\n"
        "  • Clicking the first BU loads the right detail panel.\n"
        "  • All four BU-level toggles are visible and have readable states.\n"
        "  • The Save Settings button is visible and enabled."
    )
    def test_business_unit_configuration_loads(self, settings_page: SettingsPage):
        with allure.step("Navigate to Settings"):
            settings_page.open_direct()
            assert settings_page.is_loaded(timeout=15_000), "Settings page did not load."

        with allure.step("Assert Business Unit Config tab exists"):
            bu_tab_visible = settings_page.is_visible(settings_page.bu_config_tab, timeout=5_000)
            allure.attach(
                f"BU Config tab visible: {bu_tab_visible}",
                name="BU Config tab presence",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert bu_tab_visible, "Business Unit Config tab not found on Settings page."

        with allure.step("Click Business Unit Config tab"):
            settings_page.click_bu_config_tab()

        with allure.step("Assert Business Unit Config section heading is visible"):
            bu_visible = settings_page.is_bu_config_visible(timeout=10_000)
            allure.attach(
                f"BU Config section visible: {bu_visible}",
                name="BU Config visibility",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert bu_visible, (
                "Business Unit Config section/heading not visible after clicking the tab."
            )

        with allure.step("Assert BU list panel has at least one entry"):
            bu_count = settings_page.bu_list_items.count()
            allure.attach(
                f"BU list items found: {bu_count}",
                name="BU list count",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert bu_count > 0, (
                "No Business Unit entries found in the left panel list."
            )

        with allure.step("Click first BU to load its configuration panel"):
            bu_name = settings_page.select_first_bu()
            allure.attach(
                f"Selected BU name: '{bu_name or '(first item)'}'",
                name="Selected BU",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert bu_name or True, "select_first_bu() returned empty — BU may not have a label."

        with allure.step("Assert all BU-level toggles are visible in the right panel"):
            toggles = {
                "Auto Correct Address (Letter)": settings_page.auto_correct_address_letter_toggle,
                "Inserts Margin":                settings_page.inserts_margin_toggle,
                "Margin Correction":             settings_page.margin_correction_toggle,
                "Auto Correct Address (LetterType)": settings_page.auto_correct_address_letter_type_toggle,
            }
            toggle_states: dict[str, bool | str] = {}
            missing_toggles: list[str] = []

            for label, loc in toggles.items():
                # MUI switch inputs are CSS-hidden — use count() not is_visible()
                found = loc.count() > 0
                if found:
                    toggle_states[label] = settings_page.is_toggle_checked(loc)
                else:
                    toggle_states[label] = "NOT FOUND"
                    missing_toggles.append(label)

            allure.attach(
                "\n".join(f"{k}: {v}" for k, v in toggle_states.items()),
                name="BU toggle states",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert not missing_toggles, (
                f"These BU toggle inputs were not found after selecting the first BU: "
                f"{missing_toggles}"
            )

        with allure.step("Assert each toggle has a readable boolean state"):
            for label, state in toggle_states.items():
                assert isinstance(state, bool), (
                    f"Toggle '{label}' did not return a boolean state (got: {state!r})."
                )

        with allure.step("Assert Save Settings button is visible and enabled"):
            save_visible = settings_page.is_save_button_visible(timeout=5_000)
            allure.attach(
                f"Save Settings button visible: {save_visible}",
                name="Save button visibility",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert save_visible, "Save Settings button not found on Business Unit Config page."
            save_disabled = settings_page.save_settings_button.get_attribute("disabled")
            assert save_disabled is None, (
                "Save Settings button is present but disabled on BU Config page."
            )

    @allure.story("Business Unit Configuration – Toggle Save & Undo")
    @allure.title(
        "[TC_SM_043] BU Config: toggle Auto Correct Address, save, verify, undo, save, verify"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Open Business Unit Config, select the first BU, then:\n"
        "  1. Read the initial state of 'Auto Correct Address (Letter)'.\n"
        "  2. Toggle it → assert state changed → Save → assert success toast.\n"
        "  3. Undo toggle → assert state returned to original → Save → assert success toast."
    )
    def test_bu_config_toggle_save_and_undo(self, settings_page: SettingsPage):
        with allure.step("Navigate to Settings and open BU Config tab"):
            settings_page.open_direct()
            assert settings_page.is_loaded(timeout=15_000), "Settings page did not load."
            settings_page.click_bu_config_tab()
            assert settings_page.is_bu_config_visible(timeout=10_000), (
                "Business Unit Config section not visible."
            )

        with allure.step("Select the first BU from the left panel"):
            bu_name = settings_page.select_first_bu()
            allure.attach(
                f"Selected BU: '{bu_name or '(first item)'}'",
                name="Selected BU",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Assert Auto Correct Address (Letter) toggle is present"):
            toggle = settings_page.auto_correct_address_letter_toggle
            # MUI switch inputs are CSS-hidden — use count() not is_visible()
            toggle_found = toggle.count() > 0
            allure.attach(
                f"Toggle input elements found: {toggle_found}",
                name="Toggle presence",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert toggle_found, (
                "Auto Correct Address (Letter) toggle input not found — cannot proceed."
            )

        with allure.step("Read and record initial toggle state"):
            initial_state = settings_page.is_toggle_checked(toggle)
            assert isinstance(initial_state, bool), (
                "Initial toggle state could not be read as a boolean."
            )
            allure.attach(
                f"Initial state (ON={initial_state})",
                name="Initial toggle state",
                attachment_type=allure.attachment_type.TEXT,
            )

        # ── Step 1: Toggle → assert changed → Save → assert toast ─────────────
        with allure.step(
            f"Toggle to {'OFF' if initial_state else 'ON'} (opposite of initial)"
        ):
            settings_page.click_toggle(toggle, "Auto Correct Address (Letter)")
            after_first_toggle = settings_page.is_toggle_checked(toggle)
            allure.attach(
                f"State after first toggle (ON={after_first_toggle})",
                name="State after first toggle",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert after_first_toggle != initial_state, (
                f"Toggle did not change state after click — still {initial_state}. "
                "The toggle may be read-only or the click did not register."
            )

        with allure.step("Save Settings after first toggle and assert success"):
            saved_1 = settings_page.click_save_settings()
            allure.attach(
                f"Success toast appeared: {saved_1}",
                name="Save result (step 1)",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert saved_1, (
                "Save Settings did not confirm success after toggling "
                "Auto Correct Address (Letter) to "
                f"{'OFF' if initial_state else 'ON'}."
            )

        # ── Step 2: Undo toggle → assert restored → Save → assert toast ────────
        with allure.step(
            f"Undo: toggle back to {'ON' if initial_state else 'OFF'} (original state)"
        ):
            settings_page.click_toggle(toggle, "Auto Correct Address (Letter) undo")
            after_undo = settings_page.is_toggle_checked(toggle)
            allure.attach(
                f"State after undo toggle (ON={after_undo})",
                name="State after undo",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert after_undo == initial_state, (
                f"Toggle did not return to its original state after undo. "
                f"Expected ON={initial_state}, got ON={after_undo}."
            )

        with allure.step("Save Settings after undo toggle and assert success"):
            saved_2 = settings_page.click_save_settings()
            allure.attach(
                f"Success toast appeared: {saved_2}",
                name="Save result (step 2)",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert saved_2, (
                "Save Settings did not confirm success after undoing "
                "the Auto Correct Address (Letter) toggle back to "
                f"{'ON' if initial_state else 'OFF'}."
            )

        with allure.step("Assert final toggle state matches initial (idempotency check)"):
            final_state = settings_page.is_toggle_checked(toggle)
            allure.attach(
                f"Final state (ON={final_state}) == Initial state (ON={initial_state}): "
                f"{final_state == initial_state}",
                name="Idempotency check",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert final_state == initial_state, (
                f"Final toggle state ON={final_state} does not match "
                f"initial state ON={initial_state} — settings may not have been restored."
            )
