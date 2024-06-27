import logging
import cerberus
from models.qos_template.models import Workflows
from common.exception import TaskNotRegisteredException, ParamsNotValidException
from workflow.core.register_task import REGISTER_WORKFLOWS
logger = logging.getLogger(__file__)


def validate_params(params, schema):
    """Validates JSON params with a Cerberus schema."""
    validator = cerberus.Validator()
    validator.allow_unknown = True
    is_valid = validator.validate(params, schema)
    if not is_valid:
        err = f"Inputs did not match schema.\n\tInputs: {params}\n\tSchema: {schema}\n\tErrors: {validator.errors}"
        raise ParamsNotValidException(err)


def prepare_workflow(task_handler, workflow):
    schema = task_handler.params_schema()
    schema.update(
        {
            'customer_id': {'type': 'string'},
            'site_id': {'type': 'string', 'nullable': True},
            'lock_params': {'type': 'dict', 'nullable': True}
        }
    )

    if "site_name" in workflow.params:
        schema.update({"site_name": {'type': 'string'}})

    if "pk" in workflow.params:
        schema.update({"pk": {'type': 'string'}})

    if "core_type" in workflow.params:
        schema.update({"core_type": {'type': 'string'}})

    if "callback_service" in workflow.params:
        schema.update({"callback_service": {'type': 'string'}})

    # 分布式trace
    if "trace_headers" in workflow.params:
        schema.update(
            {
                "trace_headers": {'type': 'dict'}
            }
        )

    validate_params(workflow.params, schema)
    logger.info("check params success")
    # 批量实例参数生成
    if hasattr(task_handler, "prepare_parallel"):
        if 'parallel_params' not in workflow.result or workflow.error_step == Workflows.PREPARE_PARALLEL:
            parallel_params = task_handler.prepare_parallel(workflow.params)
            workflow.result.update(parallel_params=parallel_params)
            workflow.save(update_fields=['result'])
        else:
            parallel_params = workflow.result.get('parallel_params')
        workflow.params.update(parallel_params)

    return workflow.params


class WorkflowExecutor:
    @classmethod
    def execute(cls, workflow):
        logger.info(f"{workflow.id}: Start do waiting workflow =========>: {workflow.workflow_type}")
        if workflow.workflow_type not in REGISTER_WORKFLOWS:
            raise TaskNotRegisteredException(f"{workflow.id}: flow workflow_type: {workflow.workflow_type} "
                                             f"is not support!")

        task_handler = REGISTER_WORKFLOWS.get(workflow.workflow_type)
        # 任务状态更改
        workflow = Workflows.objects.set_to_prepare(workflow.id)
        if workflow:
            # 生成workflow的批量任务参数，及任务下发的参数
            params = prepare_workflow(task_handler, workflow)
            logger.info(f"prepare_workflow {params}")
            # 创建celery任务链
            t = task_handler.signature(workflow_id=workflow.id, site_id=workflow.site_id, params=params)
            # delay方法接受任务函数的参数，并将任务放入任务队列中，等待被执行。
            logger.info("run chain")
            result = t.delay()
            logger.info(f"delay result{result}")
