from diwa import PUBLIC_PROJECT_NAME, PUBLIC_PROJECT_SHORT_NAME


def test_public_project_name_is_frozen_and_import_path_is_compatible():
    assert PUBLIC_PROJECT_SHORT_NAME == "CTI-VLA"
    assert PUBLIC_PROJECT_NAME == "Counterfactual Token Influence for Efficient Vision-Language-Action Policies"
