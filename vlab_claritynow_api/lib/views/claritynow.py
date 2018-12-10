# -*- coding: UTF-8 -*-
"""
Defines the RESTful API for the ClarityNow service
"""
import ujson
from flask import current_app
from flask_classy import request, route, Response
from vlab_inf_common.views import TaskView
from vlab_inf_common.vmware import vCenter, vim
from vlab_api_common import describe, get_logger, requires, validate_input


from vlab_claritynow_api.lib import const


logger = get_logger(__name__, loglevel=const.VLAB_CLARITYNOW_LOG_LEVEL)


class ClarityNowView(TaskView):
    """API end point TODO"""
    route_base = '/api/1/inf/claritynow'
    POST_SCHEMA = { "$schema": "http://json-schema.org/draft-04/schema#",
                    "type": "object",
                    "description": "Create a claritynow",
                    "properties": {
                        "name": {
                            "description": "The name to give your ClarityNow instance",
                            "type": "string"
                        },
                        "image": {
                            "description": "The image/version of ClarityNow to create",
                            "type": "string"
                        },
                        "network": {
                            "description": "The network to hook the ClarityNow instance up to",
                            "type": "string"
                        }
                    },
                    "required": ["name", "image", "network"]
                  }
    DELETE_SCHEMA = {"$schema": "http://json-schema.org/draft-04/schema#",
                     "description": "Destroy a ClarityNow",
                     "type": "object",
                     "properties": {
                        "name": {
                            "description": "The name of the ClarityNow instance to destroy",
                            "type": "string"
                        }
                     },
                     "required": ["name"]
                    }
    GET_SCHEMA = {"$schema": "http://json-schema.org/draft-04/schema#",
                  "description": "Display the ClarityNow instances you own"
                 }
    IMAGES_SCHEMA = {"$schema": "http://json-schema.org/draft-04/schema#",
                     "description": "View available versions of ClarityNow that can be created"
                    }


    @requires(verify=const.VLAB_VERIFY_TOKEN, version=2)
    @describe(post=POST_SCHEMA, delete=DELETE_SCHEMA, get=GET_SCHEMA)
    def get(self, *args, **kwargs):
        """Display the ClarityNow instances you own"""
        username = kwargs['token']['username']
        resp_data = {'user' : username}
        task = current_app.celery_app.send_task('claritynow.show', [username])
        resp_data['content'] = {'task-id': task.id}
        resp = Response(ujson.dumps(resp_data))
        resp.status_code = 202
        resp.headers.add('Link', '<{0}{1}/task/{2}>; rel=status'.format(const.VLAB_URL, self.route_base, task.id))
        return resp

    @requires(verify=const.VLAB_VERIFY_TOKEN, version=2)
    @validate_input(schema=POST_SCHEMA)
    def post(self, *args, **kwargs):
        """Create a ClarityNow"""
        username = kwargs['token']['username']
        resp_data = {'user' : username}
        body = kwargs['body']
        machine_name = body['name']
        image = body['image']
        network = body['network']
        task = current_app.celery_app.send_task('claritynow.create', [username, machine_name, image, network])
        resp_data['content'] = {'task-id': task.id}
        resp = Response(ujson.dumps(resp_data))
        resp.status_code = 202
        resp.headers.add('Link', '<{0}{1}/task/{2}>; rel=status'.format(const.VLAB_URL, self.route_base, task.id))
        return resp

    @requires(verify=const.VLAB_VERIFY_TOKEN, version=2)
    @validate_input(schema=DELETE_SCHEMA)
    def delete(self, *args, **kwargs):
        """Destroy a ClarityNow"""
        username = kwargs['token']['username']
        resp_data = {'user' : username}
        machine_name = kwargs['body']['name']
        task = current_app.celery_app.send_task('claritynow.delete', [username, machine_name])
        resp_data['content'] = {'task-id': task.id}
        resp = Response(ujson.dumps(resp_data))
        resp.status_code = 202
        resp.headers.add('Link', '<{0}{1}/task/{2}>; rel=status'.format(const.VLAB_URL, self.route_base, task.id))
        return resp

    @route('/image', methods=["GET"])
    @requires(verify=const.VLAB_VERIFY_TOKEN, version=2)
    @describe(get=IMAGES_SCHEMA)
    def image(self, *args, **kwargs):
        """Show available versions of ClarityNow that can be deployed"""
        username = kwargs['token']['username']
        resp_data = {'user' : username}
        task = current_app.celery_app.send_task('claritynow.image')
        resp_data['content'] = {'task-id': task.id}
        resp = Response(ujson.dumps(resp_data))
        resp.status_code = 202
        resp.headers.add('Link', '<{0}{1}/task/{2}>; rel=status'.format(const.VLAB_URL, self.route_base, task.id))
        return resp
