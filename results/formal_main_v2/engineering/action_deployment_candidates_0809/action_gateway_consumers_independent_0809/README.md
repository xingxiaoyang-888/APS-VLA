# Gateway and raw-consumer independent CPU review

Only server files under this audit directory were written. No production state, reservation, Slurm/GPU submission, model loading, Git write or sealed-state read occurred.

Gateway: final SHA 8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a; 18 independent fault cases plus 78 author cases independently rerun, 96 passed. Actual historical 237-row sacct output was reparsed, including its empty Comment column. R/S frozen 173 files were rehashed. The earlier independent two-assertion failure, test source and logs remain intact with the exact correction explained in gateway_independent_review.json.

Raw consumer: reviewer 9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd and consumer 16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034; 18 independent cases plus 62 author cases independently rerun, 80 passed. The construction-version final-registry metadata and Evidence API gaps were fixed and checked. Original terminal policy_error rows remain terminal; new identity/runtime/partial-result flags cannot replace raw reconstruction.

Typed receipts bind only those independent components and allow byte-identical copying to the stated production paths, followed by root rehash. They are not per-plan readiness or full GPU-chain proof. This auditor authored runtime_scope earlier and does not independently sign that component. Actual new wrapper/runtime/raw-review end-to-end GPU evidence is still pending.
