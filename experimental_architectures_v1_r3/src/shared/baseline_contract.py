"""Fail-closed admission for the unchanged native baseline's fixed interface."""
from dataclasses import asdict,dataclass
from cognitive_architecture_lab_v1.src.interfaces.contracts import RunRequest
from runtime_isolation_v1.src.capability_policy.policy import BoundaryError
from native_model_integration_v1.src.native_end_bridge.bridge import approved_prompt
from .strict_json import canonical,sha
class ContractAdmissionError(BoundaryError):pass
@dataclass(frozen=True)
class BaselineContract:
    model_identity:str='qwen3:4b'
    model_digest:str='UNOBSERVED_NO_MODEL_QUERIED'
    temperature:float=.7
    top_p:float=.8
    think:bool=False
    seed:None=None
    context_window:int=8192
    maximum_output_tokens:int=4096
    physical_attempts:int=36
    token_budget:int=400000
    wall_time_budget:int=1800
    provider_capabilities:tuple=('OFFLINE_SYNTHETIC_RECORDING_ONLY','STATELESS_NO_TOOLS','OLLAMA_API_GENERATE')
SUPPORTED=BaselineContract()
def admit(request):
    if type(request) is not RunRequest or request.condition_id not in ('DIRECT','SELF_REFLECT','FROZEN_CURRENT_END'):raise ContractAdmissionError('TYPED_BASELINE_REQUEST_REQUIRED')
    try:
        request.wire();approved_prompt(request.public_task_payload)
        actual={'model_identity':request.model_identity,'model_digest':request.model_digest,'temperature':request.generation_parameters['temperature'],'top_p':request.generation_parameters['top_p'],'think':request.generation_parameters['think'],'seed':request.seed_if_supported,'context_window':request.context_window,'maximum_output_tokens':request.maximum_output_tokens,'physical_attempts':request.attempt_budget,'token_budget':request.token_budget,'wall_time_budget':request.wall_time_budget,'provider_capabilities':SUPPORTED.provider_capabilities}
        if canonical(actual)!=canonical(asdict(SUPPORTED)):raise ContractAdmissionError('UNSUPPORTED_BASELINE_CONTRACT_NO_RESERVATION')
    except (ValueError,TypeError,KeyError,BoundaryError) as e:raise ContractAdmissionError('BASELINE_ADMISSION_REJECTED_BEFORE_RESERVATION') from e
    return {'requested_sha256':sha(canonical(asdict(request))),'admitted_effective_sha256':sha(canonical(asdict(request))),'supported_configuration':asdict(SUPPORTED),'public_task_sha256':sha(canonical(request.public_task_payload)),'condition_id':request.condition_id,'policy':'EXACT_DEFAULT_OR_REJECT_BEFORE_RESERVATION'}
