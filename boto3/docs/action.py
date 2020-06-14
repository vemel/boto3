# Copyright 2015 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
import inspect
from typing import Any

from botocore import xform_name
from botocore.model import OperationModel, ServiceModel
from botocore.hooks import BaseEventHooks
from botocore.utils import get_service_module_name
from botocore.docs.method import document_model_driven_method
from botocore.docs.bcdoc.restdoc import DocumentStructure

from boto3.docs.base import BaseDocumenter
from boto3.docs.method import document_model_driven_resource_method
from boto3.docs.utils import get_resource_ignore_params
from boto3.docs.utils import get_resource_public_actions
from boto3.docs.utils import add_resource_type_overview
from boto3.resources.action import Action


class ActionDocumenter(BaseDocumenter):
    def document_actions(self, section: DocumentStructure) -> None:
        modeled_actions_list = self._resource_model.actions
        modeled_actions = {}
        for modeled_action in modeled_actions_list:
            modeled_actions[modeled_action.name] = modeled_action
        resource_actions = get_resource_public_actions(
            self._resource.__class__)
        self.member_map['actions'] = sorted(resource_actions)
        add_resource_type_overview(
            section=section,
            resource_type='Actions',
            description=(
                'Actions call operations on resources.  They may '
                'automatically handle the passing in of arguments set '
                'from identifiers and some attributes.'),
            intro_link='actions_intro')

        for action_name in sorted(resource_actions):
            action_section = section.add_new_section(action_name)
            if action_name in ['load', 'reload'] and self._resource_model.load:
                assert self._resource.meta.client
                document_load_reload_action(
                    section=action_section,
                    action_name=action_name,
                    resource_name=self._resource_name,
                    event_emitter=self._resource.meta.client.meta.events,
                    load_model=self._resource_model.load,
                    service_model=self._service_model
                )
            elif action_name in modeled_actions:
                assert self._resource.meta.client
                document_action(
                    section=action_section,
                    resource_name=self._resource_name,
                    event_emitter=self._resource.meta.client.meta.events,
                    action_model=modeled_actions[action_name],
                    service_model=self._service_model,
                )
            else:
                document_custom_method(
                    action_section, action_name, resource_actions[action_name])


def document_custom_signature(section: DocumentStructure, name: str, method: Any) -> None:
    signature = inspect.signature(method)
    signature_params = ", ".join(signature.parameters)
    section.style.start_sphinx_py_method(name, signature_params)


def document_custom_method(section: DocumentStructure, method_name: str, method: Any) -> None:
    document_custom_signature(
        section, method_name, method)
    method_intro_section = section.add_new_section('method-intro')
    method_intro_section.writeln('')
    doc_string = inspect.getdoc(method)
    if doc_string is not None:
        method_intro_section.style.write_py_doc_string(doc_string)


def document_action(section: DocumentStructure, resource_name: str, event_emitter: BaseEventHooks, action_model: Action,
                    service_model: ServiceModel, include_signature: bool=True) -> None:
    """Documents a resource action

    :param section: The section to write to

    :param resource_name: The name of the resource

    :param event_emitter: The event emitter to use to emit events

    :param action_model: The model of the action

    :param service_model: The model of the service

    :param include_signature: Whether or not to include the signature.
        It is useful for generating docstrings.
    """
    operation_model = service_model.operation_model(
        action_model.request.operation)
    ignore_params = get_resource_ignore_params(action_model.request.params)

    example_return_value = 'response'
    if action_model.has_resource():
        example_return_value = xform_name(action_model.resource.type)
    example_resource_name = xform_name(resource_name)
    if service_model.service_name == resource_name:
        example_resource_name = resource_name
    example_prefix = '%s = %s.%s' % (
        example_return_value, example_resource_name, action_model.name)
    document_model_driven_resource_method(
        section=section, method_name=action_model.name,
        operation_model=operation_model,
        event_emitter=event_emitter,
        method_description=operation_model.documentation,
        example_prefix=example_prefix,
        exclude_input=ignore_params,
        resource_action_model=action_model,
        include_signature=include_signature
    )


def document_load_reload_action(section: DocumentStructure, action_name: str, resource_name: str,
                                event_emitter: BaseEventHooks, load_model: Action, service_model: ServiceModel,
                                include_signature: bool=True) -> None:
    """Documents the resource load action

    :param section: The section to write to

    :param action_name: The name of the loading action should be load or reload

    :param resource_name: The name of the resource

    :param event_emitter: The event emitter to use to emit events

    :param load_model: The model of the load action

    :param service_model: The model of the service

    :param include_signature: Whether or not to include the signature.
        It is useful for generating docstrings.
    """
    description = (
        'Calls  :py:meth:`%s.Client.%s` to update the attributes of the'
        ' %s resource. Note that the load and reload methods are '
        'the same method and can be used interchangeably.' % (
            get_service_module_name(service_model),
            xform_name(load_model.request.operation),
            resource_name)
    )
    example_resource_name = xform_name(resource_name)
    if service_model.service_name == resource_name:
        example_resource_name = resource_name
    example_prefix = '%s.%s' % (example_resource_name, action_name)
    document_model_driven_method(
        section=section, method_name=action_name,
        operation_model=OperationModel({}, service_model),
        event_emitter=event_emitter,
        method_description=description,
        example_prefix=example_prefix,
        include_signature=include_signature
    )
