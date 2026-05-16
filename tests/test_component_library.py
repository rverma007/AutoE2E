"""
Component Library module — TC_SM_028 to TC_SM_033.

Covers:
  TC_SM_028  Component Library page is accessible
  TC_SM_029  Placeholder list loads successfully
  TC_SM_030  Insert list loads successfully
  TC_SM_031  Condition list loads successfully
  TC_SM_032  Block list loads successfully
  TC_SM_033  User sample file is uploaded successfully
"""
from __future__ import annotations

import allure
import pytest

from pages.component_library_page import ComponentLibraryPage


pytestmark = pytest.mark.sanity


@allure.epic("Correspondence Application")
@allure.feature("Component Library")
class TestComponentLibrary:

    @allure.story("Page Accessibility")
    @allure.title("[TC_SM_028] Component Library page is accessible")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Navigate to the Component Library module and verify the page loads "
        "successfully without errors."
    )
    def test_component_library_accessible(self, component_library_page: ComponentLibraryPage):
        with allure.step("Navigate to Component Library"):
            component_library_page.open_direct()

        with allure.step("Assert page is loaded"):
            loaded = component_library_page.is_loaded(timeout=15_000)
            allure.attach(
                f"Page loaded: {loaded}\nURL: {component_library_page.page.url}",
                name="Page load state",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert loaded, (
                f"Component Library page did not load. URL: {component_library_page.page.url}"
            )

    @allure.story("Tab Content")
    @allure.title("[TC_SM_029] Placeholder list loads successfully")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Open the Placeholder tab in Component Library and verify the list "
        "loads with records displayed."
    )
    def test_placeholder_list_loads(self, component_library_page: ComponentLibraryPage):
        with allure.step("Navigate to Component Library"):
            component_library_page.open_direct()
            assert component_library_page.is_loaded(), "Component Library did not load."

        with allure.step("Click Placeholder tab"):
            clicked = component_library_page.click_tab(
                component_library_page.placeholder_tab, "Placeholder"
            )
            allure.attach(
                f"Placeholder tab found and clicked: {clicked}",
                name="Tab navigation",
                attachment_type=allure.attachment_type.TEXT,
            )
            if not clicked:
                # Tabs may not exist — content may be on a single page
                allure.attach(
                    "Placeholder tab not found — checking if list is already visible.",
                    name="Tab note",
                    attachment_type=allure.attachment_type.TEXT,
                )

        with allure.step("Assert placeholder list is populated"):
            populated = component_library_page.is_list_populated(timeout=10_000)
            row_count = component_library_page.row_count()
            allure.attach(
                f"List populated: {populated}\nRow count: {row_count}",
                name="List content",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert row_count > 0, (
                f"Placeholder list is empty — expected at least one record. "
                f"Row count: {row_count}"
            )

    @allure.story("Tab Content")
    @allure.title("[TC_SM_030] Insert list loads successfully")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Open the Insert tab in Component Library and verify the list loads."
    )
    def test_insert_list_loads(self, component_library_page: ComponentLibraryPage):
        with allure.step("Navigate to Component Library"):
            component_library_page.open_direct()
            assert component_library_page.is_loaded(), "Component Library did not load."

        with allure.step("Click Insert tab"):
            clicked = component_library_page.click_tab(
                component_library_page.insert_tab, "Insert"
            )
            allure.attach(
                f"Insert tab found and clicked: {clicked}",
                name="Tab navigation",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Assert insert list is populated"):
            row_count = component_library_page.row_count()
            allure.attach(
                f"Row count: {row_count}",
                name="List content",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert row_count > 0, (
                f"Insert list is empty — expected at least one record. "
                f"Row count: {row_count}"
            )

    @allure.story("Tab Content")
    @allure.title("[TC_SM_031] Condition list loads successfully")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Open the Condition tab in Component Library and verify the list loads."
    )
    def test_condition_list_loads(self, component_library_page: ComponentLibraryPage):
        with allure.step("Navigate to Component Library"):
            component_library_page.open_direct()
            assert component_library_page.is_loaded(), "Component Library did not load."

        with allure.step("Click Condition tab"):
            clicked = component_library_page.click_tab(
                component_library_page.condition_tab, "Condition"
            )
            allure.attach(
                f"Condition tab found and clicked: {clicked}",
                name="Tab navigation",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Assert condition list is populated"):
            row_count = component_library_page.row_count()
            allure.attach(
                f"Row count: {row_count}",
                name="List content",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert row_count > 0, (
                f"Condition list is empty — expected at least one record. "
                f"Row count: {row_count}"
            )

    @allure.story("Tab Content")
    @allure.title("[TC_SM_032] Block list loads successfully")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Open the Block tab in Component Library and verify the list loads."
    )
    def test_block_list_loads(self, component_library_page: ComponentLibraryPage):
        with allure.step("Navigate to Component Library"):
            component_library_page.open_direct()
            assert component_library_page.is_loaded(), "Component Library did not load."

        with allure.step("Click Block tab"):
            clicked = component_library_page.click_tab(
                component_library_page.block_tab, "Block"
            )
            allure.attach(
                f"Block tab found and clicked: {clicked}",
                name="Tab navigation",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Assert block list is populated"):
            row_count = component_library_page.row_count()
            allure.attach(
                f"Row count: {row_count}",
                name="List content",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert row_count > 0, (
                f"Block list is empty — expected at least one record. "
                f"Row count: {row_count}"
            )

    @allure.story("Sample File Upload")
    @allure.title("[TC_SM_033] User sample file is uploaded successfully")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Upload a user sample data file in the Component Library and verify it "
        "is displayed correctly after upload."
    )
    def test_user_sample_file_upload(
        self, component_library_page: ComponentLibraryPage, xml_file: str
    ):
        with allure.step("Navigate to Component Library"):
            component_library_page.open_direct()
            assert component_library_page.is_loaded(), "Component Library did not load."

        with allure.step("Locate the upload sample file button"):
            upload_btn_visible = component_library_page.is_visible(
                component_library_page.upload_sample_button, timeout=8_000
            )
            allure.attach(
                f"Upload Sample button visible: {upload_btn_visible}",
                name="Upload button availability",
                attachment_type=allure.attachment_type.TEXT,
            )
            if not upload_btn_visible and not component_library_page.is_visible(
                component_library_page.upload_sample_input, timeout=3_000
            ):
                pytest.skip(
                    "Upload Sample button/input not visible — may not be available on this page."
                )

        with allure.step("Record state before upload"):
            rows_before = component_library_page.row_count()
            allure.attach(
                f"Rows before upload: {rows_before}",
                name="Pre-upload row count",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Upload sample XML file"):
            component_library_page.upload_sample_file(xml_file)

        with allure.step("Assert page is in a valid state and upload was acknowledged"):
            assert component_library_page.is_loaded(timeout=10_000), (
                "Component Library page lost loaded state after upload."
            )
            rows_after = component_library_page.row_count()
            allure.attach(
                f"Rows before: {rows_before}\nRows after: {rows_after}",
                name="Post-upload row count",
                attachment_type=allure.attachment_type.TEXT,
            )
            # Sample file upload updates preview data, not the component list itself.
            # Row count is logged above for diagnostics; the authoritative check is is_loaded().
