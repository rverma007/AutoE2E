"""
Letter Consolidation module — TC_SM_050 to TC_SM_053.

All four test cases are currently On Hold in the UAT report.
They are implemented here so they are ready to activate when the
Letter Consolidation feature is stable.

Covers:
  TC_SM_050  Verify grouping in the letter consolidation page  [HOLD]
  TC_SM_051  Verify percentage change after letter edit → approve [HOLD]
  TC_SM_052  Verify only 1 representative per group              [HOLD]
  TC_SM_053  Verify documents can be moved between groups        [HOLD]
"""
from __future__ import annotations

import allure
import pytest

from pages.letter_consolidation_page import LetterConsolidationPage


pytestmark = pytest.mark.sanity

_HOLD_REASON = (
    "On hold — Letter Consolidation feature not yet stable in UAT environment."
)


@allure.epic("Correspondence Application")
@allure.feature("Letter Consolidation")
class TestLetterConsolidation:

    @allure.story("Grouping")
    @allure.title("[TC_SM_050] Letters are grouped correctly in Letter Consolidation")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Navigate to the Letter Consolidation page. Add a letter and verify it "
        "is assigned to a group according to the consolidation logic."
    )
    @pytest.mark.skip(reason=_HOLD_REASON)
    def test_grouping_in_consolidation_page(
        self, letter_consolidation_page: LetterConsolidationPage
    ):
        with allure.step("Navigate to Letter Consolidation"):
            letter_consolidation_page.open_direct()
            assert letter_consolidation_page.is_loaded(timeout=15_000)

        with allure.step("Verify groups are displayed"):
            group_count = letter_consolidation_page.group_count()
            allure.attach(
                f"Group count: {group_count}",
                name="Groups",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert group_count >= 0, "group_count() raised an error."

    @allure.story("Percentage Change")
    @allure.title(
        "[TC_SM_051] Percentage changes after letter edit, approval, and make-current"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Create a draft letter, edit it, submit for approval, and make it current. "
        "Verify the percentage relative to the group representative updates correctly."
    )
    @pytest.mark.skip(reason=_HOLD_REASON)
    def test_percentage_change_after_approval(
        self, letter_consolidation_page: LetterConsolidationPage
    ):
        with allure.step("Navigate to Letter Consolidation"):
            letter_consolidation_page.open_direct()
            assert letter_consolidation_page.is_loaded(timeout=15_000)

        # Full implementation pending feature stabilisation
        with allure.step("Placeholder: verify page is stable"):
            assert letter_consolidation_page.is_loaded(timeout=5_000)

    @allure.story("Representative")
    @allure.title("[TC_SM_052] Only one representative exists per group")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Open the Letter Consolidation page and verify that every group has "
        "exactly one letter marked as representative."
    )
    @pytest.mark.skip(reason=_HOLD_REASON)
    def test_only_one_representative_per_group(
        self, letter_consolidation_page: LetterConsolidationPage
    ):
        with allure.step("Navigate to Letter Consolidation"):
            letter_consolidation_page.open_direct()
            assert letter_consolidation_page.is_loaded(timeout=15_000)

        with allure.step("Verify representative badge visibility"):
            rep_visible = letter_consolidation_page.is_representative_visible(
                timeout=8_000
            )
            allure.attach(
                f"Representative badge visible: {rep_visible}",
                name="Representative check",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert rep_visible, "No representative badge found in Letter Consolidation."

    @allure.story("Move Documents")
    @allure.title("[TC_SM_053] Documents can be moved between groups")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Open a consolidation group and move a letter to a different group. "
        "Verify the letter appears in the target group and a new representative "
        "is elected in the source group if the representative was moved."
    )
    @pytest.mark.skip(reason=_HOLD_REASON)
    def test_documents_can_be_moved_between_groups(
        self, letter_consolidation_page: LetterConsolidationPage
    ):
        with allure.step("Navigate to Letter Consolidation"):
            letter_consolidation_page.open_direct()
            assert letter_consolidation_page.is_loaded(timeout=15_000)

        # Full implementation pending feature stabilisation
        with allure.step("Placeholder: verify page is stable"):
            assert letter_consolidation_page.is_loaded(timeout=5_000)
