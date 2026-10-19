"""Frozen-teacher actual-deletion labels and cache identity checks."""

from .cache import CACHE_SCHEMA_VERSION, load_deletion_labels, save_deletion_labels
from .deletion import LABEL_VERSION, DeletionLabels, DeletionTeacher, FullTeacherReference, LabelProvenance, feature_fingerprint, retained_indices

__all__ = ["CACHE_SCHEMA_VERSION", "LABEL_VERSION", "DeletionLabels", "DeletionTeacher", "FullTeacherReference",
           "LabelProvenance", "feature_fingerprint", "retained_indices", "load_deletion_labels", "save_deletion_labels"]
