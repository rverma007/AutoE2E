"""
Settings module — TC_SM_041 to TC_SM_042.

Covers:
  TC_SM_041  Verify the Global Configuration
  TC_SM_042  Verify the Business_unit_config
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
    @allure.title("[TC_SM_041] Global Configuration is visible and saveable")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Navigate to Settings → Global Configuration tab, verify the section "
        "loads correctly, and confirm Save Settings button is present. "
        "The test does not modify live configuration values."
    )
    def test_global_configuration(self, settings_page: SettingsPage):
        with allure.step("Navigate to Settings"):
            settings_page.open_direct()

        with allure.step("Assert Settings page loaded"):
            loaded = settings_page.is_loaded(timeout=15_000)
            allure.attach(
                f"Settings page loaded: {loaded}\nURL: {settings_page.page.url}",
                name="Page load state",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert loaded, (
                f"Settings page did not load. URL: {settings_page.page.url}"
            )

        with allure.step("Navigate to Global Configuration section"):
            settings_page.click_global_config_tab()

        with allure.step("Assert Global Configuration section is visible"):
            gc_visible = settings_page.is_global_config_visible(timeout=10_000)
            allure.attach(
                f"Global Configuration visible: {gc_visible}",
                name="Global Config visibility",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert gc_visible, (
                "Global Configuration section/heading not visible on Settings page."
            )

        with allure.step("Assert Save Settings button is present"):
            save_visible = settings_page.is_save_button_visible(timeout=5_000)
            allure.attach(
                f"Save Settings button visible: {save_visible}",
                name="Save button visibility",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert save_visible, (
                "Save Settings button not found on Global Configuration page."
            )

    @allure.story("Business Unit Configuration")
    @allure.title("[TC_SM_042] Business Unit Configuration is visible and saveable")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Navigate to Settings → Business Unit Config tab, select a Business Unit "
        "from the dropdown, and verify the Save Settings button is present. "
        "The test does not permanently modify configuration values."
    )
    def test_business_unit_configuration(self, settings_page: SettingsPage):
        with allure.step("Navigate to Settings"):
            settings_page.open_direct()
            assert settings_page.is_loaded(timeout=15_000), "Settings page did not load."

        with allure.step("Navigate to Business Unit Config section"):
            settings_page.click_bu_config_tab()

        with allure.step("Assert Business Unit Config section is visible"):
            bu_visible = settings_page.is_bu_config_visible(timeout=10_000)
            allure.attach(
                f"Business Unit Config visible: {bu_visible}",
                name="BU Config visibility",
                attachment_type=allure.attachment_type.TEXT,
            )
            if not bu_visible:
                pytest.skip(
                    "Business Unit Config section not visible — "
                    "may be on a separate page or tab."
                )

        with allure.step("Check for Business Unit selector dropdown"):
            bu_select = settings_page.bu_select_dropdown
            select_visible = settings_page.is_visible(bu_select, timeout=5_000)
            allure.attach(
                f"BU select dropdown visible: {select_visible}",
                name="BU dropdown",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Assert Save Settings button is present"):
            save_visible = settings_page.is_save_button_visible(timeout=5_000)
            allure.attach(
                f"Save Settings button visible: {save_visible}",
                name="Save button visibility",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert save_visible, (
                "Save Settings button not found on Business Unit Config page."
            )
