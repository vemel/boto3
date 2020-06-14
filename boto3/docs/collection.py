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
from typing import TYPE_CHECKING, Dict, List

from botocore import xform_name
from botocore.docs.bcdoc.restdoc import DocumentStructure
from botocore.docs.method import get_instance_public_methods
from botocore.docs.utils import DocumentedShape
from botocore.hooks import BaseEventHooks
from botocore.model import ServiceModel

from boto3.docs.base import BaseDocumenter
from boto3.docs.method import document_model_driven_resource_method
from boto3.docs.utils import add_resource_type_overview, get_resource_ignore_params

# pylint: disable=cyclic-import
if TYPE_CHECKING:
    from boto3.resources.action import Action
    from boto3.resources.model import Collection
else:
    Action = object()
    Collection = object()


class CollectionDocumenter(BaseDocumenter):
    def document_collections(self, section: DocumentStructure) -> None:
        collections = self.resource_model.collections
        collections_list: List[str] = []
        add_resource_type_overview(
            section=section,
            resource_type="Collections",
            description=(
                "Collections provide an interface to iterate over and "
                "manipulate groups of resources. "
            ),
            intro_link="guide_collections",
        )
        self.member_map["collections"] = collections_list
        for collection in collections:
            collection_section = section.add_new_section(collection.name)
            collections_list.append(collection.name)
            self._document_collection(collection_section, collection)

    def _document_collection(
        self, section: DocumentStructure, collection: Collection
    ) -> None:
        methods = get_instance_public_methods(getattr(self._resource, collection.name))
        document_collection_object(section, collection)
        batch_actions = {}
        for batch_action in collection.batch_actions:
            batch_actions[batch_action.name] = batch_action

        for method in sorted(methods):
            method_section = section.add_new_section(method)
            if method in batch_actions:
                document_batch_action(
                    section=method_section,
                    resource_name=self._resource_name,
                    event_emitter=self.client.meta.events,
                    batch_action_model=batch_actions[method],
                    collection_model=collection,
                    service_model=self.client.meta.service_model,
                )
            else:
                document_collection_method(
                    section=method_section,
                    resource_name=self._resource_name,
                    action_name=method,
                    event_emitter=self.client.meta.events,
                    collection_model=collection,
                    service_model=self.client.meta.service_model,
                )


def document_collection_object(
    section: DocumentStructure,
    collection_model: Collection,
    include_signature: bool = True,
) -> None:
    """Documents a collection resource object

    :param section: The section to write to

    :param collection_model: The model of the collection

    :param include_signature: Whether or not to include the signature.
        It is useful for generating docstrings.
    """
    if include_signature:
        section.style.start_sphinx_py_attr(collection_model.name)
    section.include_doc_string(
        "A collection of %s resources." % collection_model.resource.type
    )
    section.include_doc_string(
        "A %s Collection will include all resources by default, "
        "and extreme caution should be taken when performing "
        "actions on all resources." % collection_model.resource.type
    )


def document_batch_action(
    section: DocumentStructure,
    resource_name: str,
    event_emitter: BaseEventHooks,
    batch_action_model: Action,
    service_model: ServiceModel,
    collection_model: Collection,
    include_signature: bool = True,
) -> None:
    """Documents a collection's batch action

    :param section: The section to write to

    :param resource_name: The name of the resource

    :param action_name: The name of collection action. Currently only
        can be all, filter, limit, or page_size

    :param event_emitter: The event emitter to use to emit events

    :param batch_action_model: The model of the batch action

    :param collection_model: The model of the collection

    :param service_model: The model of the service

    :param include_signature: Whether or not to include the signature.
        It is useful for generating docstrings.
    """
    operation_model = service_model.operation_model(
        batch_action_model.request.operation
    )
    ignore_params = get_resource_ignore_params(batch_action_model.request.params)

    example_return_value = "response"
    if batch_action_model.has_resource():
        example_return_value = xform_name(batch_action_model.resource.type)

    example_resource_name = xform_name(resource_name)
    if service_model.service_name == resource_name:
        example_resource_name = resource_name
    example_prefix = "%s = %s.%s.%s" % (
        example_return_value,
        example_resource_name,
        collection_model.name,
        batch_action_model.name,
    )
    document_model_driven_resource_method(
        section=section,
        method_name=batch_action_model.name,
        operation_model=operation_model,
        event_emitter=event_emitter,
        method_description=operation_model.documentation,
        example_prefix=example_prefix,
        exclude_input=ignore_params,
        resource_action_model=batch_action_model,
        include_signature=include_signature,
    )


def document_collection_method(
    section: DocumentStructure,
    resource_name: str,
    action_name: str,
    event_emitter: BaseEventHooks,
    collection_model: Collection,
    service_model: ServiceModel,
    include_signature: bool = True,
) -> None:
    """Documents a collection method

    :param section: The section to write to

    :param resource_name: The name of the resource

    :param action_name: The name of collection action. Currently only
        can be all, filter, limit, or page_size

    :param event_emitter: The event emitter to use to emit events

    :param collection_model: The model of the collection

    :param service_model: The model of the service

    :param include_signature: Whether or not to include the signature.
        It is useful for generating docstrings.
    """
    operation_model = service_model.operation_model(collection_model.request.operation)

    underlying_operation_members = []
    if operation_model.input_shape:
        underlying_operation_members = operation_model.input_shape.members

    example_resource_name = xform_name(resource_name)
    if service_model.service_name == resource_name:
        example_resource_name = resource_name

    custom_action_names = ["all", "filter", "limit", "page_size"]
    method_descriptions: Dict[str, str] = {
        "all": (
            "Creates an iterable of all %s resources "
            "in the collection." % collection_model.resource.type
        ),
        "filter": (
            "Creates an iterable of all %s resources "
            "in the collection filtered by kwargs passed to "
            "method." % collection_model.resource.type
            + "A %s collection will include all resources by "
            "default if no filters are provided, and extreme "
            "caution should be taken when performing actions "
            "on all resources." % collection_model.resource.type
        ),
        "limit": (
            "Creates an iterable up to a specified amount of "
            "%s resources in the collection." % collection_model.resource.type
        ),
        "page_size": (
            "Creates an iterable of all %s resources "
            "in the collection, but limits the number of "
            "items returned by each service call by the specified "
            "amount." % collection_model.resource.type
        ),
    }

    example_prefixes: Dict[str, str] = {
        "all": "%s_iterator = %s.%s.all"
        % (
            xform_name(collection_model.resource.type),
            example_resource_name,
            collection_model.name,
        ),
        "filter": "%s_iterator = %s.%s.filter"
        % (
            xform_name(collection_model.resource.type),
            example_resource_name,
            collection_model.name,
        ),
        "limit": "%s_iterator = %s.%s.limit"
        % (
            xform_name(collection_model.resource.type),
            example_resource_name,
            collection_model.name,
        ),
        "page_size": "%s_iterator = %s.%s.page_size"
        % (
            xform_name(collection_model.resource.type),
            example_resource_name,
            collection_model.name,
        ),
    }

    include_inputs: Dict[str, List[DocumentedShape]] = {
        "limit": [
            DocumentedShape(
                name="count",
                type_name="integer",
                documentation=(
                    "The limit to the number of resources " "in the iterable."
                ),
            )
        ],
        "page_size": [
            DocumentedShape(
                name="count",
                type_name="integer",
                documentation=("The number of items returned by each " "service call"),
            )
        ],
    }

    exclude_inputs: Dict[str, List[str]] = {
        "all": underlying_operation_members,
        "filter": get_resource_ignore_params(collection_model.request.params),
        "limit": underlying_operation_members,
        "page_size": underlying_operation_members,
    }
    if action_name in custom_action_names:
        method_description = method_descriptions.get(action_name)
        example_prefix = example_prefixes.get(action_name)
        include_input = include_inputs.get(action_name)
        exclude_input = exclude_inputs.get(action_name)
        document_model_driven_resource_method(
            section=section,
            method_name=action_name,
            operation_model=operation_model,
            event_emitter=event_emitter,
            resource_action_model=collection_model,
            method_description=method_description,
            example_prefix=example_prefix,
            include_input=include_input,
            exclude_input=exclude_input,
            include_signature=include_signature,
        )
