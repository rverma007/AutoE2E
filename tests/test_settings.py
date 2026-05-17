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
        "  • The page loads and Global Config tab is active by default.\n"
        "  • The Ingestion Model dropdown is visible.\n"
        "  • The Enable AskAuto toggle is visible.\n"
        "  • The Save Settings button is present."
    )
    def test_global_configuration_default(self, settings_page: SettingsPage):
        with allure.step("Navigate to Settings"):
            settings_page.open_direct()

        with allure.step("Assert Settings page loaded"):
            loaded = settings_page.is_loaded(timeout=15_000)
            allure.attach(
                f"Settings page loaded: {loaded}\nURL: {settings_page.page.url}",
                name="Page load state",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert loaded, f"Settings page did not load. URL: {settings_page.page.url}"

        with allure.step("Assert Global Config section is visible by default"):
            gc_visible = settings_page.is_global_config_visible(timeout=10_000)
            allure.attach(
                f"Global Configuration visible by default: {gc_visible}",
                name="Global Config default visibility",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert gc_visible, (
                "Global Configuration section not visible by default on Settings page. "
                "Expected it to be the default tab."
            )

        with allure.step("Assert Ingestion Model dropdown is visible"):
            ingestion_visible = settings_page.is_visible(
                settings_page.ingestion_model_dropdown, timeout=8_000
            )
            allure.attach(
                f"Ingestion Model dropdown visible: {ingestion_visible}",
                name="Ingestion Model dropdown",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert ingestion_visible, (
                "Ingestion Model dropdown not visible on Global Config page."
            )

        with allure.step("Assert Enable AskAuto toggle is visible"):
            askauto_visible = settings_page.is_visible(
                settings_page.enable_ask_auto_toggle, timeout=8_000
            )
            allure.attach(
                f"Enable AskAuto toggle visible: {askauto_visible}",
                name="Enable AskAuto toggle",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert askauto_visible, (
                "Enable AskAuto toggle not visible on Global Config page."
            )

        with allure.step("Assert Save Settings button is present"):
            save_visible = settings_page.is_save_button_visible(timeout=5_000)
            allure.attach(
                f"Save Settings button visible: {save_visible}",
                name="Save button visibility",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert save_visible, "Save Settings button not found on Global Configuration page."

    @allure.story("Business Unit Configuration")
    @allure.title("[TC_SM_042] Business Unit Config tab loads with BU list and toggles")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Click the Business Unit Config tab and verify:\n"
        "  • The BU Config section loads.\n"
        "  • The left panel shows at least one Business Unit entry.\n"
        "  • Clicking the first BU loads the right panel with toggle controls.\n"
        "  • The Save Settings button is visible."
    )
    def test_business_unit_configuration_loads(self, settings_page: SettingsPage):
        with allure.step("Navigate to Settings"):
            settings_page.open_direct()
            assert settings_page.is_loaded(timeout=15_000), "Settings page did not load."

        with allure.step("Click Business Unit Config tab"):
            settings_page.click_bu_config_tab()

        with allure.step("Assert Business Unit Config section is visible"):
            bu_visible = settings_page.is_bu_config_visible(timeout=10_000)
            allure.attach(
                f"BU Config visible: {bu_visible}",
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
                f"Selected BU: {bu_name or '(first item)'}",
                name="Selected BU",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Assert Auto Correct Address (Letter) toggle is visible"):
            toggle_visible = settings_page.is_visible(
                settings_page.auto_correct_address_letter_toggle, timeout=8_000
            )
            allure.attach(
                f"Auto Correct Address (Letter) toggle visible: {toggle_visible}",
                name="Toggle visibility",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert toggle_visible, (
                "Auto Correct Address (Letter) toggle not visible in the BU configuration panel."
            )

        with allure.step("Assert Save Settings button is visible"):
            save_visible = settings_page.is_save_button_visible(timeout=5_000)
            allure.attach(
                f"Save Settings button visible: {save_visible}",
                name="Save button visibility",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert save_visible, "Save Settings button not found on Business Unit Config page."

    @allure.story("Business Unit Configuration – Toggle Save & Undo")
    @allure.title(
        "[TC_SM_043] BU Config: toggle Auto Correct Address, save, verify, undo, save, verify"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Open Business Unit Config, select the first BU, then:\n"
        "  1. Read the initial state of the 'Auto Correct Address (Letter)' toggle.\n"
        "  2. Toggle it to the opposite state → click Save Settings → verify success.\n"
        "  3. Undo (toggle back to original state) → click Save Settings → verify success."
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
                f"Selected BU: {bu_name or '(first item)'}",
                name="Selected BU",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Assert Auto Correct Address (Letter) toggle is accessible"):
            toggle = settings_page.auto_correct_address_letter_toggle
            toggle_visible = settings_page.is_visible(toggle, timeout=8_000)
            allure.attach(
                f"Toggle accessible: {toggle_visible}",
                name="Toggle accessibility",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert toggle_visible, (
                "Auto Correct Address (Letter) toggle not visible — cannot proceed with save test."
            )

        with allure.step("Read initial toggle state"):
            initial_state = settings_page.is_toggle_checked(toggle)
            allure.attach(
                f"Initial toggle state (checked): {initial_state}",
                name="Initial state",
                attachment_type=allure.attachment_type.TEXT,
            )

        # ── Step 1: Toggle → Save → Verify ────────────────────────────────────
        with allure.step(f"Toggle Auto Correct Address (Letter) to {'OFF' if initial_state else 'ON'}"):
            settings_page.click_toggle(toggle, "Auto Correct Address (Letter)")
            after_toggle_state = settings_page.is_toggle_checked(toggle)
            allure.attach(
                f"State after first toggle: {after_toggle_state}",
                name="State after toggle",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Click Save Settings and verify success"):
            saved = settings_page.click_save_settings()
            allure.attach(
                f"Save success toast appeared: {saved}",
                name="Save result (step 1)",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert saved, (
                "Save Settings did not show a success confirmation after toggling "
                "Auto Correct Address (Letter)."
            )

        # ── Step 2: Undo toggle → Save → Verify ───────────────────────────────
        with allure.step(f"Undo: toggle back to {'ON' if initial_state else 'OFF'}"):
            settings_page.click_toggle(toggle, "Auto Correct Address (Letter) undo")
            after_undo_state = settings_page.is_toggle_checked(toggle)
            allure.attach(
                f"State after undo toggle: {after_undo_state}",
                name="State after undo",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Click Save Settings and verify success after undo"):
            saved_undo = settings_page.click_save_settings()
            allure.attach(
                f"Save success toast appeared (undo): {saved_undo}",
                name="Save result (step 2)",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert saved_undo, (
                "Save Settings did not show a success confirmation after undoing "
                "the Auto Correct Address (Letter) toggle."
            )
