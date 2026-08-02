"""Decision influence estimator and paired teacher."""

from .die import DecisionInfluenceEstimator
from .sampling import CandidateSet, CoverageAudit, TeacherCandidateSampler, compute_coverage_audit
from .teacher import CandidateTeacherTargets, CounterfactualTeacher, TeacherTargets

__all__ = [
    "CandidateSet",
    "CandidateTeacherTargets",
    "CounterfactualTeacher",
    "CoverageAudit",
    "DecisionInfluenceEstimator",
    "TeacherCandidateSampler",
    "TeacherTargets",
    "compute_coverage_audit",
]
