from service.base_service import BaseService


class InstanceService(BaseService):
    @classmethod
    def get_all_obj_params(cls, instance_id):
        every_obj_param_list = [{
            "obj_id": "id_1",
            "obj_name": "子实例1"
        }, {
            "obj_id": "id_2",
            "obj_name": "子实例2"
        }]
        return every_obj_param_list
