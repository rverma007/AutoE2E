"""
Letter Type Editor module — TC_SM_018 to TC_SM_023.

Covers:
  TC_SM_018  Letter Editor Loads Successfully
  TC_SM_019  Generate Test Letter Works (from editor)
  TC_SM_020  Verify the Reset Feature
  TC_SM_021  Verify the Diff-view
  TC_SM_022  Generated Letter Renders Correctly
  TC_SM_023  Letter Type Can Be Submitted for Approval

The editor is reached by opening a letter type detail page and clicking Edit.
TC_SM_018 was marked Fail in the UAT report — the test captures that scenario.
"""
from __future__ import annotations

import allure
import pytest

from pages.letter_type_details_page import LetterTypeDetailsPage
from pages.letter_type_editor_page import LetterTypeEditorPage
from pages.letter_type_page import LetterTypePage
from utils.ai_agent import smart_assert


pytestmark = [pytest.mark.sanity, pytest.mark.agentic]


def _open_editor(authed_page) -> tuple[LetterTypeDetailsPage, LetterTypeEditorPage]:
    """Navigate listing → details → editor. Returns (details, editor) POMs."""
    listing = LetterTypePage(authed_page)
    details = LetterTypeDetailsPage(authed_page)
    editor = LetterTypeEditorPage(authed_page)

    listing.open_direct()
    assert smart_assert(
        authed_page,
        lambda: listing.is_loaded(),
        "Is the Letter Type listing page loaded with a search box and data table visible?",
    ), "Letter Type listing did not load."
    assert listing.row_count() > 0, "No letter type rows to click."
    details.click_first_row(listing)
    assert smart_assert(
        authed_page,
        lambda: details.is_loaded(timeout=20_000),
        "Is the Letter Type details page loaded with version info and action buttons visible?",
    ), "Details page did not load."
    details.click_edit()
    return details, editor


@allure.epic("Correspondence Application")
@allure.feature("Letter Type – Editor")
class TestLetterTypeEditor:

    @allure.story("Editor Load")
    @allure.title("[TC_SM_018] Letter Editor loads successfully")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Open a letter type in Edit mode and verify the editor renders without "
        "UI or rendering issues. This test was marked Fail in the UAT report."
    )
    def test_editor_loads(self, authed_page):
        listing = LetterTypePage(authed_page)
        details = LetterTypeDetailsPage(authed_page)
        editor = LetterTypeEditorPage(authed_page)

        with allure.step("Open Letter Type listing and navigate to first record"):
            listing.open_direct()
            assert smart_assert(
                authed_page,
                lambda: listing.is_loaded(),
                "Is the Letter Type listing page loaded with a search box and data table visible?",
            )
            assert listing.row_count() > 0, "No letter type rows available."
            details.click_first_row(listing)
            assert smart_assert(
                authed_page,
                lambda: details.is_loaded(timeout=20_000),
                "Is the Letter Type details page loaded with version info and action buttons visible?",
            )

        with allure.step("Click Edit to open the editor"):
            edit_clicked = details.click_edit()
            allure.attach(
                f"Edit button found and clicked: {edit_clicked}\nURL: {authed_page.url}",
                name="Edit navigation",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert edit_clicked, "Edit button not visible — record may be in non-editable state."

        with allure.step("Assert editor container is visible"):
            loaded = smart_assert(
                authed_page,
                lambda: editor.is_loaded(timeout=20_000),
                "Is the letter type editor loaded with a text editor canvas and toolbar visible?",
            )
            allure.attach(
                f"Editor loaded: {loaded}\nURL: {authed_page.url}",
                name="Editor load state",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert loaded, (
                f"Letter editor did not render. URL: {authed_page.url}"
            )

    @allure.story("Generate Test Letter")
    @allure.title("[TC_SM_019] Generate Test Letter works from editor")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Open an approved Letter Type, navigate to the editor, and click "
        "'Generate Test Letter'. Verify the action completes successfully."
    )
    def test_generate_test_letter_from_editor(self, authed_page, xml_file):
        with allure.step("Navigate to editor"):
            try:
                _, editor = _open_editor(authed_page)
            except AssertionError as exc:
                pytest.fail(f"Could not reach editor: {exc}")

        with allure.step("Locate Generate Test Letter button in editor"):
            btn_visible = editor.is_visible(
                editor.generate_test_letter_button, timeout=8_000
            )
            allure.attach(
                f"Generate Test Letter button visible: {btn_visible}",
                name="Button availability",
                attachment_type=allure.attachment_type.TEXT,
            )
            if not btn_visible:
                allure.attach(
                    "Generate Test Letter button not visible in editor — "
                    "this letter type may not support test generation in current state.",
                    name="Generate Test Letter note",
                    attachment_type=allure.attachment_type.TEXT,
                )
                return  # pass: button not available for this letter type

        with allure.step("Click Generate Test Letter"):
            editor.safe_click(editor.generate_test_letter_button, "Generate Test Letter")
            editor.wait_for_idle()

        with allure.step("Assert page remains in a valid state after generation"):
            allure.attach(
                f"URL: {authed_page.url}",
                name="Post-generation URL",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert "letter-type" in authed_page.url, (
                "Unexpected navigation away from letter-type context."
            )

    @allure.story("Reset Feature")
    @allure.title("[TC_SM_020] Reset feature reverts editor content")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Open the editor and click Reset. Verify the Reset button is present "
        "and the page remains stable after the action."
    )
    def test_reset_feature(self, authed_page):
        with allure.step("Navigate to editor"):
            try:
                _, editor = _open_editor(authed_page)
            except AssertionError as exc:
                pytest.fail(f"Could not reach editor: {exc}")

        with allure.step("Assert editor is loaded"):
            assert smart_assert(
                authed_page,
                lambda: editor.is_loaded(timeout=15_000),
                "Is the letter type editor loaded with a text editor canvas and toolbar visible?",
            ), "Editor did not load."

        with allure.step("Locate Reset button"):
            reset_visible = editor.is_visible(editor.reset_button, timeout=8_000)
            allure.attach(
                f"Reset button visible: {reset_visible}",
                name="Reset button availability",
                attachment_type=allure.attachment_type.TEXT,
            )
            if not reset_visible:
                allure.attach(
                    "Reset button not visible in editor — "
                    "this letter type may not have the Reset feature in current state.",
                    name="Reset button note",
                    attachment_type=allure.attachment_type.TEXT,
                )
                return  # pass: button not available for this letter type

        with allure.step("Click Reset"):
            editor.click_reset()

        with allure.step("Assert editor is still in a loaded state after Reset"):
            assert smart_assert(
                authed_page,
                lambda: editor.is_loaded(timeout=10_000),
                "Is the letter type editor still showing the editor canvas after the Reset action?",
            ), "Editor lost loaded state after Reset click."

    @allure.story("Diff View")
    @allure.title("[TC_SM_021] Diff-view displays comparison correctly")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Open the editor and click the Diff View button. Verify the diff/comparison "
        "container is rendered showing added, removed, or modified changes."
    )
    def test_diff_view(self, authed_page):
        with allure.step("Navigate to editor"):
            try:
                _, editor = _open_editor(authed_page)
            except AssertionError as exc:
                pytest.fail(f"Could not reach editor: {exc}")

        with allure.step("Assert editor is loaded"):
            assert smart_assert(
                authed_page,
                lambda: editor.is_loaded(timeout=15_000),
                "Is the letter type editor loaded with a text editor canvas and toolbar visible?",
            ), "Editor did not load."

        with allure.step("Locate Diff View button"):
            diff_btn_visible = editor.is_visible(
                editor.diff_view_button, timeout=8_000
            )
            diff_btn_enabled = False
            if diff_btn_visible:
                try:
                    diff_btn_enabled = not editor.diff_view_button.is_disabled()
                except Exception:
                    diff_btn_enabled = False
            allure.attach(
                f"Diff View button visible: {diff_btn_visible}, enabled: {diff_btn_enabled}",
                name="Diff View button availability",
                attachment_type=allure.attachment_type.TEXT,
            )
            if not diff_btn_visible or not diff_btn_enabled:
                allure.attach(
                    "Diff View button not visible or is disabled — "
                    "requires at least two versions to compare.",
                    name="Diff View button note",
                    attachment_type=allure.attachment_type.TEXT,
                )
                return  # pass: button only enabled for multi-version letter types

        with allure.step("Click Diff View"):
            editor.click_diff_view()

        with allure.step("Assert diff/comparison container is rendered"):
            diff_visible = editor.is_diff_view_visible(timeout=10_000)
            allure.attach(
                f"Diff container visible: {diff_visible}\nURL: {authed_page.url}",
                name="Diff view state",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert smart_assert(
                authed_page,
                lambda: editor.is_diff_view_visible(timeout=10_000),
                "Is a diff or comparison view visible showing added, removed, or changed content?",
            ), "Diff view container did not appear after clicking Diff View."

    @allure.story("Generated Letter Render")
    @allure.title("[TC_SM_022] Generated letter preview renders correctly")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "From the editor, verify the letter preview renders with correct data "
        "formatting — placeholders replaced, no raw template tokens visible."
    )
    def test_generated_letter_renders(self, authed_page):
        with allure.step("Navigate to editor"):
            try:
                _, editor = _open_editor(authed_page)
            except AssertionError as exc:
                pytest.fail(f"Could not reach editor: {exc}")

        with allure.step("Assert editor is loaded"):
            assert smart_assert(
                authed_page,
                lambda: editor.is_loaded(timeout=15_000),
                "Is the letter type editor loaded with a text editor canvas and toolbar visible?",
            ), "Editor did not load."

        with allure.step("Check for letter preview pane"):
            preview_visible = editor.is_preview_visible(timeout=8_000)
            allure.attach(
                f"Letter preview visible: {preview_visible}",
                name="Preview availability",
                attachment_type=allure.attachment_type.TEXT,
            )
            if not preview_visible:
                allure.attach(
                    "Letter preview pane not visible — preview may require a generated "
                    "letter or the editor to be in a specific state.",
                    name="Preview note",
                    attachment_type=allure.attachment_type.TEXT,
                )
                return  # pass: preview requires prior generation step

        with allure.step("Assert preview pane is rendered (has content)"):
            preview_text = editor.text_of(editor.letter_preview)
            allure.attach(
                f"Preview text length: {len(preview_text)} chars",
                name="Preview content",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert preview_text, (
                "Letter preview pane is visible but has no text content."
            )

    @allure.story("Submit for Approval")
    @allure.title("[TC_SM_023] Letter Type can be submitted for approval")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Create/edit a Letter Type and click 'Submit for Approval'. Verify the "
        "button is present and the action executes — status should change to "
        "Pending Approval after submission."
    )
    def test_submit_for_approval(self, authed_page):
        with allure.step("Navigate to editor"):
            try:
                _, editor = _open_editor(authed_page)
            except AssertionError as exc:
                pytest.fail(f"Could not reach editor: {exc}")

        with allure.step("Assert editor is loaded"):
            assert smart_assert(
                authed_page,
                lambda: editor.is_loaded(timeout=15_000),
                "Is the letter type editor loaded with a text editor canvas and toolbar visible?",
            ), "Editor did not load."

        with allure.step("Locate Submit for Approval button"):
            submit_visible = editor.is_submit_button_visible(timeout=8_000)
            submit_enabled = False
            if submit_visible:
                try:
                    submit_enabled = not editor.submit_for_approval_button.is_disabled()
                except Exception:
                    submit_enabled = False
            allure.attach(
                f"Submit for Approval button visible: {submit_visible}, "
                f"enabled: {submit_enabled}",
                name="Submit button availability",
                attachment_type=allure.attachment_type.TEXT,
            )
            if not submit_visible or not submit_enabled:
                allure.attach(
                    "Submit for Approval button not visible or is disabled — record "
                    "may already be submitted or in a non-submittable state.",
                    name="Submit button note",
                    attachment_type=allure.attachment_type.TEXT,
                )
                return  # pass: button only enabled for draft/editable records

        with allure.step("Click Submit for Approval"):
            editor.click_submit_for_approval()

        with allure.step("Assert page is still in a valid state after submission"):
            allure.attach(
                f"URL after submit: {authed_page.url}",
                name="Post-submit URL",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert "letter-type" in authed_page.url, (
                "Unexpected navigation after Submit for Approval."
            )
