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
from typing import TYPE_CHECKING

from botocore.docs.bcdoc.restdoc import DocumentStructure
from botocore.docs.params import ResponseParamsDocumenter
from botocore.hooks import BaseEventHooks

from boto3.docs.utils import get_identifier_description

# pylint: disable=cyclic-import
if TYPE_CHECKING:
    from boto3.resources.action import Action
    from boto3.resources.model import Identifier, ResourceModel
else:
    Action = object()
    Identifier = object()
    ResourceModel = object()


class ResourceShapeDocumenter(ResponseParamsDocumenter):
    EVENT_NAME = "resource-shape"


def document_attribute(
    section: DocumentStructure,
    service_name: str,
    resource_name: str,
    attr_name: str,
    event_emitter: BaseEventHooks,
    attr_model: ResourceModel,
    include_signature: bool = True,
) -> None:
    if include_signature:
        section.style.start_sphinx_py_attr(attr_name)
    # Note that an attribute may have one, may have many, or may have no
    # operations that back the resource's shape. So we just set the
    # operation_name to the resource name if we ever to hook in and modify
    # a particular attribute.
    ResourceShapeDocumenter(
        service_name=service_name,
        operation_name=resource_name,
        event_emitter=event_emitter,
    ).document_params(section=section, shape=attr_model)


def document_identifier(
    section: DocumentStructure,
    resource_name: str,
    identifier_model: Identifier,
    include_signature: bool = True,
) -> None:
    if include_signature:
        section.style.start_sphinx_py_attr(identifier_model.name)
    description = get_identifier_description(resource_name, identifier_model.name)
    description = "*(string)* " + description
    section.write(description)


def document_reference(
    section: DocumentStructure, reference_model: Action, include_signature: bool = True
) -> None:
    if include_signature:
        section.style.start_sphinx_py_attr(reference_model.name)
    reference_type = "(:py:class:`%s`) " % reference_model.resource.type
    section.write(reference_type)
    section.include_doc_string(
        "The related %s if set, otherwise ``None``." % reference_model.name
    )
